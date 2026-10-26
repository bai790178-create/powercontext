# PowerContext 离谱冒险 NPC（Dify DSL）

这是一个可直接导入 Dify 的 Workflow。用户输入行动后，Dify 的 HTTP Request 节点调用 `powercontext_bridge.py`：

1. 以 `user_id` 映射到一个独立的 PowerContext Scope；
2. 调用 `POST /v1/memory/search` 找回这个玩家之前的冒险记忆；
3. 根据记忆和本轮行动生成一段带有随机风格的 NPC 剧情；
4. 调用 `POST /v1/memory/remember` 保存本轮行动和剧情；
5. 把结果作为 Dify Workflow 输出。

## 导入和启动

1. 在 Dify 导入 [`adventure_npc.yml`](./adventure_npc.yml)。
2. 准备 PowerContext Server（示例地址 `http://127.0.0.1:8000`），并确认其 API 可访问。
3. 在桥接服务中配置：

```powershell
$env:POWERCONTEXT_URL = "http://127.0.0.1:8000"
$env:POWERCONTEXT_TOKEN = "" # 如果服务开启 Bearer 鉴权则填写
$env:POWERCONTEXT_DEFAULT_SCOPE = "dify-adventure"
python -m pip install -r requirements.txt
uvicorn powercontext_bridge:app --host 0.0.0.0 --port 8787
```

如果 Dify 与桥接服务不在同一台机器，把 Workflow 环境变量 `POWERCONTEXT_BRIDGE_URL` 改成 Dify 能访问的桥接服务地址。

## 验证样例

同一个 `user_id` 连续运行两次：

```text
user_id: alice
message: 我把会说话的冰箱带上船
```

然后再次运行：

```text
user_id: alice
message: 我让冰箱负责谈判
```

第二次回复应引用第一次的冰箱和船，并在 PowerContext 中产生新的记忆。换成 `user_id: bob` 后，Bob 不应看到 Alice 的冒险。

## 文件

- `adventure_npc.yml`：Dify Workflow 导出文件。
- `powercontext_bridge.py`：Dify HTTP 节点调用的桥接服务。
- `openapi.yaml`：可选的 Dify 自定义工具注册描述。
- `requirements.txt`：桥接服务依赖。
