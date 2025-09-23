// path: vsc-no-code/nocode-logic/src/extension.ts
import * as vscode from 'vscode';

export function activate(ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(
        vscode.commands.registerCommand('nocode.logic.openBuilder', () => {
            const panel = vscode.window.createWebviewPanel('nocodeLogic', 'No-Code Logic', vscode.ViewColumn.Two, { enableScripts: true });
            panel.webview.html = `<!doctype html><div id="root">Logic Builder will load here</div>`;
        })
    );
}

export function deactivate() { }
