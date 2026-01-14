const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let logStream;
let logFilePath;

function getWorkspaceRoot() {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    return null;
  }
  return folders[0].uri.fsPath;
}

function ensureLogStream(rootPath) {
  logFilePath = path.join(rootPath, 'terminal.log');
  logStream = fs.createWriteStream(logFilePath, { flags: 'a' });
}

function activate(context) {
  const rootPath = getWorkspaceRoot();
  if (!rootPath) {
    vscode.window.showWarningMessage('Terminal Logger: No workspace folder found.');
    return;
  }

  ensureLogStream(rootPath);

  const writeListener = vscode.window.onDidWriteTerminalData((event) => {
    if (!logStream) {
      return;
    }
    const stamp = new Date().toISOString();
    const prefix = `[${stamp}] [${event.terminal.name}] `;
    logStream.write(prefix + event.data);
  });

  const openLogCommand = vscode.commands.registerCommand('terminalLogger.openLog', async () => {
    if (!logFilePath) {
      return;
    }
    const doc = await vscode.workspace.openTextDocument(logFilePath);
    await vscode.window.showTextDocument(doc, { preview: false });
  });

  context.subscriptions.push(writeListener, openLogCommand);
}

function deactivate() {
  if (logStream) {
    logStream.end();
  }
}

module.exports = {
  activate,
  deactivate
};
