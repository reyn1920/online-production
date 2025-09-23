// path: vsc-no-code/nocode-studio-core/src/extension.ts
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand('nocode.openStudio', () => {
        const panel = vscode.window.createWebviewPanel(
            'nocodeStudio',
            'No-Code Studio',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        const html = getWebviewContent(context, panel);
        panel.webview.html = html;
    });

    context.subscriptions.push(disposable);
}

function getWebviewContent(context: vscode.ExtensionContext, panel: vscode.WebviewPanel) {
    const scriptUri = panel.webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'webview', 'dist', 'main.js'));
    return `<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>No-Code Studio</title>
  </head>
  <body>
    <div id="root">Loading No-Code Studio...</div>
    <script src="${scriptUri}"></script>
  </body>
  </html>`;
}

export function deactivate() { }
