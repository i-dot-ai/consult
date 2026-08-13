export const testAccessToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImVtYWlsQGV4YW1wbGUuY29tIn0.k27nav4gbG-2lIArYInTqP1GUz2LRuzb3lWandMKRoY"; // pragma: allowlist secret

// Minio (local S3) config, sourced from the environment (loaded from .env) so
// it stays in sync with what the backend uses. Playwright runs on the host, so
// the endpoint must be host-reachable (localhost:9100), not the in-container
// hostname (minio:9100).
export const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT ?? "http://localhost:9100";
export const MINIO_ACCESS_KEY = process.env.MINIO_ACCESS_KEY ?? "minioadmin";
export const MINIO_SECRET_KEY = process.env.MINIO_SECRET_KEY ?? "minioadmin";
export const S3_BUCKET = process.env.AWS_BUCKET_NAME ?? "i-dot-ai-dev-consult-data";
