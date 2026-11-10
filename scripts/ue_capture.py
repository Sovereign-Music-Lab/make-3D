"""Capture the Unreal viewport from fixed cameras around a point (for before/after comparisons).

    python3 ue_capture.py --out shots/ --tag before --target 0 0 --height-cm 170 [--simulate 2]

Writes <tag>_front.png, <tag>_threeq.png, <tag>_side.png, <tag>_back.png.
The character is assumed to face +Y (Unreal default for Blender/MPFB/AssetFurnace exports);
pass --front-yaw if yours faces elsewhere. --simulate N starts Simulate-In-Editor, waits N s
(so animation plays), captures, then stops.
"""
import argparse
import base64
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_mcp import T, call  # noqa: E402

ANNOT = {'gridSpacing': 0, 'gridExtent': 0, 'gridHeight': 0, 'maxLabelDistance': 0,
         'classFilter': {'refPath': '/Script/Engine.Actor'}, 'maxLabels': 0}


def shoot(path, x, y, z, pitch, yaw):
    t = {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0}}
    call(T.EDITOR, 'SetCameraTransform', {'transform': t})
    r = call(T.EDITOR, 'CaptureViewport', {'captureTransform': t, 'annotations': ANNOT, 'bShowUI': False})
    with open(path, 'wb') as f:
        f.write(base64.b64decode(r['image']['data']))
    print(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='.')
    p.add_argument('--tag', default='shot')
    p.add_argument('--target', type=float, nargs=2, default=(0, 0), metavar=('X', 'Y'))
    p.add_argument('--floor-z', type=float, default=0.0)
    p.add_argument('--height-cm', type=float, default=170)
    p.add_argument('--front-yaw', type=float, default=90.0, help='direction the character faces')
    p.add_argument('--simulate', type=float, default=0)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    dist = a.height_cm * 1.1
    cz = a.floor_z + a.height_cm * 0.6
    views = {'front': 0, 'threeq': 45, 'side': 90, 'back': 180}
    if a.simulate:
        call(T.EDITOR, 'StartPIE', {'options': {'bSimulate': True, 'playMode': 'PlayMode_Simulate'}})
        time.sleep(a.simulate)
    try:
        for name, off in views.items():
            ang = math.radians(a.front_yaw + off)
            x, y = a.target[0] + dist * math.cos(ang), a.target[1] + dist * math.sin(ang)
            shoot(os.path.join(a.out, f'{a.tag}_{name}.png'), x, y, cz, -4, a.front_yaw + off + 180)
    finally:
        if a.simulate:
            call(T.EDITOR, 'StopPIE', {})


if __name__ == '__main__':
    main()
