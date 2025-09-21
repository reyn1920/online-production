SHELL := /bin/bash
ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

.PHONY: all py js go rust sec ci quick rca upr

all: ci

quick:
	@echo "Running fast gate..."
	pre-commit run --all-files || true

py:
	@echo "Python: ruff + basedpyright"
	ruff check . --fix
	ruff format .
	basedpyright --level error || true

js:
	@echo "JS/TS: biome + tsc"
	pnpm dlx @biomejs/biome check .
	tsc -p tools/ai_debug/ts/tsconfig.json --pretty false --noEmit || true

go:
	@echo "Go: vet + golangci-lint"
	go vet ./... || true
	golangci-lint run --config tools/ai_debug/go/.golangci.yml || true

rust:
	@echo "Rust: cargo check + clippy"
	cargo check || true
	cargo clippy -- -D warnings || true

sec:
	@echo "Security: semgrep + gitleaks"
	semgrep --config tools/ai_debug/semgrep.yml --error --strict || true
	gitleaks detect --no-git --redact --config tools/ai_debug/gitleaks.toml || true

ci: quick py js go rust sec
	@echo "CI suite complete."

upr:
	bash tools/ai_debug/guard/upr_gate.sh

rca:
	@echo "Local LLM RCA → patch (minimal changes first)"
	python3 - << 'PY'
import subprocess, os, tempfile, pathlib
root = pathlib.Path(os.getenv("ROOT", ".")).resolve()

def run(cmd):
  try:
    out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, cwd=root, text=True)
    return out.strip()
  except subprocess.CalledProcessError as e:
    return e.output

reports = []
reports.append(("ruff", run("ruff check .")))
reports.append(("basedpyright", run("basedpyright --level error")))
reports.append(("biome", run("pnpm dlx @biomejs/biome check .")))
reports.append(("tsc", run("tsc -p tools/ai_debug/ts/tsconfig.json --pretty false --noEmit")))
body = "\n\n".join([f"### {k}\n```\n{v}\n```" for k,v in reports if v and v.strip()])
if not body.strip():
  print("No findings to explain.")
  raise SystemExit(0)

prompt = f"""
You are a senior code engineer. Explain the root cause of the following findings and propose the smallest viable diffs.
Rules:
- Change comments/strings first when possible.
- Do not rename identifiers or remove functions.
- Keep patches minimal and focused.
- Output a unified diff only, nothing else.
Context:
{body}
"""
with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
  tf.write(prompt)
  pth = tf.name
model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
print(subprocess.getoutput(f"ollama run {model} < {pth}"))
PY
