# 문제 해결 (실제로 겪은 것)

| 증상 | 원인 | 해결 |
|---|---|---|
| AssetFurnace `This engine is not installed yet` | 사진 없이 글 설명만 넘겨 그림 엔진이 필요해짐 | 사진은 `image_path`로. 글 설명을 쓰려면 `flux-image` 설치 |
| 이어서 마감했는데 옛 모델로 진행됨 | 원래 asset id로 `continue_asset` | 새 버전 id로 이어 가기(응답의 `newer_version` 확인) |
| 다운로드 진행률이 0%에서 안 움직임 | 동시 다운로드 중 표시 미갱신 | 받는 폴더 크기로 확인 |
| `a download is already running` | 다운로드는 하나씩만 | 앞 다운로드가 끝난 뒤 다시 |
| `something is already being made` | 생성 작업은 하나씩만 | 취소/완료 후 다시 |
| 로컬 모델 Claude Code에서 `auto mode cannot determine the safety` | auto 권한 모드 판정이 느린 로컬 모델에서 시간 초과 | `--permission-mode default` |
| 언리얼 `Cannot load …: the level has unsaved changes` | 복제한 레벨이 아직 디스크에 없음 | 새 레벨 `save_assets` 후 `load_level` |
| `FbxFactory does not support ".glb"` | MCP import는 FBX/OBJ만 | `scripts/glb_to_fbx_unreal.py` |
| 애니메이션을 켜면 캐릭터가 사라짐(바운드는 그대로) | 메시 cm / 애니 이동값 m | 변환 스크립트의 ×100 + `FBX_SCALE_ALL` |
| 캐릭터 전체에 흰색·검은색 얼룩 | 메시가 0.9 cm로 들어와 노멀 계산이 깨짐 | 위와 같음 |
| 애니메이션 길이가 10.4초 | Blender 기본 장면 길이로 구움 | 변환 스크립트가 프레임 범위를 맞춤 |
| 2 m짜리 구가 같이 들어옴 | glTF importer의 뼈 표시용 메시 | 변환 스크립트가 제외 |
| `set_properties … could not be set: bUpdateAnimationInEditor` / `BoneTree` | MCP로 쓸 수 없는 속성 | 에디터에서 직접 하거나 다른 방법 |
| `get_referencers` → `'NoneType' object is not iterable` | 언리얼 MCP 쪽 오류(참조 없음일 때 추정) | 참조 확인이 안 되면 에셋 삭제를 보류 |
| 재질 컴파일 `PreSkinnedPosition … not available in the Pixel shader` | 정점 셰이더 전용 노드 | `VertexInterpolator`를 거쳐 사용 |
| 재질 연결 시 입력 이름 오류 | 입력이 하나뿐인 노드는 이름이 `None`으로 보고됨 | 빈 이름/`None`으로 연결(`ue_sequin_material.py` 처리) |
| 비치는 소매 가장자리 줄무늬 | 디더 투명 + 정지 캡처 | MRQ Temporal 샘플로 렌더하면 대부분 해결 |
| 언리얼을 다시 열었더니 캐릭터가 회색(텍스처 없음) | import가 만든 재질·텍스처를 저장하지 않고 에디터가 닫힘 | `ue_import_character.py`가 폴더 안 에셋을 모두 저장(수정됨). 이미 잃었다면 다시 import |
| 작업 중 에디터가 `GracefulTerminationHandler`로 종료 | 정상 종료 신호(직접 종료 또는 메모리 부족 시 macOS가 종료) | AssetFurnace 생성처럼 무거운 작업과 동시에 돌리지 않기, 자주 저장 |
| 언리얼에서 얼굴이 다각형처럼 각져 보임(Blender에선 매끈) | glTF가 UV 이음매마다 정점을 나눠 언리얼이 조각별로 노멀 계산 | `glb_to_fbx_unreal.py`가 정점 용접 + 부드러운 노멀(기본). 그림자·밉맵은 원인 아님(확인함) |
| import 중 에디터가 몇 분 멈춤/종료됨 | 재질 슬롯마다 같은 텍스처를 중복으로 가져와 압축 | 두 번째부터 `--materials-from`으로 재질 재사용, 멈춘 것 같아도 2~3분 기다리기 |
| 얼굴 마스크에서 눈만 비어 있음 | PNG 알파=0인 곳의 색 데이터가 저장/로드 시 버려짐 | 알파는 항상 1, 데이터는 RGB에만(스크립트 수정됨) |
| 눈 흰자가 리본으로 분류됨 | 밝고 무채색이라 리본 규칙에 먼저 걸림 | 얼굴 영역 판정을 먼저(스크립트 수정됨) |
| 치마 뒤가 머리카락으로 분류됨 | AssetFurnace 텍스처에 머리색이 번져 있음 | `face.json`의 `hair_min_z`를 치마 위쪽 높이로 |

