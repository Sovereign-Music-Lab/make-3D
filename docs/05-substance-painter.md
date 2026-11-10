# 4. Substance 3D Painter: 텍스처 마무리 (가이드)

> 상태: 절차 정리 단계입니다. 이 저장소에서 아직 끝까지 자동화·검증하지 않았습니다.

AssetFurnace 결과는 그림 색이 입혀진 텍스처 한 장이라, 반사·거칠기·요철 정보가 약하고 가려졌던 부분에 얼룩이 남기도 합니다.
형태는 그대로 두고 텍스처만 바꾸므로 **리깅과 애니메이션은 그대로** 씁니다.

## 언제 하나

- **뒷모습 재생성·형태 수정이 끝난 뒤.** 3D를 다시 만들면 UV(텍스처 좌표)가 바뀌어 Painter 작업이 무효가 됩니다.

## 순서

1. 리깅된 모델 FBX 준비(`docs/03-blender.md`의 변환 결과).
2. Painter 실행, 브리지 플러그인 켜기(`listening on 127.0.0.1:60043` 확인).
3. Claude Code에 요청 예:
   ```text
   Substance Painter로 ./char.fbx 새 프로젝트 만들어줘(텍스처 4096, OpenGL 노멀). 기존 베이스 컬러 텍스처를 Fill 레이어로 불러오고, 베이크(AO·곡률·두께)까지 해줘.
   ```
   사용 도구: `painter_create_project`, `painter_import_resource`, `painter_bake`, `painter_insert_layer`, `painter_set_fill_source`, `painter_screenshot`.
4. 레이어 작업
   - 얼룩 정리: 클론/페인트 레이어로 덮기
   - 시퀸·반짝이: 자동 UV가 잘게 조각나 있으므로 **triplanar 투영**으로 노멀·금속 패턴
   - 피부: 거칠기 0.45–0.6, 약한 SSS용 두께 맵
   - 머리카락: 결 방향 노멀, 거칠기 0.3–0.4
5. 내보내기: **Unreal Engine 4 (Packed)** 계열 프리셋(BaseColor, Normal, OcclusionRoughnessMetallic). `painter_export_textures`.
6. 언리얼: 텍스처 import(노멀은 sRGB 끄기), 기존 재질에 연결하거나 새 재질 인스턴스 → 슬롯 지정 → `ue_capture.py`로 전후 비교.

## 주의

- Painter 프로젝트(.spp)와 텍스처는 용량이 커서 git에 올리지 않습니다(`.gitignore`).
- 노멀 맵 방향: Painter는 OpenGL/DirectX 선택. 언리얼은 DirectX 기준이므로 OpenGL이면 G 채널 뒤집기.
