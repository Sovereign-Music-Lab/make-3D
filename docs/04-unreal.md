# 3. Unreal Engine: import · 배치 · 애니메이션 · 재질

모든 스크립트는 에디터가 열려 있고 MCP 플러그인이 켜져 있으면 바로 동작합니다(언리얼 Python 불필요).

## import + 배치 + idle

```bash
python3 scripts/ue_import_character.py --fbx ./char.fbx --folder /Game/Characters/Hero --name SK_Hero \
  --height-cm 170 --at 0 0 --floor-z 0 [--yaw 0] [--level /Game/Maps/Stage]
```

- 생성: `SK_Hero`, `SK_Hero_Skeleton`, `SK_Hero_Anim`, 재질·텍스처 (같은 폴더)
- 크기: 메시 바운드로 키를 재서 `--height-cm`에 맞게 액터 스케일 자동 계산(AssetFurnace 결과는 보통 약 90 cm)
- 바닥: 메시 아래쪽이 `--floor-z`에 닿게 z를 계산
- 애니메이션: `AnimationSingleNode` + 반복 재생으로 설정 후 레벨·에셋 저장
- 같은 이름이 있으면 **덮어쓰지 않고 중단**

에디터 뷰포트는 첫 포즈로 멈춰 보입니다. 움직임은 Simulate/Play에서 확인합니다:

```bash
python3 scripts/ue_capture.py --out shots --tag hero --target 0 0 --height-cm 170 --simulate 2
```

## 레벨 다루기 요령

- 레벨을 복제한 직후에는 저장해야 열 수 있습니다: `AssetTools.save_assets([새 레벨])` → `SceneTools.load_level`.
  (안 하면 `the level has unsaved changes` 오류)
- 비교는 원본 레벨을 복제한 새 레벨에서. 원본은 그대로 둡니다.

## 재질: 시퀸 드레스 예제

```bash
python3 scripts/ue_sequin_material.py --folder /Game/Characters/Hero/Materials --name M_Sequin \
  --assign-actor "<액터 refPath>" --slot 3
```

- 시퀸: 셀 노이즈로 조각마다 노멀을 기울이고 색을 섞음. pre-skinned 위치 기준이라 움직여도 무늬가 몸에 붙어 있음.
- 비치는 소매: 드레스와 소매가 **한 재질 슬롯**일 때, 몸 중심에서 좌우 거리 17–20 cm 밖을 디더 투명으로.
  슬롯이 따로 있으면 `--sleeve-start 999`로 끄고 소매에는 별도 반투명 재질을 쓰세요.
- 조절: Material Instance를 만들어 `SequinCellsPerCm`, `SequinTilt`, `SequinMetallic`, `SequinRoughness`, `SequinChampagne`, `SequinSilver`, `SleeveOrganza`, `SleeveOpacity` 값 변경.
- 알려진 한계: 정지 캡처에서 디더 소매 가장자리에 줄무늬가 보일 수 있음.

## 자주 쓰는 MCP 호출 (`scripts/ue_mcp.py`)

```python
from ue_mcp import T, call, set_props, get_props, ref
call(T.SCENE, 'get_current_level', {})
call(T.SCENE, 'find_actors', {'root': None, 'name': '', 'actor_type': None, 'tag': None, 'bounds': None, 'collision_channels': None})
call(T.ACTOR, 'get_actor_bounds', {'actor': actor})
call(T.ASSET, 'duplicate', {'path': '/Game/Maps/A', 'new_path': '/Game/Maps/A_v2'})
call(T.SKELETAL_MESH, 'get_material_slots', {'mesh': ref('/Game/Characters/Hero/SK_Hero')})
```

툴셋별 전체 도구와 입력 형식은 `describe(T.SCENE)` 처럼 확인하세요. 추측하지 말고 스키마를 먼저 보는 게 빠릅니다.
