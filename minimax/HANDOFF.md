# 接续点：已完成（2026-10-28）

用户配置了真实 MiniMax Key 后，本目录已完成全部本地可执行的验收步骤。业务代码已由 MiniMax 修改，
固定测试通过；如需再次实验，使用新的 `--evidence-dir`，不要覆盖 `evidence/minimax-run-001/`。

## 已完成与证据

- 独立仓库：`F:/OceanBase/powercontext-minimax`，本地分支 `competition/minimax-sdd-2026`。
- HEAD 为官方竞赛基线 `d647275c308e09b7b623f322a26f5c4e85734fb0`；本目录内容为本分支上的新增材料。
- 工作内容仅在 `minimax/`。其他题目目录和部署实例未修改。
- 独立 `.venv`：Python 3.12.14、PowerContext 1.4.1、seekdb 1.4.0；版本见 `evidence/dependencies-windows-py312.txt`。
- 2026-10-28 重新启动隔离实例：seekdb `127.0.0.1:2882`、PowerContext `127.0.0.1:8910`；
  PID 记录在 `.runtime/services.json`，日志同在 `.runtime/`。
- `evidence/baseline/`：8 项业务测试，4 项目标功能断言失败、4 项回归通过，退出码 1，无错误或跳过。
- `evidence/context-tests.json`、`.log`、`.xml`：9 项真实集成测试通过（修改后重新运行）。
- `evidence/import.json`、`evidence/context-before-minimax.json`：真实 SQL 查询及规格、代码、测试来源。
- `evidence/state-saved.json`、`evidence/context-restored.json`：真实 PowerContext 写入与另一进程复用。
- `evidence/minimax-run-001/`：真实 MiniMax 请求、公开响应（含 usage）、修改前后快照、`change.diff`。
  模型 `MiniMax-M3.1-Flash`，finish_reason `stop`，仅修改 `sample/tasks.py`。
- `evidence/after/`：同一份测试文件（哈希与 baseline 一致）8 项全部通过，退出码 0。
- `evidence/state-completed.json`、`evidence/context-completed.json`：完成状态写入与修改后上下文，
  其中代码来源哈希与 `evidence/after/result.json:source_sha256` 一致。

## 结果摘要

- 修改前：`list_tasks` 忽略 `status`，4 项目标断言失败。
- MiniMax 修改：`status is None` 返回全部副本，否则按 `task["status"] == status` 过滤，输入不被修改、返回新列表。
- 修改后：8/8 通过；目标与回归用例未改动。

## 后续可选动作

1. 若需提交平台：仅在本分支本地提交，推送与提测需用户明确授权。
2. 重新生成证据前先 `import`，避免索引哈希与磁盘不一致；重复模型调用使用新的证据目录。
3. 停止服务：`.\scripts\stop-local.ps1`（核对 PID 与进程归属，保留数据）。

## 环境细节

- F 盘 exFAT：当前会话文件策略为 danger-full-access，可直接写入；此前提权说明已不适用。
- Git 使用单次 `-c safe.directory=F:/OceanBase/powercontext-minimax`，未配置全局通配信任。
- uv 缓存必须指定项目内 `UV_CACHE_DIR`；普通 pip 不依赖此设置。
- PowerContext 1.4.1 的 `search_memory` 返回命中字段为 `hit.memory.text` 和 `hit.memory.artifact`。
- 本地验证不等于平台评审通过；未执行远程推送或平台提测。
