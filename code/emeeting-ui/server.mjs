import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const port = Number(process.env.PORT || 5173);
const backend = process.env.BACKEND_HTTP || "http://backend:8080";

const app = express();

app.use(
  "/api",
  createProxyMiddleware({
    target: backend,
    changeOrigin: true,
    pathRewrite: { "^/api": "" },
  })
);

app.use(
  "/ws",
  createProxyMiddleware({
    target: backend,
    changeOrigin: true,
    ws: true,
  })
);

const distDir = path.join(__dirname, "dist");
app.use(express.static(distDir));
// Express 5 doesn't accept "*" string pattern here.
app.get(/.*/, (_req, res) => res.sendFile(path.join(distDir, "index.html")));

app.listen(port, "0.0.0.0", () => {
  console.log(`[ui] listening on :${port}, proxy -> ${backend}`);
});

