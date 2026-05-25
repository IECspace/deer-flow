# MirrorSphere 路线图与未来规划

## 1. 演进目标

MirrorSphere 以需求驱动为核心，盘活平台沉淀下来的流量数据资产，构建"能力-数据-价值"的正向循环。

当前平台已完成基于 HTTP 流量的测试场景核心能力交付，支撑了基础业务测试需求，在系统设计、功能丰富度、性能管理、智能化水平、产品体验等方面持续演进。

## 2. Harness AI 能力演进

### 2.1 阶段概览

```text
Phase 1: Knowledge Q&A           ← 已完成（91.3% 准确率）
Phase 2: Requirement Intelligence ← Skills 已就绪，MCP 部分就绪
Phase 3: Analysis Copilot        ← 规划中
Phase 4: Controlled Execution    ← 规划中
```

### 2.2 Phase 1: 知识问答（已完成）

**交付物**：
- MirrorSphere runtime overlay 生成
- 自定义 Agent 人设（mirrorsphere agent + SOUL）
- `mirrorsphere-knowledge` Skill
- 仓库索引器 + 知识包导出器
- 文件系统 MCP 接地
- 评测数据集（45 条 Q&A，80% 通过率阈值）

**验收结果**：
- 平台知识问答准确率：91.3%
- 代码定位命中率 > 85%
- DeerFlow 源码修改极少

### 2.3 Phase 2: 需求智能（Skills 已就绪）

**已就绪的 Skills**：

| Skill | 功能 | 状态 |
|-------|------|------|
| `mirrorsphere-prd-analysis` | PRD 解析 → 结构化分析 → 技术评审文档 | 结构已就绪 |
| `mirrorsphere-test-design` | PRD/技术文档 → 测试用例表 → MCP 入库 | 结构已就绪 |
| `mirrorsphere-mindmap-generation` | 需求/用例 → Mermaid 脑图 | 结构已就绪 |

**处理链**：
```text
PRD 文档
  → 文档解析（附件/URL/内联文本）
  → 需求拆分 + 场景提取
  → 技术评审文档生成（接口协议/流程图/架构/DB设计/安全）
  → 测试用例生成（用例名/优先级/前置条件/步骤/预期结果/实际结果/备注）
  → 用户确认后 → MCP tpc-batch-add 批量入库
  → 脑图生成
```

**MCP 集成**：
- `tpc-batch-add` — 批量插入测试计划用例到 portal 数据库
- `tpc-list` — 查询已有用例
- `module-tree` — 获取模块树帮助用户定位 module_id

### 2.4 Phase 3: 分析 Copilot（规划中）

**能力领域**：
- 智能测试用例池维护（缺失用例检测、重复用例提示）
- 根因分析（RCA）：回放失败 → 证据链 → 根因定位
- 变更影响分析
- 契约漂移检测

**RCA 处理链**：
```text
replay_id / record_id
  → 获取 replay_exec 数据
  → 关联 worker/agent 状态
  → 查询 ES 中的 Diff 结果
  → 检查 API 断言失败记录
  → 生成 RCA 报告（根因 + 证据链 + 影响范围 + 建议修复）
```

### 2.5 Phase 4: 受控执行（规划中）

**能力领域**：
- AI 起草流量录制任务配置
- AI 起草流量回放任务配置
- AI 推荐 Worker/Agent/过滤规则/并发配置

**安全策略**：
1. 只读推荐
2. 草稿生成供人工审核
3. 受控执行需明确审批

---

## 3. 平台能力增强路线

### 3.1 智能测试用例池 - Test Case Pool (TCP)

当前已具备基础用例 CRUD 和批量管理能力，未来智能化方向：

- **流量特征分析**：自动分析录制流量数据，总结流量特征
- **参数分类**：基于维度、路由、用户行为的参数分类
- **智能统计**：成功率统计、差异分布、字段变化趋势
- **错误归因**：借助 LLM 实现自动化错误分析与归因
- **自动化升级**：自动选择、生成、升级用例，而非手工维护

### 3.2 智能调度模块

当前 Worker 调度为手动选择（最多 5 个），未来：

- 根据任务负载智能扩缩容 Worker 资源
- 基于性能指标自动选择最优 Worker
- 更灵活地支持大规模流量测试（突破 MaxWorkerNum 限制）
- Kubernetes HPA 联动

### 3.3 性能与效率提升

| 方向 | 当前状态 | 规划 |
|------|----------|------|
| 输入源 | raw/file/tcp/kafka/custom | 增强 Kafka 双向支持 |
| 存储 | 本地文件 + S3 | 直连 OSS/GCS，无需本地中转 |
| 采集技术 | libpcap | eBPF 升级（更低开销） |
| 监控 | 基础 Prometheus | 完善核心组件性能指标 |

**eBPF 技术升级**：
- 底层流量录制技术从 libpcap 升级到 eBPF
- 实现更高效低开销的采集与过滤
- 减少内核态到用户态的数据拷贝

### 3.4 功能增强

| 功能 | 说明 | 依赖 |
|------|------|------|
| gRPC 录制回放 | 支持 gRPC 协议 | GoReplay 扩展 |
| 数据库容量评估 | MySQL/Redis 性能测试 | 新组件 |
| 协议编解码扩展 | 自定义协议内容编解码 | 插件化 |
| Chaos Mesh 对接 | 混沌工程 + 流量回放 | K8s Operator |
| 多端 APM | 集成应用性能监控 | 第三方 |

**接口协议适配详细说明**：
- MSDK 业务线接口具有多种数据格式：JSON、Protobuf
- 有加密压缩、签名等安全协议
- 平台已内置 Content-Length 同步更新机制
- 未来需支持用户自定义编解码插件

### 3.5 混沌工程（待对接）

- 对接 Chaos Mesh 进行故障注入
- 配合流量回放验证系统容错能力
- 影子流量：生产流量复制到测试环境故障注入
- 自动化恢复验证

## 4. 体验优化路线

### 4.1 功能体验

- 收集使用方的体验需求，持续提升平台易用性
- 简化录制/回放任务创建流程
- 增强 Diff 结果可视化（字段级高亮）
- 测试报告自动生成和推送

### 4.2 部署体验

- 完善部署手册
- 最小化 All-in-One 部署方案（单机 Docker Compose）
- Helm Chart 标准化 K8s 部署
- 一键初始化脚本

### 4.3 文档沉淀

- **标准 SOP**：场景化引导 + step-by-step 实操设计
- **需求池管理**：持续跟进功能迭代与用户反馈

## 5. 平台战略

### 5.1 技术资产复用

将平台打造为团队 AI 工程化能力的实战孵化底座：
- 改变当前后端团队 AI 应用碎片化的现状
- 通过持续迭代的真实业务场景沉淀体系化的 AI 落地方法论
- 实现团队技术能力的规模化提升

### 5.2 高价值场景突破

聚焦核心业务目标：
- 网络架构优化
- 测试效能提升（目标：稳定提升 30%+）
- 质量风险前置（目标：线上问题漏测率下降 50%）

### 5.3 生态共建

建立开放协同的平台生态机制：
- 面向全公司技术团队开放共建通道
- 打破团队壁垒
- "业务场景输入 → 平台能力迭代 → 多团队受益"正向循环
- mobapay QA 团队已表达共建兴趣
- 中台 Web QA 团队聚焦压测 + Chaos Mesh 联合使用

---

## 6. 技术债与改进项

### 6.1 已知技术债

| 项目 | 问题 | 影响 |
|------|------|------|
| Pilot/Portal 职责重叠 | 部分 handler/router 重复定义 | 维护成本 |
| GoReplay 版本锁定 | 深度定制难以跟进上游更新 | 安全/功能 |
| 前端 Rspack | 较新工具链，社区生态仍在发展 | 插件可用性 |
| Airtest-Agent Windows | 只能运行在 Windows 物理机 | 部署灵活性 |

### 6.2 改进方向

- Portal/Pilot 职责边界明确化（Portal 面向用户，Pilot 面向执行层）
- GoReplay 定制部分抽象为独立模块，降低升级耦合
- Airtest-Agent 探索 Docker for Windows 容器化

---

## 7. Skill 基础设施路线

| Skill | 状态 | 说明 |
|-------|------|------|
| `mirrorsphere-knowledge` | 已上线 | 平台知识问答 |
| `mirrorsphere-prd-analysis` | 结构已就绪 | PRD 分析 + 技术评审 |
| `mirrorsphere-test-design` | 结构已就绪 | 测试用例生成 + MCP 入库 |
| `mirrorsphere-mindmap-generation` | 结构已就绪 | 测试脑图生成 |
| `mirrorsphere-rca` | 规划中 | 根因分析 |
| `mirrorsphere-case-maintainer` | 规划中 | 用例池智能维护 |
| `mirrorsphere-record-replay-planner` | 规划中 | 录制回放任务规划 |

## 8. MCP 基础设施路线

| MCP 服务 | 状态 | 功能 |
|----------|------|------|
| filesystem | 已上线 | 代码仓库只读接地 |
| mirrorsphere-portal (tpc-batch-add) | 部分就绪 | 测试用例批量写入 |
| mirrorsphere-portal (tpc-list, module-tree) | 部分就绪 | 用例查询、模块树 |
| report/log/diff 检索 | 规划中 | RCA 证据获取 |
| record/replay 状态查询 | 规划中 | 任务状态获取 |
| 受控写入（录制/回放/Mock 创建） | 规划中 | AI 辅助创建任务 |

## 9. 评测基础设施路线

| 评测类别 | 状态 | 数据集 |
|----------|------|--------|
| 知识问答 | 已上线 | 45 条，91.3% 通过率 |
| 代码定位 | 已包含在知识问答中 | path/tag 维度评测 |
| PRD-to-case 质量 | 规划中 | - |
| PRD-to-mindmap 质量 | 规划中 | - |
| RCA 质量 | 规划中 | - |
| 任务草稿质量 | 规划中 | - |

## 10. 里程碑总结

| 里程碑 | 阶段 | 状态 |
|--------|------|------|
| M1. Runtime Overlay | Phase 1 | ✅ 已完成 |
| M2. Knowledge Base | Phase 1 | ✅ 已完成 |
| M3. Q&A Validation (91.3%) | Phase 1 | ✅ 已完成 |
| M4. PRD Analysis Skill 结构 | Phase 2 | ✅ 已完成 |
| M5. Test Design Skill 结构 | Phase 2 | ✅ 已完成 |
| M6. Mindmap Skill 结构 | Phase 2 | ✅ 已完成 |
| M7. MCP Portal 集成 | Phase 2 | 🔄 部分完成 |
| M8. RCA MVP | Phase 3 | 📋 规划中 |
| M9. Case Pool Assistant MVP | Phase 3 | 📋 规划中 |
| M10. Draft-Only Planner | Phase 4 | 📋 规划中 |
| M11. Controlled Execution | Phase 4 | 📋 规划中 |

## 11. 风险与缓解

| 风险 | 缓解策略 |
|------|----------|
| DeerFlow 版本漂移 | 所有自定义逻辑在 harness 内，通过 runtime 注入而非 patch |
| 知识质量不足 | 优先使用仓库实时读取，定期刷新知识包 |
| 不受控 AI 执行 | 早期保持只读，引入 draft-first + 审批门控 |
| PRD 质量参差 | 输出缺失信息清单，支持迭代优化而非一次性生成 |
| GoReplay 上游不活跃 | 核心增强抽象为独立模块，必要时可更换底层引擎 |
| 多团队共建协调 | 标准化 API 和插件接口，降低耦合 |
