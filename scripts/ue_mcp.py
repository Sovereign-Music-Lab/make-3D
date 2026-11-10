"""Small client for Unreal Engine 5.8's built-in MCP server (ModelContextProtocol + EditorToolset).

The editor exposes three MCP tools: list_toolsets, describe_toolset, call_tool.
This module wraps them so scripts can call any EditorToolset tool in one line.

    from ue_mcp import call, T
    call(T.SCENE, 'get_current_level', {})

Endpoint defaults to http://127.0.0.1:8000/mcp; override with UE_MCP_URL.
"""
import json
import os
import urllib.request

URL = os.environ.get('UE_MCP_URL', 'http://127.0.0.1:8000/mcp')
_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
_session = None


class T:
    """Toolset names (exact strings the editor expects)."""
    _P = 'editor_toolset.toolsets.'
    ASSET = _P + 'asset.AssetTools'
    ACTOR = _P + 'actor.ActorTools'
    SCENE = _P + 'scene.SceneTools'
    OBJECT = _P + 'object.ObjectTools'
    MATERIAL = _P + 'material.MaterialTools'
    MATERIAL_INSTANCE = _P + 'material_instance.MaterialInstanceTools'
    SKELETAL_MESH = _P + 'skeletal_mesh.SkeletalMeshTools'
    STATIC_MESH = _P + 'static_mesh.StaticMeshTools'
    TEXTURE = _P + 'texture.TextureTools'
    EDITOR = 'EditorToolset.EditorAppToolset'
    LOGS = 'EditorToolset.LogsToolset'


def _post(body, timeout=300):
    headers = dict(_HEADERS)
    if _session:
        headers['Mcp-Session-Id'] = _session
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()  # notifications get an empty reply
        return resp.headers.get('Mcp-Session-Id'), (json.loads(body) if body.strip() else {})


def rpc(method, params=None):
    global _session
    if _session is None:
        sid, _ = _post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2025-06-18', 'capabilities': {},
            'clientInfo': {'name': 'make-3d', 'version': '1.0'}}})
        _session = sid or ''
        _post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    return _post({'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params or {}})[1]


def call(toolset, tool, args=None):
    """Call one EditorToolset tool. Returns its returnValue (or the whole result)."""
    r = rpc('tools/call', {'name': 'call_tool', 'arguments': {
        'toolset_name': toolset, 'tool_name': tool, 'arguments': args or {}}})
    res = r.get('result', {})
    if r.get('error') or res.get('isError'):
        raise RuntimeError(f'{toolset}.{tool}: {r}')
    text = res['content'][0].get('text', '')
    try:
        value = json.loads(text)
    except ValueError:
        return text
    return value.get('returnValue', value) if isinstance(value, dict) else value


def describe(toolset):
    """Tool names and input schemas of one toolset."""
    r = rpc('tools/call', {'name': 'describe_toolset', 'arguments': {'toolset_name': toolset}})
    return json.loads(r['result']['content'][0]['text'])


def set_props(obj, values):
    return call(T.OBJECT, 'set_properties', {'instance': obj, 'values': json.dumps(values)})


def get_props(obj, names):
    v = call(T.OBJECT, 'get_properties', {'instance': obj, 'properties': names})
    return json.loads(v) if isinstance(v, str) else v


def ref(path):
    """'/Game/Folder/Asset' -> {'refPath': '/Game/Folder/Asset.Asset'}"""
    return {'refPath': path if '.' in path.rsplit('/', 1)[-1] else f'{path}.{path.rsplit("/", 1)[-1]}'}


if __name__ == '__main__':
    print('level:', call(T.SCENE, 'get_current_level', {}))
