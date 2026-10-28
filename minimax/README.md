# MiniMax × OceanBase：SDD 工程上下文模块

本项目根据任务检索有效规格、相关代码与测试，恢复已保存进展，再把上下文交给 MiniMax 完成局部代码修改。
题面：[规有所依](https://oceanbase.yuque.com/org-wiki-obtech-vh7w9r/hc3pio/qlqnoryzrs7gtqbw)。
基于官方 `2026-competition-ecosystem` 分支的 `d647275c308e09b7b623f322a26f5c4e85734fb0` 开发，材料均在 `minimax/`。

**当前进度：已完成。真实 seekdb 检索、PowerContext 状态恢复、MiniMax 实际修改、修改后 8 项业务测试与 9 项集成测试均已实际运行并留存证据。**

## 依赖与配置

- 本次验证：Windows、Python 3.12.14、seekdb 1.4.0、PowerContext 1.4.1。
- 需要可访问的真实 seekdb / OceanBase MySQL 协议实例；Windows 启动脚本需要已安装的 seekdb 可执行文件。
  seekdb 获取方式参见 [官方项目](https://github.com/oceanbase/seekdb)。不依赖本机其他题目的数据库或业务数据。
- 所有以下命令均在本仓库的 `minimax/` 目录执行。`python` 指本目录 `.venv` 中的 Python。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

根据本机配置编辑 `.env`。数据库账号只需本项目专用数据库权限；默认 SQL 端口为 2882。
`MINIMAX_API_KEY` 填入用户本地获得的实际 Key，模型和 Base URL 按账号可用配置填写。
`.env` 和 `.runtime/` 已被 Git 忽略；配置示例无真实凭证。
模型参数依据 [MiniMax 官方接口文档](https://platform.minimaxi.com/docs/api-reference/text-openai-api)。
参赛赠送的 Token Plan 如何领取以主办方通知为准，本项目不自动购买资源。

## 启动服务

Windows：在新端口和本目录 `.runtime/` 中运行隔离实例，替换下方实际安装路径：

```powershell
.\scripts\start-local.ps1 -SeekdbExe 'C:\path\to\seekdb.exe'
python -X utf8 scripts/check-services.py
```

首次启动会初始化数据库与 Python 模块，可能需要一两分钟。未就绪时查看 `.runtime/` 下的两个 stderr 日志，
等待就绪后再执行检查；端口被占用时脚本会拒绝启动，不会停止其他进程。

Linux / macOS 或使用外部数据库时：先按 seekdb 官方说明启动兼容实例，在 `.env` 配置实际连接；
另开一个终端运行以下命令并保持运行。此路径未在当前 Windows 验证中执行。

```bash
python -m sdd_context.pc_server
```

PowerContext 只监听 `127.0.0.1:8910`；默认状态路径 `.runtime/powercontext/state.db`。
Windows seekdb 示例端口 2882，由数据库自身提供连接控制；不要将无密码示例暴露到公网。

## 不需要模型 Key 的验证

```powershell
python -X utf8 -m sdd_context --out evidence/import.json import
python -X utf8 scripts/record-tests.py baseline
python -X utf8 scripts/record-context-checks.py
python -X utf8 -m sdd_context --out evidence/context-before-minimax.json context TASK-001
```

`baseline` 在目标功能确实缺失、环境正常的情况下，记录 4 个目标断言失败、4 个回归用例通过。
外层记录程序成功退出表示“修改前证据符合预期”；其中保存的 pytest 退出码必须是 1。
9 个集成用例验证真实 SQL 检索、无关资料排除、语义规格更新、错误导入保护、独立进程状态复用等。
重导入检查会在独立临时样例中将“未知状态返回空列表”改成“抛出 ValueError”，确认上下文使用新内容。

输出 `context` 的结构包括 `task`、`sources`、`database_query`、`task_state`、`generated_at`。
每条来源包含真实相对路径、符号、内容、文件哈希和行号。`EXPORT-001` 查询只命中独立 CSV 规格。
如果源文件变化，先重新 `import`；模块会拒绝使用与磁盘不一致的索引。

## 保存并恢复任务进展

以下两条命令是独立进程，状态由真实 PowerContext 服务保存，不由 CLI 本地 JSON 模拟：

```powershell
python -X utf8 -m sdd_context --out evidence/state-saved.json save-state TASK-001 --done 'spec reviewed; baseline recorded' --todo 'run MiniMax edit and the unchanged tests' --test-result 'baseline: 4 target failures, 4 regression passes'
python -X utf8 -m sdd_context --out evidence/context-restored.json context TASK-001
```

`task_state.latest.state` 应与保存内容一致，且包含可追踪的 PowerContext 制品引用。
集成测试会为每次运行创建独立的新任务 Scope，先确认空状态，再写入和由新进程读取。
也可以停止再重启 PowerContext 服务，保留同一状态目录后运行第二条命令，核对引用和状态。

## 用真实 MiniMax 修改代码

本步已真实执行：`MiniMax-M3.1-Flash` 接收 `evidence/minimax-run-001/context.json` 中的检索上下文，
返回 `sample/tasks.py` 的完整修改（`evidence/minimax-run-001/change.diff`，`before.py` → `after.py`），
修改后 8 项固定业务测试全部通过（`evidence/after/result.json`，退出码 0，测试文件哈希未变）。
复现命令：

```powershell
python -X utf8 -m sdd_context modify TASK-001 --evidence-dir evidence/minimax-run-001
python -X utf8 scripts/record-tests.py after
python -X utf8 -m sdd_context --out evidence/state-completed.json save-state TASK-001 --done 'MiniMax edit; 8 unchanged business tests passed' --todo 'review final delivery' --test-result 'after: 8 passed; see evidence/after'
python -X utf8 -m sdd_context import
python -X utf8 -m sdd_context --out evidence/context-completed.json context TASK-001
```

上例命令对应本次已完成的记录；重复实验须替换 `--evidence-dir`，已有目录会被拒绝覆盖。未配置 Key 时 `modify` 明确报错，不会伪造模型记录。
`modify` 发起一次真实请求，无自动重试；
只允许修改 `sample/tasks.py`，不能修改测试。请求包含实际数据库上下文和恢复状态，响应保存公开输出与用量，
不保存 API Key 或私有思维链。若请求失败或输出不合法，保留失败记录，选择新证据目录重试。

验收不要求 MiniMax 每次生成完全相同的代码；以记录与提交代码差异对应、固定测试实际通过为准。

## 重置与复现

恢复修改前快照，不删除数据库、已保存状态或证据：

```powershell
python scripts/reset-sample.py evidence/baseline/tasks.py
python -X utf8 -m sdd_context import
```

修改完成后也可用 `evidence/after/tasks.py` 恢复修改后快照。重新验证基线会更新 `evidence/baseline/`，
有意重复模型调用时使用新的 `--evidence-dir`，避免覆盖历史模型记录。
干净环境先初始化数据库并 `import`，无需复制作者的 `.runtime/`；PowerContext 从新空库创建任务 Scope。

Windows 停止本项目创建的服务、保留数据：`.\scripts\stop-local.ps1`。脚本会核对 PID 和进程归属。

## 交付材料与限制

| 材料 | 路径 |
| --- | --- |
| 源码、样例与固定测试 | `sdd_context/`、`sample/`、`tests/` |
| 初始数据、有效规格和来源清单 | `sample/manifest.json`、`sample/specs/tasks.md`、`sample/tests/test_tasks.py` |
| 修改前代码快照、目标失败日志、版本与退出码 | `evidence/baseline/` |
| 真实数据库查询与来源 | `evidence/import.json`、`evidence/context-*.json` |
| 集成测试命令、日志与依赖版本 | `evidence/context-tests.json`、`.log`、`.xml` |
| PowerContext 写入与复用 | `evidence/state-saved.json`、`evidence/context-restored.json` |
| MiniMax 请求、公开响应、快照与差异 | `evidence/minimax-run-001/`（`request.json`、`response.json`、`change.diff`） |
| 修改后固定测试 | `evidence/after/`（`result.json`、`junit.xml`、`pytest.log`） |
| 完成状态与修改后上下文 | `evidence/state-completed.json`、`evidence/context-completed.json` |
| 技术结构与分工 | `TECHNICAL.md` |

检索采用显式标签，没有自动代码依赖推断或向量检索。PowerContext 检索最多 50 条状态匹配记录，适用于本样例规模。
本次未执行 Linux 路径、平台提测或远程推送，不能将本地集成通过写成全部赛题验收通过。
PowerContext、seekdb 作为官方依赖使用；样例、上下文模块和验证脚本在本参赛目录中编写。
