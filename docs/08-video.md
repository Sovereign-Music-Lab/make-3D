# 7. 영상 만들기 (가이드)

> 상태: 절차 정리 단계입니다. 이 저장소에서 아직 끝까지 검증하지 않았습니다.

## 1) Level Sequence 만들기

1. Content Browser → **Add → Cinematics → Level Sequence**.
2. 캐릭터 액터를 Sequencer에 추가 → **Animation** 트랙에 AnimSequence(idle, 모캡 결과) 배치.
3. **Cine Camera Actor** 추가 → 카메라 컷 트랙. 초점 거리 35–85 mm, 초점은 캐릭터 눈에(Look at Tracking 또는 Focus 설정).
4. 조명 키프레임, 카메라 이동(돌리·크레인) 등.

## 2) 렌더: Movie Render Queue

프로젝트 플러그인 **Movie Render Queue** 필요.

1. **Window → Cinematics → Movie Render Queue** → Level Sequence 추가.
2. 설정 권장:
   - Output: PNG 시퀀스(또는 EXR), 해상도 1920×1080, 쇼츠면 1080×1920
   - Anti-aliasing: Spatial 1, Temporal 8 이상(머리카락·디더 투명이 깔끔해짐), Warm Up 프레임 32
   - Console Variables: `r.MotionBlurQuality 4` 등 필요 시
3. Render (Local).

> 정지 캡처에서 보이던 디더 투명 줄무늬는 Temporal 샘플이 쌓이면 대부분 사라집니다.

## 3) mp4로 합치기 (ffmpeg)

```bash
ffmpeg -framerate 30 -i renders/shot.%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 shot.mp4
```

음악/목소리 합치기:

```bash
ffmpeg -i shot.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4
```

## 4) 점검

- 프레임 누락·깜빡임, 머리카락·옷 뚫림, 발 미끄러짐
- 첫 프레임 노출 튐(Warm Up 부족), 색이 바랜 느낌(톤매핑/sRGB 출력 확인)
