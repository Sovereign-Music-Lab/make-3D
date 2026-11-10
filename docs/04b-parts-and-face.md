# 3-2. 옷·부위 분리와 눈 깜빡임·입 움직임

AssetFurnace 캐릭터는 몸·머리카락·옷이 **한 덩어리 메시**이고, 눈과 입은 **텍스처에 그려져** 있습니다(얼굴 뼈·블렌드셰이프 없음).
이 단계는 형태를 바꾸지 않고 (1) 부위별 재질 슬롯으로 나누고 (2) 눈·입 마스크 텍스처를 만들어 언리얼 재질로 깜빡이고 입을 엽니다.
리그·스킨 웨이트·애니메이션은 그대로입니다.

> 상태: 검증. 한 캐릭터로 끝까지 돌렸습니다. 색·위치 규칙은 캐릭터마다 조금씩 조정이 필요합니다(아래 "조정").

## 1) 눈·입 위치 찾기 (정면 직교 렌더)

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/render_front_ortho.py -- rigged.glb face_front.png 0 0.375 0.15 800
```

- 인자: 중심 x, 중심 z, 화면 폭(모델 단위 m), 해상도. 픽셀 (px,py) → 모델 `x = cx - size/2 + px/res*size`, `z = cz + size/2 - py/res*size`
- 그림을 보고 두 눈·입의 중심과 반지름, 얼굴 영역을 읽어 `face.json`에 적습니다([예시](../examples/face_config_example.json)).

## 2) 부위 분리 + 얼굴 마스크

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/split_parts_face_masks.py -- idle.glb parts.glb face.json preview_dir/
```

- 결과: `parts.glb` (재질 슬롯 `AF_Skin, AF_Face, AF_Hair, AF_Dress, AF_Sleeves, AF_Bows, AF_Shoes` + 머리 부분의 `*_Head`), `parts_facemask.png`
- 분류: 면마다 텍스처 색(HSV)·위치·방향으로 나눈 뒤 이웃 다수결로 다듬음
- `preview_dir/parts_front|side|back.png`: 부위별 색으로 칠한 확인용 렌더
- 얼굴 마스크(얼굴 텍스처 UV 공간): **R=눈, G=입, B=눈/입 안의 세로 위치(위 0 → 아래 1), A=1**

확인(마스크를 얼굴에 초록으로 표시):

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/check_facemask.py -- parts.glb parts_facemask.png mask_check.png 0 0.36 0.1
```

### 조정 (`face.json`의 선택 항목)

| 키 | 기본값 | 언제 바꾸나 |
|---|---|---|
| `hair_min_z` | 0.02 | 치마 뒤가 머리카락으로 잡힐 때 올림(텍스처에 머리색이 번진 경우) |
| `hem_z` | -0.08 | 다리에 옷 조각이 섞일 때(치마 끝 높이) |
| `torso_half_width` | 0.075 | 소매/몸통 경계 |
| `sleeve_min_z` | 0.03 | 손·치마 옆이 소매로 잡힐 때 올림 |

## 3) 언리얼로

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/glb_to_fbx_unreal.py -- parts.glb parts.fbx
python3 scripts/ue_import_character.py --fbx parts.fbx --folder /Game/Characters/Hero_v2 --name SK_Hero_v2 --height-cm 157 --at 0 0 --floor-z 0
```

같은 캐릭터를 다시 가져올 때는 `--materials-from /Game/Characters/Hero_v1` 로 이전 재질·텍스처를 슬롯 이름으로 재사용하세요.
재질 9개 × 텍스처를 매번 새로 가져오면 에디터가 몇 분간 멈춘 것처럼 보입니다.

## 4) 눈 깜빡임·입 재질

```bash
python3 scripts/ue_face_anim_material.py --folder /Game/Characters/Hero_v2 --name M_Hero_FaceAnim \
  --base-texture /Game/Characters/Hero_v1/Image_3 --mask-file parts_facemask.png \
  --eyelid 0.51 0.29 0.22 --assign-actor "<액터 refPath>" --slot-name AF_Face
```

| 파라미터 | 기본 | 뜻 |
|---|---|---|
| `BlinkPeriod` | 3.6 | 자동 깜빡임 간격(초). 한 번에 약 0.24초 |
| `AutoBlink` | 1 | 0이면 자동 깜빡임 끔 |
| `BlinkManual` | 0 | 0~1, 수동 눈 감기(포즈·연출용). 자동과 큰 쪽 적용 |
| `MouthOpen` | 0 | 0~1, 입 벌림(립싱크·얼굴 캡처 연결용) |
| `EyelidColor` | 피부색 | 눈꺼풀 색. 눈 위 피부를 샘플링해서 넣기(선형 색) |
| `LashColor`, `MouthColor` | 진한 갈색, 어두운 빨강 | 속눈썹 선, 입 안 |

- 에디터 화면은 시간이 흐르지 않아 깜빡이는 순간에 멈춰 보일 수 있습니다. 움직임은 Simulate/Play/렌더에서 확인.
- 검증: `BlinkManual` 0 / 0.5 / 1 과 `MouthOpen` 0.9 고정값 캡처, Simulate에서 눈 영역 밝기가 `BlinkPeriod` 주기로 변하는 것 확인.

## 한계

- 진짜 옷 레이어(옷 아래 몸이 있는 별도 의상)가 아니라 **재질 슬롯 분리**입니다. 천 시뮬레이션을 하려면 옷을 따로 모델링하거나 몸을 채워 넣어야 합니다.
- 입은 텍스처에 어두운 틈을 그리는 방식이라 턱이 실제로 내려가지 않습니다. 실제 턱 움직임은 Blender에서 셰이프 키/턱 뼈 추가가 필요합니다.
- 얼굴 캡처(Live Link Face)는 ARKit 곡선을 `BlinkManual`·`MouthOpen`에 연결하면 됩니다(가이드: [07-motion-capture](07-motion-capture.md)).
