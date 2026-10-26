import http from "node:http";
import { SeekdbClient } from "seekdb";

const port = Number(process.env.PORT || 8103);
const config = {
  host: process.env.SEEKDB_HOST || "127.0.0.1",
  port: Number(process.env.SEEKDB_PORT || 2881),
  user: process.env.SEEKDB_USER || "root",
  password: process.env.SEEKDB_PASSWORD || "",
  database: process.env.SEEKDB_DATABASE || "test",
};
const client = new SeekdbClient(config);
let ready;

async function init() {
  if (!ready) {
    ready = client.execute(`CREATE TABLE IF NOT EXISTS stepfun_documents (
      id VARCHAR(128) PRIMARY KEY, body TEXT NOT NULL, metadata JSON,
      embedding VECTOR(384) NOT NULL,
      FULLTEXT INDEX ft_body (body) WITH PARSER ik,
      VECTOR INDEX vec_embedding (embedding) WITH (DISTANCE=l2, TYPE=hnsw)
    )`);
  }
  await ready;
}

async function body(req) {
  let text = "";
  for await (const chunk of req) text += chunk;
  return text ? JSON.parse(text) : {};
}

function json(res, status, value) {
  const text = JSON.stringify(value);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(text) });
  res.end(text);
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/health") {
      await init();
      await client.execute("SELECT 1");
      return json(res, 200, { ok: true, backend: "seekdb-js" });
    }
    await init();
    if (req.method === "POST" && req.url === "/api/documents") {
      const input = await body(req);
      for (const doc of input.documents || []) {
        await client.execute(
          "INSERT INTO stepfun_documents (id, body, metadata, embedding) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE body=VALUES(body), metadata=VALUES(metadata), embedding=VALUES(embedding)",
          [doc.id, doc.body, JSON.stringify(doc.metadata || {}), JSON.stringify(doc.embedding)],
        );
      }
      return json(res, 200, { written: (input.documents || []).length, backend: "seekdb-js" });
    }
    if (req.method === "POST" && req.url === "/api/search") {
      const input = await body(req);
      const rows = await client.execute(
        `SELECT id, body, metadata,
                MATCH(body) AGAINST (? IN NATURAL LANGUAGE MODE) AS lexical_score,
                l2_distance(embedding, ?) AS vector_distance
           FROM stepfun_documents
          ORDER BY MATCH(body) AGAINST (? IN NATURAL LANGUAGE MODE)
                 + 1.0 / (1.0 + l2_distance(embedding, ?)) DESC
          LIMIT ?`,
        [input.query || "", JSON.stringify(input.embedding || []), input.query || "", JSON.stringify(input.embedding || []), Number(input.limit || 5)],
      );
      return json(res, 200, { query: input.query || "", results: rows || [], backend: "seekdb-js", hybrid: true });
    }
    json(res, 404, { error: "not found" });
  } catch (error) {
    json(res, 503, { error: String(error?.message || error) });
  }
});

server.listen(port, () => console.log(`StepFun seekdb-js bridge listening on ${port}`));
