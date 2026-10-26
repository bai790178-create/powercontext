CREATE TABLE IF NOT EXISTS stepfun_documents (
  id VARCHAR(128) PRIMARY KEY,
  body TEXT NOT NULL,
  metadata JSON,
  embedding VECTOR(384) NOT NULL,
  FULLTEXT INDEX ft_body (body) WITH PARSER ik,
  VECTOR INDEX vec_embedding (embedding) WITH (DISTANCE=l2, TYPE=hnsw)
);
