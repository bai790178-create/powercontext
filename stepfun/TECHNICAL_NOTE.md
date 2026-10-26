# 技术说明

## 端侧推理

`app.js` 使用 Transformers.js 的 `feature-extraction` pipeline。模型是公开的 `Xenova/all-MiniLM-L6-v2`，加载 `quantized: true` 的 INT8 权重。`navigator.gpu` 存在时设置 `device: "webgpu"`；创建失败或浏览器不支持 WebGPU 时重新以 `device: "wasm"` 加载。文档向量和查询向量都走同一个本地 pipeline。

## seekdb 数据层

浏览器不在内存中保存检索索引。`server.py` 仅作为本地 HTTP 桥接层，把浏览器计算好的向量写入 seekdb 的 `stepfun_documents` 表。`/api/search` 通过一条 SQL 计算 `MATCH(body) AGAINST` 和 `l2_distance(embedding, ...)`，按两路分数融合后返回原文和元数据。

## 性能记录方式

页面记录模型首次加载、批量 embedding、写入和查询耗时。量化前后的体积可通过浏览器 Network 面板对比模型文件；检索质量使用同一组查询的 Recall@3 对比 INT8 与未量化权重。页面明确显示当前 `WebGPU` 或 `WASM` 后端。
