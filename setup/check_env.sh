#!/bin/sh
# Report what this pipeline needs and what is present. Changes nothing.
#   sh setup/check_env.sh
UE_APP="${UE_APP:-/Users/Shared/Epic Games/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app}"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
ok() { printf '  [ok]   %s\n' "$1"; }
no() { printf '  [--]   %s\n' "$1"; }

echo "machine: $(uname -sm)"
[ "$(uname -m)" = "arm64" ] && ok "Apple Silicon" || no "Apple Silicon expected (AssetFurnace Metal engines)"
mem=$(sysctl -n hw.memsize 2>/dev/null); [ -n "$mem" ] && echo "  memory: $((mem / 1073741824)) GB (24 GB+ recommended)"
command -v claude >/dev/null && ok "Claude Code $(claude --version 2>/dev/null | head -1)" || no "Claude Code (https://claude.com/claude-code)"
[ -d "$UE_APP" ] && ok "Unreal Editor: $UE_APP" || no "Unreal Engine 5.8 (set UE_APP)"
[ -x "$BLENDER" ] && ok "$("$BLENDER" --version 2>/dev/null | head -1)" || no "Blender 5.x (set BLENDER)"
[ -n "${ASSETFURNACE_DIR:-}" ] && [ -x "$ASSETFURNACE_DIR/lab" ] && ok "AssetFurnace: $ASSETFURNACE_DIR" || no "AssetFurnace (set ASSETFURNACE_DIR; install: https://assetfurnace.com)"
command -v ollama >/dev/null && ok "Ollama $(ollama --version 2>/dev/null)" || no "Ollama (optional, local models)"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' && ok "python3 $(python3 -V 2>&1)" || no "python3 >= 3.9"

if curl -s -m 3 -o /dev/null -X POST "${UE_MCP_URL:-http://127.0.0.1:8000/mcp}" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"check","version":"0"}}}'; then
  ok "Unreal MCP answering"
else
  no "Unreal MCP not answering (open your project with the Model Context Protocol plugin on)"
fi
curl -s -m 3 -o /dev/null http://127.0.0.1:8777/ && ok "AssetFurnace studio on :8777" || no "AssetFurnace studio not running (starts on first MCP call, or run ./lab)"
