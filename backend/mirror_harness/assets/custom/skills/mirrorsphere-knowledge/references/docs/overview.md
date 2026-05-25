# MirrorSphere 平台概述

## MirrorSphere 是什么

MirrorSphere（镜域）是基于 Go + React + 开源 GoReplay 技术栈打造的企业级 HTTP 流量录制回放平台，扩展了分布式调度、智能比对、接口测试、UI 自动化、可视化管理等企业级能力，支持多环境流量无损复制与精准回放，帮助测试团队显著提升测试效率、降低测试成本，通过真实流量场景保障系统稳定性。

MirrorSphere 不是单一的录制器或回放器，而是一套由前端、后端服务、执行节点和自动化能力共同组成的测试基础设施平台。

## 项目命名

- **"镜"**：喻指流量的无损录制与真实回放，确保请求与响应的完整性和准确性
- **"域"**：代表完整的执行环境
- **目标**：成为 HTTP 流量录制回放的团队内标准范式，推动质量保障体系的升级

## 平台核心能力

| 能力域 | 说明 | 对应组件 |
|--------|------|----------|
| 流量录制 | 基于 GoReplay 深度定制，内核级抓包 | recorder |
| 流量回放 | 多目标、限流、循环、并发、定时/周期调度 | replayer |
| Diff 对比分析 | 自研 Diff Engine，多目标响应差异对比 | portal (diffy) |
| Mock 请求 | 自定义 HTTP 请求构造和批量发送 | portal (mock) |
| API 接口自动化 | 单接口测试 + 场景编排 + 断言 + 定时执行 | portal (api) |
| 测试用例池 | 通用用例库，支持 CRUD/导入/模块树 | portal (test_case_pool) |
| 测试计划用例 | 与版本计划绑定的用例管理，多环境通过状态 | portal (test_plan_case) |
| UI 自动化（移动端） | 基于 Airtest 的 Android UI 自动化 | airtest-agent |
| UI 自动化（Web 端） | 基于 Midscene 的浏览器自动化 | midscene-agent |
| AI 能力 | 知识问答、PRD 分析、用例生成、脑图 | harness |

## 项目背景与痛点

2025 年 9 月，组建以兴趣为主的虚拟开发小组，力争建设能够解决传统测试痛点的平台。

**痛点一：回归测试接口遗漏，测试覆盖率不足**

传统测试人员手动编写的测试用例，存在场景覆盖不全面、真实场景缺失、效率低下的问题。手动维护成本高，每次业务变更都需要重新审视大量测试用例。

**痛点二：压测投入的人力成本高，资源管理复杂**

传统压测方式需投入大量人力和资源：资源准备阶段需要数小时甚至数天申请和配置机器，压测中需持续监控，压测后需及时回收资源。

**痛点三：测试环境与生产环境的流量差异导致测试结果不准确**

测试环境的数据量、流量特征、环境配置均与生产环境存在差异，无法模拟真实用户行为和请求分布。

**痛点四：个性化接口协议适配难**

MSDK 业务线的接口数据具有特殊的安全协议（JSON/Protobuf 数据格式、加密压缩、签名），对于 QA 来说学习成本高、维护成本高，有效自动化用例占比低。

**痛点五：线上问题难以复现，故障定位效率低**

线上问题往往发生在特定的场景和条件下，测试环境难以完全模拟。缺少完整流量数据，故障定位依赖经验和猜测。

**痛点六：API 变更风险难以控制**

接口变更未被充分测试，兼容性问题导致客户端请求失败，风险识别困难。

## 平台目标

在**数据安全、易用性、定制化能力、性能表现、成本、可维护性、架构弹性、内部闭环**8 个维度上实现平衡，实现测试效率和质量的提升。

---

## 核心组件详解

MirrorSphere 由以下 8 个核心项目构成：

### portal（管理后台服务端）

管理后台的 Go 服务端程序，基于 Cloudwego Hertz 高性能框架，提供全量业务 API。

**技术栈**：Go 1.24 / Cloudwego Hertz / MySQL / S3 / Elasticsearch / Protocol Buffers

**API 域覆盖**：

| 域 | API 前缀 | 核心操作 |
|----|----------|----------|
| 录制管理 | `/record/` | rcd-add, rcd-list, rcd-get, rcd-edit, rcd-open, rcd-stop, rcd-delete |
| 回放管理 | `/replay/` | rpy-add, rpy-list, rpy-get, rpy-edit, rpy-open, rpy-stop, rpy-close-period |
| Mock | `/mock/` | mk-add, mk-list, mk-get, mk-edit, mk-test, mk-gen-curl, mk-open, mk-stop |
| API 测试 | `/api/main/` | am-list, am-add, am-batch-add, am-add-manual, am-import, am-edit, am-test |
| API 用例 | `/api/case/` | ac-list, ac-add, ac-edit, ac-test, ac-delete |
| API 场景 | `/api/scene/` | as-list, as-add, as-edit, as-test, as-delete |
| 测试用例池 | `/test/case-pool/` | tcp-add, tcp-batch-add, tcp-list, tcp-get, tcp-edit, tcp-import, tcp-move |
| 测试计划用例 | `/test/plan-case/` | tpc-add, tpc-batch-add, tpc-list, tpc-get, tpc-edit, tpc-edit-env, tpc-import, tpc-tree |
| Agent 管理 | `/agent/` | list, offline, re-enable, available |
| Worker 管理 | `/worker/` | w-list, w-edit, w-offline, w-re-enable, w-available |
| 业务线 | `/biz/` | b-add, b-list, b-get, b-edit, b-delete, b-accessible |
| 环境管理 | `/biz/env/` | be-list, be-add, be-edit, be-delete, be-option |
| 用户认证 | `/auth/` | 登录、权限验证 |
| Diff 对比 | `/diffy/` | default, host |
| UI 自动化 | `/ui-airtest/` | uat-add, uat-list, uat-open, uat-upload-code |
| 审批 | `/record/rcd-approve`, `/replay/rpy-approve`, `/mock/mk-approve` | 审批通过/拒绝 |

**业务线（Biz）管理**：
- 每个业务线有独立的审批人配置
- 支持飞书 Webhook 通知（Hook URL + 签名密钥）
- 基于业务线的权限隔离

### portal_web（管理后台前端）

**技术栈**：TypeScript / React 18 / Ant Design 5 / Rspack / Zustand / Monaco Editor / React Router 7

**多环境支持**：
- `pnpm dev` — 本地开发 (localhost:3000)
- `pnpm build:test` — 测试环境
- `pnpm build:pre` — 预发环境
- `pnpm build:prod` — 生产环境

**页面模块**：流量录制、流量回放、Mock 测试、API 自动化、测试用例管理、UI 测试、Agent/Worker 管理、系统设置、数据报表

### pilot（控制中心）

系统的"大脑"，负责控制录制器和回放器的启停、任务调度和资源管理。

**技术栈**：Go 1.24 / Cloudwego Hertz / MySQL / S3 / Elasticsearch / Prometheus

**核心职责**：
- Agent 注册/反注册/心跳/状态管理
- Worker 注册/反注册/任务分发
- 录制任务调度（解析规则 → 下发命令 → 监控执行）
- 回放任务调度（文件定位 → 选择 Worker → 下发 → 监控）
- UI 自动化任务分发
- S3 预签名 URL 生成
- Elasticsearch 索引管理

### recorder（流量录制器）

以 Agent 进程形式运行于目标服务周边，负责捕获 HTTP 流量。

**技术栈**：Go 1.24 / Gin / GoReplay（深度定制）/ libpcap

**启动参数**：
- `--biz` — 业务线标识
- `--name` — Agent 名称

**部署方式**：Kubernetes Sidecar（推荐）或 DaemonSet，需要 `NET_ADMIN` + `NET_RAW` 权限

**录制模式**：
- 仅录制（mode=1）：只录制流量保存
- 录制且回放（mode=2）：录制的同时直接回放到目标地址

**采集策略配置**：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| http_allow_header | Header 白名单 | `X-Biz:adbi` |
| http_disallow_header | Header 黑名单 | `X-Internal:true` |
| http_allow_method | Method 白名单 | `GET,POST` |
| http_allow_url | URL 白名单 | `/api/v1/*` |
| http_disallow_url | URL 黑名单 | `/health,/metrics` |
| duration | 最大录制时长(秒) | `3600` |
| limit_mode | 限流模式(1=绝对值,2=百分比) | `1` |
| limit_value | 限流值 | `100` |

**性能影响**：
- CPU 使用率通常低于 5%
- 内存占用低于 100MB
- 流量录制处理延迟小于 1ms

### replayer（流量回放器）

以常驻 Worker 进程方式部署，负责执行流量回放任务。

**技术栈**：Go 1.24 / Gin / GoReplay

**执行模式**：
- 即时执行（mode=1）：立即开始回放
- 定时执行（mode=2）：指定时间点开始
- 定期执行（mode=3）：cron 表达式周期执行

**回放策略**：

| 策略 | 配置 | 说明 |
|------|------|------|
| 限流（绝对值） | `limit_mode=1, limit_value=10` | 每秒不超过 10 个请求 |
| 限流（百分比） | `limit_mode=2, limit_value=200` | 2 倍速回放 |
| 循环回放 | `loop_file=true` | 无限循环回放文件 |
| 并发控制 | `concurrent=5` | 单请求并发 5 次 |
| 多目标 | `output_dst=["http://a","http://b"]` | A/B 对比 |
| 流量染色 | 自动注入 `MS-Traffic: true` | 区分回放流量 |

**流量染色 Header**：
- `MS-Traffic: true` — 标识为回放流量
- `MS-Traffic-Key: <plan_key>` — 关联录制/回放计划

**输入源类型**：raw（实时抓包）、file（文件）、tcp、kafka、自定义

### airtest-agent（Airtest UI 自动化执行节点）

基于 Airtest 框架的移动端 UI 自动化测试代理。

**技术栈**：Go 1.24 / Gin / Python / Airtest / ADB

**执行流程**：
1. 注册到 Pilot（发送 IP、hostname、PID、OS、架构）
2. 定时轮询 Pilot 获取任务
3. 下载测试代码包（zip/tar.gz/rar）
4. 解压并扫描 `.air` 测试目录
5. 使用 Python 虚拟环境执行 Airtest
6. 生成 HTML 报告（含截图）
7. 上传产物到 S3
8. 回调 Pilot 汇报执行结果

**执行模式**：立即执行、定时执行、周期执行（cron）

### midscene-agent（Midscene Web UI 自动化执行节点）

基于 Midscene 框架的 Web 端 UI 自动化测试代理。

**技术栈**：Go 1.25 / Gin / Midscene

**特点**：
- 针对 Web 浏览器自动化
- 支持凭证加密（`-encrypt` CLI 参数）
- 包含数据库层（`sql/` 目录）

### harness（AI 能力扩展层）

MirrorSphere 的 AI 工程目录，基于 ByteDance DeerFlow 2.0 构建。

**技术栈**：Python / DeerFlow 2.0 / LangChain / MCP

**已上线能力**：
- 平台知识问答（91.3% 准确率）

**已就绪 Skills**：
- `mirrorsphere-prd-analysis` — PRD 分析 + 技术评审文档生成
- `mirrorsphere-test-design` — 测试用例自动生成 + MCP 入库
- `mirrorsphere-mindmap-generation` — Mermaid 脑图生成

---

## 功能详解

### 流量录制功能

**录制方式**：
1. **Agent 模式（主要）**：libpcap 内核级流量捕获，非侵入式
2. **Chrome 插件模式**：mirrorsphere-chrome-plugin 浏览器抓包
3. **离线模式**：文件监听，自动上传新增文件

**录制任务状态机**：
```
未开启(1) → 进行中(3) → 已结束(4)
    ↓
  已废弃(2)
```

**录制子任务状态机**：
```
未开启(1) → 已开启录制(3) → 录制中(4) → 停止录制中(5) → 已停止录制(6)
    ↓
  已废弃(2)
```

### 流量回放功能

**回放任务状态机**：
```
未开启(1) → 进行中(3) → 已结束(4)
    ↓
  已废弃(2)
```

**高级回放特性**（GoReplay 内核增强）：
- payload_id 关联：关联同一次回放的不同目标地址响应
- 响应来源标识：标识回放响应来自哪个目标
- 链路追踪：识别 X-Trace-ID 写入 ES，打通微服务链路
- MS-Traffic-Key：关联流量与任务
- 动态参数替换：参数值按指定规则动态替换
- Header 重命名：解决不同业务方 trace id 名称不一致问题

### Diff 对比分析

基于 Elasticsearch 存储的回放日志，提供两种对比模式：

1. **Default 模式**（`/diffy/default`）：按 request_id 对比原始响应与回放响应
2. **Host 模式**（`/diffy/host`）：多目标回放时，对比不同 host 的响应差异

支持按 path、method、host、时间范围、x-trace-id 等维度筛选。

### Mock 请求功能

**HTTP 请求构造引擎**：
- 可视化配置界面，通过表单定义请求信息
- 支持算法策略（QueryString/Body 的加密签名策略）
- 前置操作：等待控制器、自定义脚本
- 后置操作：参数提取（正则/JSONPath）、自定义脚本
- 断言规则：文本断言、正则断言、JSONPath 断言、响应时间断言、文档结构断言
- 一键生成标准 curl 命令（`/mock/mk-gen-curl`）

### API 自动化测试

**三层结构**：
1. **API 模块树**：按业务组织的目录树结构
2. **API 接口**：单个接口定义（method + path + 配置）
3. **API 用例**：绑定到接口的测试用例（含断言和参数化）

**接口来源**：
- 从录制流量自动生成（`am-add`、`am-batch-add`）
- 手动创建（`am-add-manual`）
- Chrome 插件 JSON 导入（`am-import`）
- Curl 命令导入

**场景测试**：
- 编排多个 API/Case 组成场景
- 支持等待控制器（延时）
- 支持条件控制器（变量判断）
- 支持前后置脚本
- 支持参数传递（上一步的响应作为下一步的输入）

**断言引擎**：
| 类型 | 说明 |
|------|------|
| 文本断言 | response_code/header/body 包含/不包含/等于 |
| 正则断言 | Perl 兼容正则匹配 |
| JSONPath | 路径值的 eq/neq/gt/lt/in/notin/regex |
| 响应时间 | 响应时间在 N 毫秒以内 |
| 文档结构 | JSON Schema 结构验证 |

### 测试用例池（Test Case Pool）

通用测试用例库，不绑定版本计划。

**用例字段**：name、module_id、level（优先级）、precondition（前置条件）、steps（操作步骤）、expected_result（预期结果）、label（标签）、remark（备注）

**操作**：增/删/改/查/批量新增/导入(Excel/CSV)/模块移动/批量删除

### 测试计划用例（Test Plan Case）

绑定到版本计划的用例管理，支持多环境测试状态。

**用例字段**：继承 Pool 的所有字段 + actual_result（实际结果）+ test_env/pre_env/prod_env（各环境通过状态）+ source（来源）

**多环境通过状态**：0-待测试、1-测试通过、2-测试不通过

**统计汇总**（TestPlanCaseSummary）：
- 每个模块的 total_count
- test/pre/prod 各环境的 pending/pass/fail/na 计数
- 各环境通过率

**操作**：增/删/改/查/批量新增/导入/模块树/环境状态批量修改/批量移动/批量删除

### UI 自动化测试

**支持引擎**：
- Airtest（Android 移动端）
- Midscene（Web 浏览器端）

**用例管理**：
- 上传代码包（zip/tar.gz/rar）
- 指定默认执行 Agent
- 执行模式：立即/定时/周期
- 优先级分级（level）
- 执行历史和产物查看

**产物**：HTML 测试报告（含截图）、执行日志、manifest.json

---

## 审批流程

录制、回放、Mock 操作均支持审批机制：

1. 用户创建任务 → 状态为"未开启"
2. 用户提交审批（如业务线配置了审批人）
3. 审批人审批通过/拒绝
4. 通过后可以开启执行

审批状态通过飞书 Webhook 通知审批人。

---

## 应用场景

| 场景 | 说明 | 使用功能 |
|------|------|----------|
| 灰度测试 | 验证新功能在真实流量下的稳定性 | 录制 + 回放（多目标） |
| 回归测试 | 确保系统变更不破坏现有功能 | 录制 + 回放 + Diff |
| 接口自动化 | 单接口和场景的自动化测试 | API 测试 + 断言 |
| A/B 比对 | 对比不同版本的响应差异 | 多目标回放 + Diff（Host 模式） |
| 全链路压测 | 容量评估与性能瓶颈识别 | 回放（循环+并发+限流） |
| 故障演练 | 混沌工程建设 | 回放 + 流量染色 |
| AccessLog | 轻量级访问日志分析 | 录制（log_enabled）+ ES 查询 |
| UI 回归 | 移动端/Web 端 UI 自动化 | UI 自动化（Airtest/Midscene） |
| 用例管理 | 测试用例统一管理 | 用例池 + 计划用例 |

---

## 行业对比与差异化优势

**调研维度**：
- **商业方案**：MeterSphere、Apifox 等
- **企业实践**：字节、腾讯、转转、得物
- **开源方案**：月光宝盒、JVM-SandBox、GoReplay、JMeter
- **公司内部**：各团队自研工具，分散且深度绑定业务

**MirrorSphere 差异化**：
- 深度定制 GoReplay 内核，满足企业级需求
- 多租户 + RBAC 权限 + 审批流程
- Go 高性能，支持高并发压测
- Kubernetes 调度，Worker 弹性伸缩
- 自研 Diff Engine，多目标响应差异分析
- 私有部署，数据不离开企业内部
- 集成 AI 辅助分析和用例生成
- 支持 MSDK 等自研加密压缩协议的自动编解码
- 一站式平台：录制 + 回放 + API 测试 + UI 自动化 + 用例管理

---

## 项目成果

通过技术创新实现了该领域在团队内从 0 到 1 的突破，将"流量录制-回放-分析-关联用例"全流程标准化、产品化、平台化。

开发过程大量使用 AI 辅助编程（Web 前端占比 70%+，服务端占比 50%+），平台已上线并在发行团队投入使用：

- **质量保障体系升级**：100% 还原生产流量，回归性接口测试漏测率降为 0
- **成本优化与提效**：压测机器成本降低约 50%，人力成本由 2-3 人天降至 1 人天
- **用例覆盖率提升**：QA 零感知接口协议复杂性，MSDK 自动化用例覆盖率提升 10%+
- **生态补位**：填补团队技术生态空白，为上层工具提供基础能力支撑
- **跨团队认可**：mobapay QA、中台 Web QA 团队对参与共建表达兴趣

2026 H1 目标：完成 70% 测试用例迁移至该平台。

---

## 使用基础手册

### 快速入门：创建流量录制任务

1. 进入「流量录制」页面
2. 点击「新建录制任务」
3. 填写任务名称，选择业务线
4. 选择 Agent（已注册的录制器实例）
5. 配置过滤规则（可选）：URL 白名单、Method 白名单、Header 过滤
6. 设置录制时长
7. 提交 → 等待审批（如需） → 开启录制

### 快速入门：创建流量回放任务

1. 进入「流量回放」页面
2. 点击「新建回放任务」
3. 选择关联的录制任务（input_src 来自录制文件）
4. 选择 Worker（最多 5 个，用于并行回放）
5. 配置回放目标地址（output_dst，支持多目标用于 A/B 对比）
6. 配置回放策略：限流、并发、循环、时长
7. 选择执行模式：即时/定时/定期
8. 提交 → 审批 → 开启回放

### 快速入门：API 自动化测试

1. 进入「API 测试」页面
2. 创建 API 模块树（按业务分组）
3. 新增 API 接口：选择 Method、填写 Path、配置 Headers/Query/Body
4. 或从录制流量批量导入接口
5. 为接口创建测试用例，配置断言规则
6. 点击「测试」执行单次测试
7. 或配置定时执行计划，自动化回归

### 快速入门：Mock 请求

1. 进入「Mock」页面
2. 配置 HTTP 请求：Host + Method + Path + Headers + Body
3. 可配置算法策略（加密/签名）
4. 可配置前后置操作和断言
5. 点击「测试」预览请求/响应
6. 或点击「生成 Curl」获取命令行命令
7. 创建 Mock 计划批量执行

### 快速入门：测试用例管理

1. 进入「测试用例池」或「测试计划用例」
2. 创建模块树（多层级目录）
3. 新增用例：填写名称、优先级(P0-P3)、前置条件、操作步骤、预期结果
4. 或通过 Excel/CSV 文件批量导入
5. 测试计划用例支持多环境（test/pre/prod）通过状态标记
6. 查看统计汇总（通过率、待测数、失败数）

### 快速入门：UI 自动化测试

1. 进入「UI 自动化」页面
2. 确保有已注册的 Airtest Agent 或 Midscene Agent
3. 上传测试代码包（包含 .air 目录或 Midscene 脚本）
4. 配置默认执行 Agent 和执行模式
5. 开启执行 → 查看执行历史 → 查看报告

---

## 部署

所有组件均支持私有化部署、容器/非容器部署。

**Recorder Sidecar 部署示例**：
```yaml
containers:
- command:
  - ./bootstrap.sh
  - --biz=adbi
  - --name=流量录制实验
  image: sg-harbor.moonton.net/public/msdk/mirrorsphere-recorder:v1.0
  resources:
    limits: { cpu: 500m, memory: 1Gi }
    requests: { cpu: 200m, memory: 500Mi }
  securityContext:
    capabilities:
      add: [NET_ADMIN, NET_RAW]
    runAsUser: 0
```

**可观测性**：各服务接入 Prometheus + Grafana + Hela，实现日志收集、指标收集、指标展示、多渠道告警。

---

## Harness 与 DeerFlow 的关系

`harness` 不是独立替代 MirrorSphere 的平台，而是 MirrorSphere 的 AI 工程目录。

- DeerFlow 负责通用 super-agent 运行时与 UI
- Harness 负责 MirrorSphere 私有知识、skills、runtime overlay、评测与 MCP 能力

当用户在 AI Chat 中询问 "MirrorSphere 是什么" 时，应优先以上述平台定义为准，而不是引用外部世界知识。
