# No-Code Ollama Bridge

Small VS Code extension to send editor selection to a local Ollama HTTP chat endpoint and open the reply in a new editor tab.

Quick start:

1. Start Ollama: `npm run ollama:server`.
2. Ensure `.env.local` has `OLLAMA_HOST=http://127.0.0.1:11434` and `OLLAMA_MODEL` set.
3. In VS Code (F5), run `No-Code: Ollama Chat Selection` or press `Ctrl+Alt+O` when an editor is focused.

Settings (workspace `settings.json`):

```json
"nocode.ollama.host": "http://127.0.0.1:11434",
"nocode.ollama.model": "llama3.1:8b"
```

This extension is add-only and uses free local Ollama models.
