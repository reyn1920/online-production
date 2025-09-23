// path: vsc-no-code/nocode-ollama/src/extension.ts
import * as vscode from 'vscode';
import fetch from 'node-fetch';

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.commands.registerCommand('nocode.ollama.chatSelection', async () => {
            const editor = vscode.window.activeTextEditor;
            const selection = editor?.document.getText(editor.selection) || (await vscode.window.showInputBox({ prompt: 'Enter prompt for Ollama' }));
            if (!selection) return vscode.window.showInformationMessage('No prompt provided');

            const config = vscode.workspace.getConfiguration('nocode.ollama');
            const host = config.get<string>('host') || process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
            const model = config.get<string>('model') || process.env.OLLAMA_MODEL || 'llama3.1:8b';

            try {
                const resp = await fetch(`${host}/v1/chat/completions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model, messages: [{ role: 'user', content: selection }] })
                });
                const data = await resp.json();
                const reply = data?.choices?.[0]?.message?.content || JSON.stringify(data, null, 2);

                const doc = await vscode.workspace.openTextDocument({ content: reply, language: 'markdown' });
                await vscode.window.showTextDocument(doc, { preview: false });
            } catch (err) {
                vscode.window.showErrorMessage('Ollama request failed: ' + String(err));
            }
        })
    );
}

export function deactivate() { }
