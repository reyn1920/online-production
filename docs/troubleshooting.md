# Troubleshooting

- If the webview is blank, ensure the extension's webview bundle exists at `webview/dist/main.js`.
- If `node` or `npm` are missing, install LTS Node from nodejs.org (free).
- If Python venv is missing, create `.venv` with `python -m venv .venv` and install required packages.
- If port 8000 is in use, run `lsof -iTCP:8000 -sTCP:LISTEN -n -P` to identify the process and `kill` if acceptable.
- Rule-1 guard hits will be in `rule1_guard_report.txt`.

## Permanent fix for VS Code freezes caused by report files

1. Quit VS Code fully (Code > Quit or Command+Q) and re-open it.
2. Open `.vscode/settings.json` and add an exclude pattern for `*_report.txt` files.

Example entry:

```json
"files.exclude": {
	"**/*_report.txt": true
}
```

This prevents VS Code from attempting to read report files that may be large or generated frequently.

## Fixing the "command not found: python" issue

On macOS the `python` binary may not be present by default. Use your virtual environment and activate it before running scripts:

```bash
source .venv/bin/activate
# or for a venv named venv
source venv/bin/activate
```

After activation, the `python` command will point to the environment's interpreter.
