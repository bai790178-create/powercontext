# 一页技术说明

## 任务与结构

本作品为已有开发助手提供任务上下文，并以 `sample/tasks.py:list_tasks` 增加状态筛选为验证任务。
CLI 入口为 `python -m sdd_context`，输入任务 ID，输出 JSON。

```text
规格 / 代码 / 测试 + manifest
           │ import
           ▼
     seekdb 工程资料与标签索引
           │ 根据任务标签执行 SQL 查询
           ▼
     有来源、文件哈希、行号的上下文 ◄── PowerContext 恢复的进展
           │
           ▼
     MiniMax 开发助手 → sample/tasks.py 的修改 → 固定功能与回归测试
                                                   │
                                                   ▼
                                    PowerContext 保存进展与验证结果
```

## 各项技术的实际分工

| 技术 | 接口与作用 | 可核对记录 |
| --- | --- | --- |
| seekdb 1.4.0 | PyMySQL / SQL；保存真实文件全文、SHA-256、符号和标签；按任务标签查询 | `evidence/import.json`、上下文中的 `database_query`、真实返回行 |
| PowerContext 1.4.1 | 官方 Python Client / HTTP；独立任务 Scope 中显式写入 Memory 并检索 | `evidence/state-saved.json`、`evidence/context-restored.json`、制品 ID 与版本 |
| MiniMax | 官方兼容 HTTP 接口；接收真实上下文，返回唯一业务文件的完整修改 | `evidence/minimax-*/request.json`、公开响应、代码快照、diff |

PowerContext 自身的持久层使用独立 SQLite 文件，由 PowerContext 服务管理；工程资料及其检索使用真实 seekdb。
不需要为显式状态读写配置额外生成模型或 embedding 模型。

## 上下文选择与更新

`sample/manifest.json` 显式维护任务描述、检索词、资料路径、类型和符号。SQL 对任务检索词与资料标签做连接，
按匹配数量排序；另一个 CSV 导出任务使用不同标签，验证输出不是固定答案。定位信息引用真实文件及完整内容。
索引与磁盘哈希不一致时要求重新导入，避免使用旧快照；导入在一个事务中替换本模块索引。

## 验证与边界

业务测试固定不变：筛选、未知状态、空字符串是目标行为；无筛选查询、顺序、空输入、输入不可变和迭代器是回归行为。
集成测试使用真实数据库与 PowerContext，覆盖语义规格更新、空状态写入和独立进程读取。
这是小型、显式标签检索方案；未实现自动依赖分析、向量检索或完整 Agent 会话恢复。
任务状态从每个任务 Scope 的最多 50 条匹配 Memory 中按保存时间选最新一条，适用于本次小规模验证。

当前已完成真实 MiniMax 调用与修改后验证：模型接收检索上下文，只改 `sample/tasks.py`，8 项固定业务测试全部通过。
本地验收清单各项均有对应证据；平台评审与远程提测不属于本地可完成的步骤。
