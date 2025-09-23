// path: vsc-no-code/nocode-data/src/extension.ts
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

export function activate(ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(
        vscode.commands.registerCommand('nocode.data.openDesigner', async () => {
            const ws = vscode.workspace.workspaceFolders?.[0];
            if (!ws) return vscode.window.showErrorMessage('Open a workspace first');
            const project = path.join(ws.uri.fsPath, '.nocode');
            fs.mkdirSync(project, { recursive: true });
            const projFile = path.join(project, 'project.json');
            if (!fs.existsSync(projFile)) fs.writeFileSync(projFile, JSON.stringify({ name: 'nocode-project', sources: [] }, null, 2));
            vscode.window.showInformationMessage('No-Code project initialized at ' + project);
        })
    );
}

export function deactivate() { }
