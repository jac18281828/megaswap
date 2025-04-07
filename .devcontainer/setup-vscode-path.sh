
# Find the VS Code server remote-cli path and add it to PATH
VSCODE_CLI_PATH=$(find -L ${HOME}/.vscode-server/bin -name "remote-cli" -type d | head -n 1)
if [ -n "$VSCODE_CLI_PATH" ]; then
  export PATH="$PATH:$VSCODE_CLI_PATH"
  echo "Added VS Code remote CLI to PATH: $VSCODE_CLI_PATH"
fi
