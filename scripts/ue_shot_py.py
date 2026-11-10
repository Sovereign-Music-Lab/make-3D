"""Unreal-side (run with ue_python.py): move the level viewport camera and request a
high-res screenshot (written on the next frames; wait ~2 s before the next call).
Fallback for ue_capture.py when the MCP server is not answering.

    python3 ue_python.py ue_shot_py.py <out.png> X Y Z PITCH YAW [W=1280 H=720]
"""
import sys

import unreal

a = sys.argv[1:]
out = a[0]
x, y, z, pitch, yaw = map(float, a[1:6])
w, h = (int(a[6]), int(a[7])) if len(a) > 7 else (1280, 720)
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
    unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
unreal.AutomationLibrary.take_high_res_screenshot(w, h, out)
print('requested', out)
