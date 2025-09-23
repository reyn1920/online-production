// path: vsc-no-code/nocode-gen-react/src/extension.ts
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export function activate(ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(
        vscode.commands.registerCommand('nocode.generateReactApp', async (uri: vscode.Uri) => {
            const target = uri?.fsPath || (await vscode.window.showInputBox({ prompt: 'Target directory for generated app' }));
            if (!target) return;
            const dest = path.join(target, 'ui');
            fs.mkdirSync(dest, { recursive: true });
            // Minimal index.html and package.json
            fs.writeFileSync(path.join(dest, 'index.html'), '<!doctype html><div id="root"></div>');
            fs.writeFileSync(path.join(dest, 'package.json'), JSON.stringify({ name: 'nocode-ui', scripts: { dev: 'vite' } }, null, 2));
            vscode.window.showInformationMessage('Generated UI app at ' + dest);
        })
    );
}

export function deactivate() { }
