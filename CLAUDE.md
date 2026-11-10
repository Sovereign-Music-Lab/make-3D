# make-3D — Claude Code 작업 규칙

사용자에게 답할 때는 한국어로, 짧고 쉽게. 코드·경로·도구 이름은 원문 그대로.

## 도구 순서
- 언리얼: `list_toolsets` → 필요한 툴셋 하나만 `describe_toolset` → `call_tool`. 스키마를 추측하지 않는다. `tool_name`은 짧은 이름.
- AssetFurnace: `status` → `create`/`continue_asset` → `run_status` 반복 → `preview`로 결과를 사용자에게 보여 준다.
- 스크립트: `scripts/` 의 CLI를 우선 쓰고, 없을 때만 `scripts/ue_mcp.py`로 직접 호출한다.

## 안전
- 기존 레벨·에셋·파일을 덮어쓰지 않는다. 새 폴더·새 이름(`_v2` 등)으로 만든다.
- 모델 파일 다운로드, 유료 생성, 외부 업로드, 삭제는 사용자 승인 후에만. 다운로드는 이름·크기·라이선스를 먼저 알린다.
- 실존 인물 캐릭터는 본인 동의를 확인한다.

## 검증
- 바뀔 때마다 `scripts/ue_capture.py`로 같은 카메라 전후를 캡처해서 확인한다. 도구 성공 ≠ 외형 완성.
- 저장 후 재로드, 애니메이션(Simulate), 크기·바닥, 관절 변형은 따로 확인하고, 안 한 것은 안 했다고 말한다.

## 이 저장소에 올리지 않는 것
- 모델 파일(.gguf, .safetensors), 3D·언리얼 결과물(.glb, .fbx, .uasset, .umap, .blend, .spp), 개인 사진, 개인 경로.
