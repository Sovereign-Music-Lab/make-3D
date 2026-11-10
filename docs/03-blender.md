# 2. Blender: GLB → 언리얼용 FBX

언리얼 MCP의 `SkeletalMeshTools.import_file`은 **FBX/OBJ만** 받습니다. AssetFurnace 결과(GLB)는 Blender로 변환합니다.
창을 띄우지 않는 백그라운드 실행이라 열려 있는 Blender 작업에 영향이 없습니다.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/glb_to_fbx_unreal.py -- in_idle.glb out.fbx
```

옵션: `--scale 100`(기본, m→cm), `--fps 24`(기본).

## 스크립트가 처리하는 것

모두 실제 import에서 문제가 됐던 것들입니다.

| 문제 | 증상 | 처리 |
|---|---|---|
| glTF importer가 뼈 표시용 구(Icosphere)를 추가 | 2 m짜리 구가 캐릭터와 함께 들어감 | 스킨되지 않은 메시는 제외 |
| 기본 장면 길이 1–250 프레임 | 4초 idle이 10.4초로 늘어남 | 장면 프레임을 동작 범위에 맞춤 |
| 단위 불일치 | 언리얼에서 메시는 cm, 애니 이동값은 m → **애니메이션을 켜면 캐릭터가 사라짐** | 메시·뼈·이동 키를 ×100 후 `FBX_SCALE_ALL`로 내보냄 |
| `FBX_SCALE_ALL`만 쓰면 | 메시가 0.9 cm로 들어와 노멀이 깨져 흰색·검은색 얼룩 | 위와 같음(×100을 먼저) |

## Blender를 더 쓰는 경우 (가이드)

- **형태 수정·리토폴로지·UV 정리**: Blender MCP(`execute_blender_code`)로 실시간 조작하거나 직접 작업 후, 같은 스크립트로 FBX 변환.
- **사람 캐릭터를 처음부터**: MPFB(MakeHuman) 애드온 + `mpfb` MCP. 얼굴 표정(ARKit 52개 블렌드셰이프)을 넣을 수 있어 얼굴 모캡에 유리합니다.
- 셰이더 노드는 이름이 아니라 `node.type`으로 찾으세요(이름은 언어 설정에 따라 바뀜).
