# MirrorSphere 架构设计

## 1. 总体架构

MirrorSphere 采用分层架构设计，由 8 个核心服务构成：

```text
┌─────────────────────────────────────────────────────────────────┐
│                       用户层 (User Layer)                        │
│   portal_web (React 18 + Ant Design 5 + Rspack)                 │
│   AI Chat (DeerFlow UI)                                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP API
┌──────────────────────────────▼──────────────────────────────────┐
│                    服务层 (Service Layer)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │  portal  │  │  pilot   │  │         harness (AI)          │  │
│  │ (Hertz)  │  │ (Hertz)  │  │  (DeerFlow 2.0 + MCP)        │  │
│  └──────────┘  └──────────┘  └──────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Pull Model (主动轮询)
┌──────────────────────────────▼──────────────────────────────────┐
│                   执行层 (Execution Layer)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ recorder │  │ replayer │  │airtest-agent │  │midscene-  │  │
│  │  (Gin)   │  │  (Gin)   │  │   (Gin)      │  │  agent    │  │
│  └──────────┘  └──────────┘  └──────────────┘  └───────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                  基础设施层 (Infrastructure)                      │
│  MySQL / Elasticsearch / S3 / EFS / Prometheus / Grafana / K8s   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 组件技术栈

| 组件 | 语言 | 框架 | 部署方式 | Go Module |
|------|------|------|----------|-----------|
| portal | Go 1.24 | Cloudwego Hertz | Deployment | `lf.git.oa.mt/mirrorsphere/portal` |
| portal_web | TypeScript | React 18 + Rspack | 静态部署 | - |
| pilot | Go 1.24 | Cloudwego Hertz | Deployment | `lf.git.oa.mt/mirrorsphere/pilot` |
| recorder | Go 1.24 | Gin + GoReplay | Sidecar/DaemonSet | `lf.git.oa.mt/mirrorsphere/recorder` |
| replayer | Go 1.24 | Gin + GoReplay | Deployment | `lf.git.oa.mt/mirrorsphere/replayer` |
| airtest-agent | Go 1.24 | Gin + Python | 物理机进程 | `lf.git.oa.mt/mirrorsphere/airtest-agent` |
| midscene-agent | Go 1.25 | Gin + Midscene | 进程 | `lf.git.oa.mt/mirrorsphere/midscene-agent` |
| harness | Python | DeerFlow 2.0 | Deployment | - |

## 3. 通信架构

### 3.1 通信模式

所有执行层组件使用**主动轮询模型（Pull Model）**：

```text
recorder/replayer/airtest-agent/midscene-agent
    │
    │ 定时 HTTP 请求 (心跳 + 获取任务)
    ▼
  pilot
    │
    │ HMAC-SHA1 签名验证
    ▼
  返回任务指令 / 空响应
```

**设计原因**：
- Agent 运行在受限网络环境（如目标服务 Pod 内），Push 不可达
- Pull 模型天然适配 Agent 弹性伸缩，无需管理连接
- 心跳即轮询，一举两得

### 3.2 签名验证

所有组件与 Pilot 的通信经 HMAC-SHA1 签名验证：
- 签名算法定义在 `pilot/biz/consts/sign.go`
- Agent/Worker 启动时配置签名密钥
- 每个请求在 Header 中携带时间戳和签名

### 3.3 文件传输

Agent 文件上传使用 S3 预签名 URL：
- Pilot 通过 `/s3/` 接口生成临时上传 URL
- Agent 直接上传到 S3，无需经过 Pilot 中转
- 预签名 URL 有时效性，保障数据安全

### 3.4 前端通信

portal_web → portal：标准 RESTful HTTP API
- 所有接口基于 Protocol Buffers 定义
- 响应格式统一：`{code, message, data, time}`
- 支持 MOA (OAuth) 认证

## 4. 数据流架构

### 4.1 流量录制数据流

```text
┌─────────────┐
│ 目标业务服务  │
└──────┬──────┘
       │ libpcap 内核级流量捕获 (零拷贝)
       ▼
┌─────────────┐    ①录制文件(.gor)     ┌─────────┐
│  recorder   │ ────────────────────▶  │   S3    │
│  (Agent)    │                        └─────────┘
└──────┬──────┘
       │ ②心跳 + 状态上报
       ▼
┌─────────────┐    ③任务状态写入       ┌─────────┐
│    pilot    │ ────────────────────▶  │  MySQL  │
└─────────────┘
```

**录制模式2（录制且回放）**时增加：
```text
recorder → 实时发送请求到 output_dst → 响应写入 Elasticsearch
```

### 4.2 流量回放数据流

```text
┌─────────────┐    ①下载.gor文件      ┌─────────┐
│  replayer   │ ◀──────────────────── │   S3    │
│  (Worker)   │                       └─────────┘
└──────┬──────┘
       │ ②发送回放请求 (+ MS-Traffic + MS-Traffic-Key)
       ▼
┌─────────────────────┐
│   目标服务 A (原始)   │
│   目标服务 B (新版本) │ ← 多目标支持 A/B 对比
└──────────┬──────────┘
           │ ③响应结果
           ▼
┌──────────────────┐    ④Diff 对比     ┌─────────┐
│  Elasticsearch   │ ◀───────────────  │ portal  │
│ (payload_id关联) │                   │ (diffy) │
└──────────────────┘                   └─────────┘
```

### 4.3 API 自动化数据流

```text
┌─────────────┐
│  portal_web │  用户配置接口 + 断言
└──────┬──────┘
       │ POST /api/main/am-test 或 /api/case/ac-test
       ▼
┌─────────────┐    发送HTTP请求      ┌─────────────┐
│   portal    │ ─────────────────▶   │  目标服务    │
│  (执行器)   │ ◀─────────────────   │             │
└──────┬──────┘    收到HTTP响应      └─────────────┘
       │
       │ 执行断言 + 后置操作 + 参数提取
       │ 结果写入 api_log 表
       ▼
┌─────────────┐
│   MySQL     │  执行历史 + 统计报表
└─────────────┘
```

### 4.4 UI 自动化数据流

```text
┌──────────────┐    ①轮询获取任务     ┌─────────────┐
│airtest-agent │ ◀────────────────── │    pilot    │
└──────┬───────┘                     └─────────────┘
       │ ②下载代码包
       ▼
┌─────────────┐
│     S3      │
└─────────────┘
       │ ③解压 + 执行 Airtest/Midscene
       ▼
┌──────────────┐    ④上传报告+截图    ┌─────────────┐
│ Android/Web  │                     │     S3      │
│   设备       │                     └──────┬──────┘
└──────────────┘                            │
                                            │ ⑤回调结果
                                            ▼
                                     ┌─────────────┐
                                     │    pilot    │
                                     └─────────────┘
```

## 5. 数据存储设计

### 5.1 MySQL 数据模型

基于 Pilot 的 DAL 层（`pilot/biz/dal/dmysql/`），核心数据表：

| 表 | 职责 | 关键字段 |
|----|------|----------|
| agent | 录制器注册表 | id, biz, name, ip, hostname, pid, status, active_at |
| worker | 回放器注册表 | id, biz, ip, hostname, pid, status, active_at |
| record | 录制计划 | id, name, key, biz, status, approve_status, mode, schedule |
| record_exec | 录制子任务 | id, record_id, agent_id, status |
| replay | 回放计划 | id, name, key, record_id, biz, status, mode, schedule |
| replay_exec | 回放子任务 | id, replay_id, worker_id, status |
| biz | 业务线 | id, name, zh_name, status, approver, feishu_hook_url |

Portal 额外的数据表：

| 表 | 职责 |
|----|------|
| test_case_pool | 通用测试用例库 |
| test_plan_case | 计划用例（绑定版本） |
| api_main | API 接口定义 |
| api_case | API 测试用例 |
| api_scene | 场景测试用例 |
| api_module | API 模块树 |
| api_log | 执行历史 |
| mock | Mock 计划 |
| ui_airtest | UI 自动化用例 |
| ui_airtest_exec | UI 自动化执行记录 |
| ui_airtest_agent | UI Agent 注册表 |

### 5.2 Elasticsearch

用途：存储流量回放的请求/响应日志，支持 Diff 对比分析。

索引字段：
- `request_id` — 请求唯一标识
- `ms_traffic_key` — 关联录制/回放计划
- `x_trace_id` — 微服务链路追踪 ID
- `host` — 请求目标主机
- `path` — 请求路径
- `method` — HTTP 方法
- `request` — 请求内容
- `response` — 响应内容
- `timestamp` — 时间戳

**录制文件索引**：`pilot/biz/dal/dmysql/record_file_es.go` 管理录制文件的 ES 索引。

### 5.3 S3 对象存储

存储内容：
- 录制流量文件（.gor 格式）
- UI 自动化代码包（zip/tar.gz/rar）
- UI 自动化测试报告（HTML + 截图）
- 执行日志和产物

访问方式：预签名 URL（临时有效期），由 Pilot S3 服务生成。

### 5.4 Amazon EFS

跨 Pod 文件共享，解决 Mock 流量文件需要经过 S3 桥接的开销问题。Replayer Pod 可以直接读取共享文件系统上的自定义流量文件。

## 6. Recorder 内核架构

### 6.1 GoReplay 工作原理

```text
┌─────────────────────────────────────┐
│         Linux Kernel                 │
│  ┌─────────────────────────────┐    │
│  │   Network Interface (eth0)  │    │
│  └─────────────┬───────────────┘    │
│                │ libpcap (BPF)       │
└────────────────┼────────────────────┘
                 │ 原始网络包
                 ▼
┌─────────────────────────────────────┐
│         GoReplay Process             │
│  ┌──────────┐  ┌──────────────┐    │
│  │ Listener │→ │ TCP Assembly │    │  ← 内核级捕获 + TCP 重组
│  └──────────┘  └──────┬───────┘    │
│                        ▼            │
│  ┌─────────────────────────────┐    │
│  │    HTTP Parser + Filter     │    │  ← URL/Method/Header 过滤
│  └──────────────┬──────────────┘    │
│                 ▼                   │
│  ┌──────────────────────────────┐   │
│  │   Output Plugins (async)     │   │
│  │  ├── file  (.gor 文件)       │   │
│  │  ├── http  (实时回放)        │   │
│  │  ├── tcp   (TCP 转发)        │   │
│  │  └── kafka (消息队列)        │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 6.2 MirrorSphere 对 GoReplay 的内核增强

| 增强项 | 实现细节 | 解决问题 |
|--------|----------|----------|
| ES 8.x 兼容 | 修复 Elastigo 库 API | 支持新版 Elasticsearch |
| payload_id 传递 | output_http 插件写入 ES | 关联多目标回放响应 |
| 响应来源标识 | 新增 host 标识字段 | 多目标对比时区分来源 |
| X-Trace-ID 集成 | 识别并写入 ES | 打通微服务链路追踪 |
| MS-Traffic-Key | 新增自定义 Header | 帮助目标服务辨识流量来源 |
| kill 文件刷新 | 修复信号处理 | 保证录制数据完整性 |
| 队列统计 | message 队列 metrics | 排查性能瓶颈 |
| 动态参数替换 | 规则引擎替换参数值 | 压测幂等性场景 |
| 并发控制 | 中间件设置并发数 | 模拟高并发 |
| Content-Length 同步 | 加密/压缩后自动更新 | MSDK 签名校验 |
| 压缩自动解码 | gzip/deflate/br 识别 | 压缩响应内容友好展示 |
| Header 重命名 | http_rename_header 支持 | 不同业务方 trace id 统一 |

### 6.3 性能设计

- **内核级流量捕获**：基于 libpcap BPF，内核层完成数据过滤
- **零拷贝技术**：减少用户态/内核态间的数据拷贝
- **异步处理架构**：录制、存储全流程异步化，不阻塞业务
- **内存池设计**：Goroutine 池限制并发，对象复用减少 GC
- **采样策略**：按比例或数量控制录制流量

## 7. Pilot 调度架构

### 7.1 模块划分

```text
pilot/biz/
├── handler/        ← API 处理器
│   ├── agent/      ← Agent 注册/心跳
│   ├── worker/     ← Worker 注册/心跳
│   ├── record/     ← 录制任务管理
│   ├── replay/     ← 回放任务管理
│   ├── s3/         ← 预签名 URL 生成
│   └── hybrid/     ← 混合操作（可用资源查询）
├── router/         ← 路由注册 + 中间件
│   ├── agent/      ← Agent 路由 + 签名中间件
│   ├── worker/     ← Worker 路由 + 签名中间件
│   ├── record/     ← 录制路由
│   ├── replay/     ← 回放路由
│   └── s3/         ← S3 路由
├── dal/            ← 数据访问层
│   ├── dmysql/     ← MySQL 操作
│   ├── des/        ← Elasticsearch 操作
│   ├── ds3/        ← S3 操作
│   └── dcache/     ← 缓存操作
├── consts/         ← 常量定义（状态码、模式等）
├── middleware/     ← 通用中间件（metrics、recovery、context）
└── component/      ← 基础组件（logger、metrics）
```

### 7.2 Agent 生命周期管理

```text
Agent 启动
    │
    ▼
┌──────────┐     POST /agent/register
│ 注册     │ ──────────────────────────▶ Pilot
└────┬─────┘     (biz, name, ip, hostname, pid)
     │
     ▼
┌──────────┐     定时 GET /agent/heartbeat
│ 活跃     │ ◀─────────────────────────▶ Pilot
│ (status=1)│     返回任务指令
└────┬─────┘
     │ 超时无心跳 / 主动反注册
     ▼
┌──────────┐     POST /agent/unregister
│ 已反注册  │ ──────────────────────────▶ Pilot
│ (status=2)│
└──────────┘
```

Agent 状态：已注册(1)、已反注册(2)

### 7.3 录制任务调度

```text
用户创建录制计划 (portal → pilot)
    │
    ▼
┌──────────────────┐
│ 解析录制规则      │  ← 根据配置生成 GoReplay 命令行参数
│ (ParserRule)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 选择可用 Agent   │  ← 已注册 + 当前无进行中任务
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 创建 RecordExec  │  ← 每个 Agent 一个子任务
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Agent 心跳获取   │  ← Agent 定时轮询获取到任务
│ 执行录制命令     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 状态流转         │  ← 未开启 → 已开启 → 录制中 → 停止中 → 已停止
└──────────────────┘
```

### 7.4 Worker 资源调度

- 单个回放计划最多选择 5 个 Worker（`MaxWorkerNum = 5`）
- Worker 注册时默认支持所有业务线（`DefaultWorkerBiz = "all"`）
- 可通过 portal 编辑 Worker 指定支持的业务线
- Worker 状态：已注册(1)、已反注册(2)

## 8. Portal 业务架构

### 8.1 项目分层

```text
portal/
├── biz/
│   ├── handler/    ← 请求处理（参数校验 + 调用 service）
│   ├── service/    ← 业务逻辑
│   ├── dal/        ← 数据访问
│   └── middleware/ ← 中间件（CORS、日志、指标、recovery）
├── idl/            ← Protocol Buffers 接口定义
├── conf/           ← 配置管理
└── router*.go      ← 路由注册
```

### 8.2 接口协议设计

所有接口使用 Protocol Buffers 定义，遵循统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "time": 1716192000
}
```

列表接口统一分页格式：
```json
{
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 8.3 审批流程设计

```text
创建任务 → approve_status = 待审批
    │
    ▼ (飞书 Webhook 通知审批人)
审批人操作
    ├── 通过 → approve_status = 已通过 → 可开启执行
    └── 拒绝 → approve_status = 已拒绝 (附拒绝原因)
```

审批通过的操作（`/record/rcd-approve`, `/replay/rpy-approve`, `/mock/mk-approve`）通过 HybridService 统一处理。

### 8.4 API 自动化引擎设计

```text
┌─────────────────────────────────────────────┐
│              API 请求构造引擎                 │
├─────────────────────────────────────────────┤
│  Input:                                      │
│    host + method + path + headers + query    │
│    + body (json/form)                        │
│    + algorithm (加密签名策略)                  │
├─────────────────────────────────────────────┤
│  Pre-Actions:                                │
│    ├── wait_controller (等待 N 毫秒)          │
│    └── script (自定义脚本)                    │
├─────────────────────────────────────────────┤
│  执行 HTTP 请求                               │
├─────────────────────────────────────────────┤
│  Post-Actions:                               │
│    ├── extract_param (参数提取)               │
│    │     ├── regular (正则提取)               │
│    │     └── jsonpath (JSONPath 提取)         │
│    └── script (自定义脚本)                    │
├─────────────────────────────────────────────┤
│  Assertions:                                 │
│    ├── text (文本包含/不包含/等于)             │
│    ├── regular (正则匹配)                     │
│    ├── jsonpath (路径值运算)                   │
│    ├── response_duration (响应时间)            │
│    └── document_structure (JSON Schema)       │
├─────────────────────────────────────────────┤
│  Output:                                     │
│    request + response + duration + assert_result │
└─────────────────────────────────────────────┘
```

场景测试编排支持的步骤类型：
- `api` — 引用已有 API 接口
- `case` — 引用已有测试用例
- `custom_request` — 自定义请求
- `wait_controller` — 等待控制器
- `condition_controller` — 条件控制器（变量判断：eq/neq/in/notin/gt/lt/empty）

## 9. Harness（AI 能力层）架构

### 9.1 定位

```
harness = DeerFlow Runtime Overlay + MirrorSphere Knowledge/Skill/MCP Layer
```

### 9.2 能力分层

```text
┌────────────────────────────────────────┐
│         Persona Layer (Agent)          │
│   mirrorsphere agent + SOUL           │
├────────────────────────────────────────┤
│          Skill Layer                   │
│   knowledge / prd-analysis /           │
│   test-design / mindmap-generation     │
├────────────────────────────────────────┤
│        Knowledge Layer                 │
│   L1: 静态文档 (references/docs/)      │
│   L2: 代码索引 (knowledge-pack.md)     │
│   L3: 动态数据 (future MCP)           │
├────────────────────────────────────────┤
│           MCP Layer                    │
│   filesystem / mirrorsphere-portal     │
├────────────────────────────────────────┤
│         DeerFlow Runtime               │
│   config.yaml / extensions / agents    │
└────────────────────────────────────────┘
```

### 9.3 运行时注入策略

Harness 不修改 DeerFlow 源码，通过以下方式注入定制：
- `config.yaml` — 模型配置、搜索配置
- `extensions_config.json` — MCP server 定义
- `frontend.env` — 前端默认 assistant
- `agents/mirrorsphere/` — 自定义 Agent 人设 + SOUL
- `skills/custom/` — 自定义 Skills（含 knowledge）

### 9.4 MCP 集成

`mirrorsphere-portal` MCP 服务端提供的工具：
- `tpc-batch-add` — 批量插入测试计划用例
- `tpc-list` — 查询测试计划用例列表
- `module-tree` — 获取模块树结构

## 10. 安全设计

### 10.1 通信安全

| 层面 | 机制 |
|------|------|
| Agent/Worker ↔ Pilot | HMAC-SHA1 签名验证 |
| 文件传输 | S3 预签名 URL（时效性） |
| 前端认证 | MOA OAuth |
| API 权限 | RBAC 角色访问控制 |

### 10.2 权限管理

- **业务线隔离**：用户只能操作有权限的业务线
- **审批机制**：关键操作（录制/回放/Mock）需审批人确认
- **操作审计**：所有操作记录可追溯

### 10.3 数据安全

- 私有部署，数据不离开企业内部
- 录制流量文件存储在企业内部 S3
- 临时预签名 URL 有效期控制
- Agent 上传仅通过临时 URL，无持久凭证暴露

### 10.4 流量安全

- 回放流量通过 `MS-Traffic: true` Header 标记
- 目标服务可根据 Header 识别并隔离回放流量
- 支持 `http_disallow_url` 过滤敏感路径
- 支持 `http_disallow_header` 过滤敏感请求

## 11. 可扩展性设计

### 11.1 水平扩展

- Portal/Pilot：无状态服务，直接增加副本数
- Replayer Worker：根据负载弹性扩缩容
- Recorder Agent：每个目标服务 Pod 一个 Sidecar

### 11.2 存储扩展

- MySQL：读写分离（如需）
- Elasticsearch：按时间切分索引
- S3：无限容量对象存储

### 11.3 接口协议扩展

- Protocol Buffers 定义所有接口，支持向后兼容演进
- 支持自定义算法策略（AlgoD），适配不同业务线加密签名

## 12. 可观测性

### 12.1 指标收集

- 各服务内置 Prometheus metrics 中间件（`pilot/biz/middleware/metrics.go`）
- 暴露 `/metrics` 端点
- 关键指标：请求 QPS、延迟分布、错误率

### 12.2 日志

- 接入 Hela 日志平台
- 结构化日志（`pilot/biz/component/logger/`）
- 请求级别日志追踪

### 12.3 告警

- 基于 Prometheus 告警规则
- Grafana 面板可视化
- 多渠道告警触达（飞书等）

### 12.4 健康检查

- 所有服务提供 `/ping` 健康检查接口
- Kubernetes liveness/readiness probe 集成
- Pilot 定期检查 Agent/Worker 活跃状态

## 13. 部署架构

### 13.1 Kubernetes 部署模式

```text
Namespace: mirrorsphere
├── Deployment: portal (replicas: 2+)
├── Deployment: pilot (replicas: 2+)
├── Deployment: replayer (replicas: N, 按需扩缩)
├── Deployment: harness (replicas: 1+)
├── Deployment: portal-web (Nginx 静态)
├── DaemonSet/Sidecar: recorder (目标服务 Pod)
└── 外部: airtest-agent (Windows 物理机)
         midscene-agent (测试机器)
```

### 13.2 Recorder Sidecar 部署

```yaml
containers:
- command: ["./bootstrap.sh", "--biz=adbi", "--name=流量录制实验"]
  image: sg-harbor.moonton.net/public/msdk/mirrorsphere-recorder:v1.0
  resources:
    limits: { cpu: 500m, memory: 1Gi }
    requests: { cpu: 200m, memory: 500Mi }
  securityContext:
    capabilities:
      add: [NET_ADMIN, NET_RAW]
    runAsUser: 0
```

必须以 root 用户运行，需要 `NET_ADMIN` + `NET_RAW` 能力进行网络流量捕获。
