import { pipeline, env } from "https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2/+esm";

env.allowLocalModels = false;
const status = document.querySelector("#status");
const modelId = "Xenova/all-MiniLM-L6-v2";
let embedder;

function setStatus(message) { status.textContent = message; }

async function loadEmbedder() {
  if (embedder) return embedder;
  const device = navigator.gpu ? "webgpu" : "wasm";
  try {
    embedder = await pipeline("feature-extraction", modelId, { device, quantized: true });
    setStatus(`本地模型已加载：${device.toUpperCase()}，INT8 quantized=true`);
  } catch (error) {
    if (device !== "wasm") {
      embedder = await pipeline("feature-extraction", modelId, { device: "wasm", quantized: true });
      setStatus("WebGPU 不可用，已自动降级到 WASM；推理仍在浏览器本地执行。");
    } else throw error;
  }
  return embedder;
}

async function embed(texts) {
  const model = await loadEmbedder();
  const values = [];
  for (const text of texts) {
    const tensor = await model(text, { pooling: "mean", normalize: true });
    values.push(Array.from(tensor.data));
  }
  return values;
}

document.querySelector("#load").onclick = () => loadEmbedder().catch((e) => setStatus(`模型加载失败：${e.message}`));

document.querySelector("#ingest").onclick = async () => {
  try {
    const bodies = document.querySelector("#documents").value.split(/\n+/).map((x) => x.trim()).filter(Boolean);
    const vectors = await embed(bodies);
    const response = await fetch("http://127.0.0.1:8103/api/documents", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ documents: bodies.map((body, i) => ({ id: `doc-${i + 1}`, body, metadata: { source: "browser" }, embedding: vectors[i] })) }),
    });
    if (!response.ok) throw new Error(await response.text());
    setStatus(`已在浏览器本地生成 ${bodies.length} 个向量，并写入 seekdb。`);
  } catch (e) { setStatus(`写入失败：${e.message}`); }
};

document.querySelector("#search").onclick = async () => {
  try {
    const query = document.querySelector("#query").value.trim();
    const [embedding] = await embed([query]);
    const response = await fetch("http://127.0.0.1:8103/api/search", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ query, embedding, limit: 5 }),
    });
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    document.querySelector("#results").innerHTML = data.results.map((item) =>
      `<article><b>${item.id}</b><p>${item.body}</p><small>lexical=${Number(item.lexical_score).toFixed(3)}; vector distance=${Number(item.vector_distance).toFixed(3)}</small></article>`
    ).join("");
    setStatus(`seekdb 已完成全文 + 向量混合检索，共返回 ${data.results.length} 条。`);
  } catch (e) { setStatus(`检索失败：${e.message}`); }
};
