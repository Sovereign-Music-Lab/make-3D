#!/bin/sh
# Register the MCP servers this pipeline uses with Claude Code (user scope).
# Paths come from environment variables so nothing personal is hard-coded.
# Re-running is safe: an existing entry is removed and added again.
#
#   ASSETFURNACE_DIR=~/image-to-3dlab sh setup/register_mcp.sh
#
# Optional (skipped when unset or missing):
#   BLENDER_MCP_CMD        e.g. ~/.local/bin/mcp-for-blender   (pip/uv tool "mcp-for-blender")
#   PAINTER_MCP_PY         python that has substance_painter_mcp installed
#   MPFB_MCP_CMD           mpfb-mcp executable
set -eu

add() { name=$1; shift; claude mcp remove "$name" -s user >/dev/null 2>&1 || true; claude mcp add-json --scope user "$name" "$1"; }

# Unreal Engine 5.8 built-in MCP (enable plugins "Model Context Protocol" + "Editor Toolset")
claude mcp remove unreal -s user >/dev/null 2>&1 || true
claude mcp add --scope user --transport http unreal "${UE_MCP_URL:-http://127.0.0.1:8000/mcp}"

if [ -n "${ASSETFURNACE_DIR:-}" ] && [ -x "$ASSETFURNACE_DIR/lab" ]; then
  add assetfurnace "{\"type\":\"stdio\",\"command\":\"$ASSETFURNACE_DIR/lab\",\"args\":[\"mcp\"]}"
else
  echo "skip assetfurnace (set ASSETFURNACE_DIR to the AssetFurnace install folder)"
fi

if [ -n "${BLENDER_MCP_CMD:-}" ] && [ -x "$BLENDER_MCP_CMD" ]; then
  add blender "{\"type\":\"stdio\",\"command\":\"$BLENDER_MCP_CMD\",\"args\":[],\"env\":{\"BLENDER_HOST\":\"127.0.0.1\",\"BLENDER_PORT\":\"9876\",\"DISABLE_TELEMETRY\":\"true\"}}"
else
  echo "skip blender (optional: set BLENDER_MCP_CMD)"
fi

if [ -n "${PAINTER_MCP_PY:-}" ] && [ -x "$PAINTER_MCP_PY" ]; then
  add substance-painter "{\"type\":\"stdio\",\"command\":\"$PAINTER_MCP_PY\",\"args\":[\"-m\",\"substance_painter_mcp\"],\"env\":{\"SP_MCP_BRIDGE_HOST\":\"127.0.0.1\",\"SP_MCP_BRIDGE_PORT\":\"60043\",\"SP_MCP_BRIDGE_TIMEOUT\":\"120\"}}"
else
  echo "skip substance-painter (optional: set PAINTER_MCP_PY)"
fi

if [ -n "${MPFB_MCP_CMD:-}" ] && [ -x "$MPFB_MCP_CMD" ]; then
  add mpfb "{\"type\":\"stdio\",\"command\":\"$MPFB_MCP_CMD\",\"args\":[]}"
else
  echo "skip mpfb (optional: set MPFB_MCP_CMD)"
fi

claude mcp list
