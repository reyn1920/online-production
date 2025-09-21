import express from "express";
import cors from "cors";
import { exec } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

function runCmd(cmd, cwd = process.cwd()) {
  return new Promise((resolve) => {
    exec(cmd, { cwd, env: process.env, maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      const code = err ? (err.code ?? 1) : 0;
      resolve({ code, stdout: String(stdout), stderr: String(stderr) });
    });
  });
}

app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/run", async (req, res) => {
  const { action, args = [] } = req.body || {};
  let cmd = null;
  if (action === "quick") cmd = "make -C tools/ai_debug quick";
  if (action === "ci") cmd = "make -C tools/ai_debug ci";
  if (action === "rca") cmd = "make -C tools/ai_debug rca";
  if (action === "upr") cmd = "make -C tools/ai_debug upr";
  if (action === "ollama_pull") cmd = "ollama pull llama3.1:8b && ollama pull codestral || true";
  if (!cmd) return res.status(400).json({ ok: false, error: "unknown action" });
  const out = await runCmd(cmd, path.resolve(process.cwd()));
  res.json({ ok: out.code === 0, ...out });
});

app.post("/write", async (req, res) => {
  const { relPath, content } = req.body || {};
  if (!relPath) return res.status(400).json({ ok: false, error: "relPath required" });
  const dst = path.resolve(process.cwd(), relPath);
  await fs.promises.mkdir(path.dirname(dst), { recursive: true });
  await fs.promises.writeFile(dst, content ?? "", "utf8");
  res.json({ ok: true, path: relPath });
});

app.post("/llm-generate", async (req, res) => {
  const { prompt, relPath } = req.body || {};
  if (!prompt || !relPath) return res.status(400).json({ ok: false, error: "prompt and relPath required" });
  const cmd = `printf %s "$(cat << 'EOF'\n${prompt}\nEOF\n)" | ollama run ${process.env.OLLAMA_MODEL || "llama3.1:8b"}`;
  const out = await runCmd(cmd);
  const dst = path.resolve(process.cwd(), relPath);
  await fs.promises.mkdir(path.dirname(dst), { recursive: true });
  await fs.promises.writeFile(dst, out.stdout, "utf8");
  res.json({ ok: out.code === 0, path: relPath, bytes: out.stdout.length });
});

app.post("/flow", async (req, res) => {
  const { steps = [] } = req.body || {};
  const results = [];
  for (const step of steps) {
    if (step.kind === "run") {
      results.push(await runCmd(step.cmd || ""));
    } else if (step.kind === "write") {
      const dst = path.resolve(process.cwd(), step.relPath);
      await fs.promises.mkdir(path.dirname(dst), { recursive: true });
      await fs.promises.writeFile(dst, step.content ?? "", "utf8");
      results.push({ ok: true, path: step.relPath });
    } else if (step.kind === "llm") {
      const prompt = step.prompt || "";
      const cmd = `printf %s "$(cat << 'EOF'\n${prompt}\nEOF\n)" | ollama run ${process.env.OLLAMA_MODEL || "llama3.1:8b"}`;
      results.push(await runCmd(cmd));
    } else {
      results.push({ ok: false, error: "unknown step" });
    }
  }
  res.json({ ok: true, results });
});

const PORT = process.env.PORT || 4455;
app.listen(PORT, () => {
// DEBUG_REMOVED: console.log(`No-code server on http://localhost:${PORT}`);
});
