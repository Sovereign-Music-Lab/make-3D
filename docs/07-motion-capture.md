# 6. 모션캡처 (가이드)

> 상태: 절차 정리 단계입니다. 이 저장소에서 아직 끝까지 검증하지 않았습니다. 해 보면서 이 문서를 고칩니다.

## 방법 고르기

| 방법 | 필요한 것 | 장점 | 한계 |
|---|---|---|---|
| A. AssetFurnace 동작 | 없음 (`list_moves`) | 가장 쉬움, 리그에 바로 맞음 | 정해진 동작만(idle, walk, run …) |
| B. 영상 모캡 | 휴대폰 촬영 영상 + 영상→FBX 서비스/앱 | 장비 없이 내 동작 | 손가락·발 접지 정확도 낮음, 서비스 약관 확인 |
| C. 모캡 슈트·Live Link | 슈트(Rokoko, Xsens 등) | 실시간, 정확 | 장비 비용 |
| D. 얼굴: Live Link Face | iPhone(Face ID 기종) + Live Link Face 앱 | 실시간 표정 | **캐릭터에 ARKit 52개 블렌드셰이프가 있어야 함** |

> AssetFurnace 캐릭터는 몸 리그만 있고 표정 블렌드셰이프가 없습니다. 얼굴 모캡을 하려면 MPFB(faceunits) 등으로
> 표정 셰이프가 있는 머리를 만들거나 Blender에서 셰이프 키를 추가해야 합니다.

## B/C: 몸 동작을 내 캐릭터에 입히기 (리타게팅)

1. 모캡 결과 FBX를 언리얼로 import(스켈레톤은 새로 생성).
2. **IK Rig** 두 개 만들기: 모캡 스켈레톤용, 내 캐릭터 스켈레톤용. 각각 Pelvis/Spine/Head/팔/다리 체인 지정, Retarget Root = 골반.
3. **IK Retargeter**: 소스=모캡 IK Rig, 타깃=캐릭터 IK Rig. 두 자세가 다르면(A포즈/T포즈) Retarget Pose를 맞춤.
4. 애니메이션 내보내기(Export Selected Animations) → 캐릭터용 AnimSequence 생성.
5. `ue_import_character.py`로 배치한 액터의 `AnimationData.animToPlay`를 새 애니로 바꾸고 `ue_capture.py --simulate`로 확인.
6. 점검: 발 미끄러짐, 발이 바닥을 뚫는지, 치마·머리카락이 몸을 뚫는지.

## D: 얼굴 (Live Link Face)

1. 프로젝트 플러그인: **Live Link**, **Apple ARKit Face Support**.
2. iPhone과 Mac을 같은 네트워크에 두고, Live Link Face 앱 설정에서 Mac의 IP 입력.
3. 언리얼 **Window → Virtual Production → Live Link** 에 iPhone 소스가 보이면 연결됨.
4. 캐릭터 Animation Blueprint에 **Live Link Pose** 노드, 표정 이름을 ARKit 52개와 맞춤.

## 녹화

- **Take Recorder**(Takes 플러그인)로 Live Link 입력을 Level Sequence/애니메이션으로 저장.
- 녹화본을 Sequencer에서 다듬어 [영상 만들기](08-video.md)로.
