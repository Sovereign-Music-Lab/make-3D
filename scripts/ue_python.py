"""Run Python inside the open Unreal editor (Python plugin "Remote Execution").

Enable once: Project Settings > Plugins > Python > Enable Remote Execution (or add to
Config/DefaultEngine.ini, then restart the editor):
    [/Script/PythonScriptPlugin.PythonScriptPluginSettings]
    bRemoteExecution=True
    RemoteExecutionMulticastBindAddress=127.0.0.1
    RemoteExecutionMulticastTtl=0

    python3 ue_python.py file.py [arg ...]    # args reach the script as sys.argv[1:]
    python3 ue_python.py -c "import unreal; print(unreal.SystemLibrary.get_engine_version())"

Uses the engine's own remote_execution.py (set UE_ROOT if the engine is elsewhere).
"""
import importlib.util
import json
import os
import sys
import time

UE_ROOT = os.environ.get('UE_ROOT', '/Users/Shared/Epic Games/UE_5.8/UE_5.8')
RE_PATH = os.path.join(UE_ROOT, 'Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py')


def _module():
    spec = importlib.util.spec_from_file_location('ue_remote_execution', RE_PATH)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def run(code, timeout=600):
    re_ = _module()
    cfg = re_.RemoteExecutionConfig()
    # macOS: a socket bound to 127.0.0.1 never receives multicast, so the editor (bound to
    # 127.0.0.1) cannot hear multicast pings. Listen on 0.0.0.0 for its multicast replies and
    # also send every discovery message straight (unicast) to the editor's 127.0.0.1 socket.
    cfg.multicast_bind_address = '0.0.0.0'
    r = re_.RemoteExecution(cfg)

    def patch(conn):
        import socket as _s
        sock = conn._broadcast_socket
        try:  # also join the group on loopback, where the editor sends its replies
            sock.setsockopt(_s.IPPROTO_IP, _s.IP_ADD_MEMBERSHIP,
                            _s.inet_aton(cfg.multicast_group_endpoint[0]) + _s.inet_aton('127.0.0.1'))
        except OSError:
            pass
        send = conn._broadcast_message

        def both(message):
            send(message)
            try:
                conn._broadcast_socket.sendto(message.to_json_bytes(), ('127.0.0.1', cfg.multicast_group_endpoint[1]))
            except OSError:
                pass
        conn._broadcast_message = both
    r.start()
    patch(r._broadcast_connection)
    try:
        t0 = time.time()
        while not r.remote_nodes:
            if time.time() - t0 > 8:
                raise RuntimeError('no Unreal editor answered: is Remote Execution enabled and the editor open?')
            time.sleep(0.2)
        r.open_command_connection(r.remote_nodes[0]['node_id'])
        res = r.run_command(code, unattended=True, exec_mode=re_.MODE_EXEC_FILE, raise_on_failure=False)
        return res
    finally:
        r.stop()


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == '-c':
        code = sys.argv[2]
    else:
        path = os.path.abspath(sys.argv[1])
        args = sys.argv[2:]
        code = f'import sys\nsys.argv = {json.dumps([path] + args)}\nexec(compile(open({path!r}).read(), {path!r}, "exec"))'
    res = run(code)
    for line in res.get('output', []):
        print(line.get('output', '').rstrip())
    if not res.get('success'):
        print('FAILED:', res.get('result')); sys.exit(1)


if __name__ == '__main__':
    main()
