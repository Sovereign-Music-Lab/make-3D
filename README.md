# make-3D

**사진 한 장(또는 글 설명)에서 언리얼 캐릭터 → 텍스처 마무리 → 모션캡처 → 영상까지.**
Claude Code가 MCP로 AssetFurnace · Blender · Unreal Engine 5.8 · Substance 3D Painter를 직접 조작하는 로컬 3D 파이프라인입니다.
생성은 전부 내 Mac에서 돌고, 이 저장소에는 스크립트와 사용법만 있습니다(모델 파일·에셋 없음).

> From one photo (or a text idea) to an animated Unreal Engine character and a rendered video,
> driven by Claude Code through MCP. Scripts and docs only — no weights or assets. Apache-2.0.

```text
사진/아이디어 ─▶ AssetFurnace ─▶ Blender ─▶ Unreal Engine ─▶ Substance Painter ─▶ 완성 점검 ─▶ 모션캡처 ─▶ 영상
             (3D·리깅·idle)   (FBX 변환)   (import·재질·배치)  (텍스처 마무리)                  (Live Link 등)  (Sequencer·MRQ)
```

## 단계별 상태

정직하게 표시합니다. **검증**은 이 스크립트로 실제 끝까지 돌려 본 단계, **가이드**는 절차만 정리하고 아직 이 저장소에서 자동화·검증하지 않은 단계입니다.

| 단계 | 도구 | 상태 | 문서 |
|---|---|---|---|
| 0. 설치·MCP 연결 | Claude Code, `setup/` | 검증 | [docs/01-setup.md](docs/01-setup.md) |
| 1. 사진/아이디어 → 3D 캐릭터(리깅·idle) | AssetFurnace | 검증 | [docs/02-character.md](docs/02-character.md) |
| 2. GLB → FBX (언리얼 단위 문제 해결) | Blender (백그라운드) | 검증 | [docs/03-blender.md](docs/03-blender.md) |
| 3. 언리얼 import·배치·애니메이션·재질 | Unreal 5.8 MCP | 검증 | [docs/04-unreal.md](docs/04-unreal.md) |
| 3-2. 옷·부위 분리, 눈 깜빡임·입 움직임 | Blender + Unreal 재질 | 검증 | [docs/04b-parts-and-face.md](docs/04b-parts-and-face.md) |
| 3-3. 가닥 헤어 (Groom) | Blender + Unreal Python | 검증(정지 화면, 물리 제외) | [docs/04c-strand-hair.md](docs/04c-strand-hair.md) |
| 4. 텍스처 마무리 | Substance 3D Painter | 가이드 | [docs/05-substance-painter.md](docs/05-substance-painter.md) |
| 5. 완성 점검 | 캡처 스크립트 | 검증(캡처) / 가이드(체크리스트) | [docs/06-finish.md](docs/06-finish.md) |
| 6. 모션캡처 | Live Link Face, 영상 모캡, IK Retargeter | 가이드 | [docs/07-motion-capture.md](docs/07-motion-capture.md) |
| 7. 영상 만들기 | Sequencer, Movie Render Queue, ffmpeg | 가이드 | [docs/08-video.md](docs/08-video.md) |
| 문제 해결 | — | 실제로 겪은 문제 | [docs/troubleshooting.md](docs/troubleshooting.md) |

## 필요한 것

- Apple Silicon Mac, 메모리 24 GB 이상 권장, 디스크 여유 30 GB 이상(AI 모델 파일)
- [Claude Code](https://claude.com/claude-code)
- Unreal Engine 5.8 (내장 플러그인 **Model Context Protocol**, **Editor Toolset** 사용)
- Blender 5.x
- [AssetFurnace](https://assetfurnace.com) (로컬 사진→3D, 무료·오픈소스)
- 선택: Substance 3D Painter 12.x, iPhone(얼굴 모캡), Ollama(로컬 모델)

## 빠른 시작 (예제: “은색 우주복을 입은 고양이 우주비행사”)

사진이 없어도 됩니다. 예제는 글 설명으로 그림부터 그려서 진행합니다(AssetFurnace에 그림 엔진 `flux-image` 필요).
내 사진을 쓰려면 3번에서 `image_path`만 바꾸면 됩니다.

1. 환경 확인과 MCP 등록
   ```bash
   sh setup/check_env.sh
   ```
   ```bash
   ASSETFURNACE_DIR=~/image-to-3dlab sh setup/register_mcp.sh
   ```
2. 언리얼에서 작업할 프로젝트를 열고(플러그인 2개 켬), 이 폴더에서 Claude Code 실행
   ```bash
   claude
   ```
3. Claude Code에 요청
   ```text
   AssetFurnace로 캐릭터 만들어줘. 설명: "a cute cat astronaut in a silver space suit, full body, standing, plain grey background". want=character, finish_detail=high. 다 되면 preview 보여줘.
   ```
4. FBX로 변환
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/glb_to_fbx_unreal.py -- ~/image-to-3dlab/output/animate/<run>/<name>_idle.glb ./cat_astronaut.fbx
   ```
5. 언리얼로 가져와 바닥에 세우고 idle 재생
   ```bash
   python3 scripts/ue_import_character.py --fbx ./cat_astronaut.fbx --folder /Game/Characters/CatAstronaut --name SK_CatAstronaut --height-cm 120 --at 0 0 --floor-z 0
   ```
6. 4방향 캡처로 확인(Simulate로 움직이는 상태)
   ```bash
   python3 scripts/ue_capture.py --out shots --tag cat --target 0 0 --height-cm 120 --simulate 2
   ```

이후 [텍스처 마무리](docs/05-substance-painter.md) → [모션캡처](docs/07-motion-capture.md) → [영상](docs/08-video.md) 순서로 진행합니다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `setup/check_env.sh` | 필요한 프로그램·서버 상태 점검(아무것도 바꾸지 않음) |
| `setup/register_mcp.sh` | Claude Code에 MCP 서버 등록(경로는 환경변수) |
| `scripts/ue_mcp.py` | 언리얼 MCP 최소 클라이언트. `call(T.SCENE, 'get_current_level')` 한 줄로 호출 |
| `scripts/glb_to_fbx_unreal.py` | 리깅·애니메이션 GLB → 언리얼용 FBX (단위·프레임·헬퍼 메시 처리) |
| `scripts/ue_import_character.py` | FBX import → 실제 키로 바닥에 배치 → idle 반복 재생 → 저장 |
| `scripts/ue_capture.py` | 정면·3/4·측면·후면 고정 카메라 캡처(선택: Simulate 중 캡처) |
| `scripts/ue_sequin_material.py` | 시퀸 + 비치는 소매 드레스 재질 생성(파라미터로 조절) |
| `scripts/render_front_ortho.py` | 정면 직교 렌더(눈·입 위치 읽기용, 픽셀→모델 좌표 변환) |
| `scripts/split_parts_face_masks.py` | 한 덩어리 메시를 부위별 재질 슬롯으로 분리 + 눈·입 마스크 텍스처 |
| `scripts/check_facemask.py` | 얼굴 마스크가 눈·입에 맞는지 확인 렌더 |
| `scripts/ue_face_anim_material.py` | 자동 눈 깜빡임 + 입 벌림 재질 |
| `examples/prompts.md` | Claude Code에 그대로 붙여 쓰는 요청 예시 |
| `CLAUDE.md` | 이 저장소에서 Claude Code가 지킬 작업 규칙 |

## 작업 원칙

- 기존 레벨·에셋을 덮어쓰지 않고 새 폴더·새 이름으로 만든다(스크립트가 덮어쓰기를 거부함).
- “import 성공”과 “보기 좋음”은 다르다. 바뀔 때마다 캡처로 확인한다.
- AI 모델 파일 다운로드는 크기·라이선스를 확인하고 사람이 승인한 뒤에만 한다.
- 실존 인물을 닮게 만들 때는 본인 동의와 초상권을 확인한다.

## 라이선스

이 저장소의 스크립트와 문서: [Apache License 2.0](LICENSE). 이 저장소는 어떤 서드파티 소프트웨어·모델·에셋도 포함하거나 재배포하지 않습니다.
Unreal Engine, Blender, Substance 3D Painter, AssetFurnace와 그것이 받는 모델 파일은 각자의 라이선스를 따릅니다([NOTICE](NOTICE)).
