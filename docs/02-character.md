# 1. 사진/아이디어 → 3D 캐릭터 (AssetFurnace)

AssetFurnace는 그림 → 3D 모델 → 마감(Finish) → 리깅 → 애니메이션을 한 번에 돌립니다. Claude Code에서는 `assetfurnace` MCP 도구로 조작합니다.

## 입력 고르기

| 입력 | `create` 인자 | 필요한 엔진 |
|---|---|---|
| 내 사진 | `image_path: "/abs/photo.png"` | pixal3d |
| 글 설명 | `description: "..."` | pixal3d + flux-image |
| 사진 + 내 뒷모습 사진 | `image_path` + `back_image_path` | pixal3d + front-back |

좋은 사진: 전신, 정면, 단색 배경, 팔이 몸에서 조금 떨어진 자세. 머리부터 발끝까지 잘리지 않게.

> **흔한 실수:** 사진이 있는데 글 설명만 넘기면 AssetFurnace가 그림부터 그리려고 해서, 그림 엔진이 없으면
> `This engine is not installed yet` 오류가 납니다. 사진은 꼭 `image_path`로 넘기세요.

## 만들기

예제(글 설명):

```json
{"want": "character",
 "description": "a cute cat astronaut in a silver space suit, full body, standing, plain grey background",
 "finish_detail": "high"}
```

- `want: "character"` → model → finished → rigged → animated(idle) 까지 자동
- 진행: `run_status(run_id)` (최대 50초씩 기다리며 반복)
- 결과 보기: `preview(asset_id)` (정면·3/4·측면·후면 그림), 또는 스튜디오 `http://127.0.0.1:8777/viewer/studio.html#asset=<id>`
- 결과 파일: `output/animate/<run>/<name>_rigged.glb`, `<name>_idle.glb`

## 마감 수준 `finish_detail`

| 값 | 삼각형 | 언제 |
|---|---|---|
| `game` (기본) | 2만 | 게임용 |
| `high` | 5만 | 사람·사실적 캐릭터 |
| `hero` | 몸 3.2만 + 머리 재생성 | 얼굴이 중요할 때(오래 걸림, 예: 17분) |
| `full` | 원본 전체 | 정지 렌더용, 리깅 불가 |

## 뒷모습 고치기

사진 한 장이면 뒷모습은 AI가 추측합니다(머리색이 달라지는 등). 고치는 순서:

1. 뒷모습 그림 다시 그리기 (flux-image 필요)
   ```json
   {"asset_id": "<id>", "up_to": "back", "again": true,
    "back_change": "seen from directly behind: <머리·옷 뒷면을 앞모습과 같게 구체적으로>"}
   ```
2. 그림 확인. 일부만 고치려면 `brush_back`(흰색 마스크 부분만 다시 그림), 예전 그림으로 돌리려면 `back_versions`.
3. 앞+뒤로 3D 다시 만들기 (front-back 필요): `continue_asset(<id>, up_to="model", again=True)`
4. **새 버전 id로** 이어서 마감·리깅·애니메이션: `continue_asset(<새 id>, up_to="animated", finish_detail="hero")`
   > 원래 id로 이어 가면 옛 모델에서 마감이 시작됩니다. 응답의 `newer_version` 안내를 확인하세요.

## 다른 동작

`list_moves` 로 동작 목록(idle, walk, run …)을 보고 `continue_asset(<id>, up_to="animated", move="walk")`.

## 문제가 보이면 (`options` 도구에 전체 목록)

| 증상 | 다시 마감할 때 |
|---|---|
| 머리카락에 색 얼룩, 작은 눈이 어두움 | `advanced: {"edge_fade": false}` |
| 눈이 두 개로 보이거나 미끄러짐 | `advanced: {"nudge": false}` |
| 텍스처가 흐림 | `advanced: {"texture_size": 4096}` |

한 번에 하나씩만 바꾸고 전후를 `preview`로 비교하세요.
