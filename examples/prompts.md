# Claude Code 요청 예시

예제 캐릭터는 “은색 우주복을 입은 고양이 우주비행사”입니다. 실제 사람 사진을 쓸 때는 본인 동의와 초상권을 확인하세요.

## 환경 확인

```text
언리얼 MCP로 현재 레벨 이름이랑 액터 목록만 알려줘. 아무것도 수정하지 마.
```

```text
AssetFurnace status 확인해서 설치된 엔진이랑 지금 돌고 있는 작업 알려줘.
```

## 캐릭터 만들기

```text
AssetFurnace로 캐릭터 만들어줘. 설명: "a cute cat astronaut in a silver space suit, full body, standing, plain grey background".
want=character, finish_detail=high. 다 되면 preview 보여줘.
```

```text
내 사진 ~/Pictures/me_fullbody.png 로 AssetFurnace 캐릭터 만들어줘. 사진은 image_path로 넘기고 finish_detail은 hero.
```

## 뒷모습 고치기

```text
asset <id> 뒷모습을 다시 그려줘. 앞모습과 같은 은색 우주복, 등에 산소 탱크, 꼬리는 우주복 밖으로. 그림 먼저 보여주고 괜찮으면 앞뒤로 3D 다시 만들어서 마감·리깅·idle까지.
```

## 언리얼로

```text
asset <id>의 idle GLB를 scripts/glb_to_fbx_unreal.py로 FBX로 바꾸고, scripts/ue_import_character.py로
/Game/Characters/CatAstronaut 에 import해서 키 120cm로 (0,0) 바닥에 세워줘. 4방향 캡처를 Simulate 상태로 보여줘.
```

## 재질

```text
캐릭터 슬롯 목록 보여주고, 우주복 슬롯에 금속 재질 인스턴스 만들어서 적용해줘. 원래 재질은 지우지 말고 새 이름으로.
```

## 모캡·영상

```text
AssetFurnace list_moves 보여주고 walk 동작으로 새 애니메이션 만들어서 언리얼 캐릭터에 바꿔 끼워줘.
```

```text
Level Sequence 하나 만들어서 캐릭터 idle 10초, 시네 카메라가 천천히 앞으로 다가오게 하고 Movie Render Queue로 1080x1920 PNG 렌더 설정까지 해줘.
```

## 요청 요령

- “기존 것은 덮어쓰지 말고 새 이름으로” — 실수해도 되돌리기 쉬움
- “결과를 캡처로 보여줘” — 성공 메시지 대신 눈으로 확인
- 다운로드가 필요한 단계는 Claude가 크기·라이선스를 먼저 묻습니다. 확인 후 승인하세요.
