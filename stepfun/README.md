# StepFun 端侧混合检索知识库

这是一个浏览器端完成 embedding 的迷你知识库。文档和查询文本由 Transformers.js 在用户设备本地向量化，浏览器只把原文、元数据和向量发送给本地 `server.py`，由 seekdb 保存并执行向量与全文混合检索。

## 启动

1. 在 `stepfun/` 目录运行 `npm install`。
2. 启动本地 seekdb，并执行 `schema.sql`；也可以按 `server.mjs` 的配置使用 seekdb embedded mode。
3. 设置 `SEEKDB_HOST`, `SEEKDB_PORT`, `SEEKDB_USER`, `SEEKDB_PASSWORD` 和 `SEEKDB_DATABASE`。
4. 运行 `npm start`，然后在 Chrome/Edge 打开 `index.html`。`server.mjs` 通过官方 `seekdb` JavaScript SDK 访问数据库；`server.py` 是等价的 MySQL 协议兼容启动方式。

模型从公开的 `Xenova/all-MiniLM-L6-v2` 加载，使用 `quantized: true` 的 INT8 权重；浏览器优先选择 WebGPU，能力不可用时自动切换 WASM。推理函数只在浏览器执行，服务端不接受文本并代为调用模型。

## 验证

导入文本后等待“已写入 seekdb”，再输入查询。搜索请求携带浏览器生成的 query embedding；`server.py` 使用单条 SQL 同时计算全文匹配和向量距离，再以加权分数排序。
