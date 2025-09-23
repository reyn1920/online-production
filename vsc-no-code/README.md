# No-Code Studio Pack

Add-only scaffold for a VS Code no-code studio using free libraries. See `docs/` for quickstart.

## Ollama Bridge

The `No-Code: Ollama Chat Selection` command sends the current editor selection (or a prompted message) to a local Ollama HTTP server and opens the reply in a new editor tab.

Usage:

- Start Ollama server (`npm run ollama:server`) and ensure `OLLAMA_HOST` in `.env.local` is set (defaults to `http://127.0.0.1:11434`).
- Open an editor, select text, press `Ctrl+Alt+O` or run `No-Code: Ollama Chat Selection` from the Command Palette.

The extension is located at `vsc-no-code/nocode-ollama`.
