# 0. 설치와 MCP 연결

## 1) 프로그램 설치

| 프로그램 | 비고 |
|---|---|
| Claude Code | `claude --version` 으로 확인 |
| Unreal Engine 5.8 | Epic Games Launcher |
| Blender 5.x | `/Applications/Blender.app` (다른 위치면 `BLENDER` 환경변수) |
| AssetFurnace | `curl -fsSL https://assetfurnace.com/install.sh \| bash` — 설치 스크립트를 먼저 읽어 보고 실행 |
| (선택) Substance 3D Painter 12.x | 텍스처 마무리 |
| (선택) Ollama | 로컬 모델로 Claude Code를 쓸 때 |

점검:

```bash
sh setup/check_env.sh
```

## 2) 언리얼 프로젝트 플러그인

`Edit → Plugins` 에서 켜고 에디터 재시작:

- **Model Context Protocol** — 에디터가 `http://127.0.0.1:8000/mcp` 로 MCP 서버를 연다
- **Editor Toolset** — 레벨·액터·에셋·재질·캡처 도구 모음
- (권장) **Python Editor Script Plugin**, **Sequencer Scripting**, **Movie Render Queue**, **Live Link**, **Apple ARKit Face Support**, **Takes**

언리얼 MCP가 보여 주는 도구는 3개뿐입니다: `list_toolsets` → `describe_toolset` → `call_tool`.
`call_tool`의 `tool_name`은 접두사 없는 짧은 이름입니다. 예:

```json
{"toolset_name": "editor_toolset.toolsets.scene.SceneTools", "tool_name": "get_current_level", "arguments": {}}
```

## 3) Claude Code에 MCP 등록

```bash
ASSETFURNACE_DIR=~/image-to-3dlab sh setup/register_mcp.sh
```

선택 서버는 환경변수를 주면 함께 등록됩니다: `BLENDER_MCP_CMD`, `PAINTER_MCP_PY`, `MPFB_MCP_CMD`.
확인:

```bash
claude mcp list
```

`✔ Connected`는 MCP 서버 프로그램이 떴다는 뜻입니다. 앱(언리얼·Blender·Painter)이 꺼져 있으면 도구 호출은 실패합니다.

## 4) AssetFurnace 엔진(AI 모델) 설치

엔진마다 모델 파일을 따로 받습니다. Claude Code에 *"AssetFurnace에 pixal3d 설치해줘"* 라고 하면 크기·라이선스를 먼저 보여 주고, 승인해야 받습니다.

| 엔진 | 하는 일 | 크기 | 라이선스 |
|---|---|---|---|
| `pixal3d` | 사진 → 3D | 8.6 GB | MIT + DINOv3 License |
| `autorig` | 뼈대·스킨 웨이트 | 1.5 GB | MIT |
| `matte` | 배경 제거 | 172 MB | MIT |
| `upscaler` | Hero 얼굴 선명화 | 64 MB | BSD-3-Clause |
| `flux-image` | 글 → 그림, 뒷모습 그리기 | 8.3 GB | Apache-2.0 |
| `front-back` | 앞+뒤 그림 두 장으로 3D | 5.5 GB | MIT + DINOv3 License |

진행 상태: 스튜디오 `http://127.0.0.1:8777` 의 Setup & Status, 또는 `curl http://127.0.0.1:8777/api/setup/<엔진>/status`.
여러 파일을 동시에 받을 때 진행률이 0%로 보일 수 있습니다. 받는 폴더 크기로 확인하세요.

> 일부 모델은 국가별 라이선스 제한이 있습니다(예: Hunyuan 가중치는 EU·영국·한국에서 사용 불가). 설치 전에 반드시 확인하세요.

## 5) (선택) Blender MCP 애드온

Blender를 실시간으로 조작하려면 `mcp-for-blender` 애드온을 설치하고, 3D 뷰 **N** 키 → **MCP for Blender** 탭 → **Connect to MCP server** (기본 포트 9876).
이 저장소의 FBX 변환은 애드온 없이 백그라운드 Blender로 돌아갑니다.

## 6) (선택) Substance Painter 브리지

`substance-painter-mcp`의 브리지 플러그인을 `~/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/` 에 설치하고,
Painter **Python → Reload Plugins Folder** → **Python → Plugins** 에서 체크. 로그에 `listening on 127.0.0.1:60043` 이 나오면 연결됨.

## 7) (선택) 로컬 모델로 Claude Code 쓰기

```bash
ollama launch claude --model gemma4:12b-mlx -- --permission-mode default
```

- `--permission-mode default` 권장: 기본 `auto` 모드는 도구 실행 전 안전 판정을 같은 로컬 모델이 하다가 시간 초과가 나서 도구가 막힙니다.
- 측정 예: 12B 로컬 모델로 언리얼 레벨 조회 1회에 85초·7턴. 작은 모델에는 한 번에 한 단계씩 시키세요.
