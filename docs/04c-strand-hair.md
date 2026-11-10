# 3-3. 가닥 헤어 (Groom)

AssetFurnace가 만든 머리는 겉껍데기 메시라서, 가까이서 보면 플라스틱처럼 보입니다. 이 단계에서는 그 메시 위에 진짜 가닥(strand)을 심고, 언리얼의 Groom 기능으로 렌더링합니다.

흐름: **Blender에서 가닥 만들기(.abc) → 언리얼 Groom import → 굵기·바인딩 → 캐릭터에 붙이기 → Hair 재질**

## 0. 준비 (한 번만)

### 플러그인
언리얼 `.uproject`에서 아래 두 플러그인을 켜고 에디터를 재시작합니다.
```json
{"Name": "HairStrands", "Enabled": true},
{"Name": "AlembicHairImporter", "Enabled": true}
```
그리고 Project Settings → Rendering → **Support Compute Skin Cache**를 켭니다(바인딩된 헤어가 움직이는 메시를 따라가려면 필요).

### Python 원격 실행
Groom import는 언리얼 MCP 도구에 없어서, 에디터 안에서 Python을 돌립니다. `Config/DefaultEngine.ini`에 아래를 넣고 재시작합니다.
```ini
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bRemoteExecution=True
RemoteExecutionMulticastGroupEndpoint=239.0.0.1:6766
RemoteExecutionMulticastBindAddress=127.0.0.1
RemoteExecutionMulticastTtl=0
```
연결 확인:
```bash
python3 scripts/ue_python.py -c "import unreal; print(unreal.SystemLibrary.get_engine_version())"
```
- macOS에서는 127.0.0.1에 묶인 소켓이 멀티캐스트를 못 받습니다. `ue_python.py`가 루프백 멤버십 + 유니캐스트로 우회하니, 에디터 쪽을 `0.0.0.0`으로 바꾸지 마세요(같은 네트워크의 다른 기기에 열립니다).
- 엔진 위치가 다르면 `UE_ROOT` 환경변수를 설정하세요.

## 1. Blender: 머리 메시에서 가닥 만들기
부위 분리(3-2) 결과 중 `AF_Hair*` 재질 면 위에 가닥을 심고, 표면을 따라 아래로 흘러내리게 만든 뒤 Alembic으로 내보냅니다.
```bash
blender -b --factory-startup -P scripts/strands_from_hair_mesh.py -- my_char_parts.glb my_char_hair.abc \
    --count 40000 --length 0.07 --points 12 --wave 0.004 --scale 100
```
- `--count` 가닥 수, `--length` 길이(m), `--points` 가닥당 점 수, `--scale 100` 언리얼 cm 단위.
- 처음엔 `--count 5000`으로 빨리 확인한 뒤 늘리세요.

## 2. 언리얼: Groom import
```bash
python3 scripts/ue_python.py scripts/ue_import_groom.py my_char_hair.abc \
    /Game/MyChar Groom_MyChar_Hair /Game/MyChar/SK_MyChar 0.012 90 -1
```
- UE 5.8에서는 옛 `GroomFactory`가 형식을 안 받아서, 스크립트가 `Interchange.FeatureFlags.Import.ABC 1`을 켠 뒤 import합니다.
- 이미 같은 이름이 있으면 덮어쓰지 않고 멈춥니다.
- `90 -1`은 Blender(Y-up)를 언리얼(Z-up)로 돌리는 회전·뒤집기입니다. 머리가 눕거나 거울처럼 보이면 이 값을 바꿔 보세요.

## 3. 굵기 + 바인딩
import는 됐는데 설정·바인딩이 안 됐다면(중간에 끊긴 경우 등) 따로 실행합니다.
```bash
python3 scripts/ue_python.py scripts/ue_groom_setup.py \
    /Game/MyChar/Groom_MyChar_Hair /Game/MyChar/SK_MyChar 0.012 0
```
- 굵기 0.012 cm, 뿌리 1.0 / 끝 0.2로 가늘어지게.
- 바인딩 `GB_<groom 이름>`을 만듭니다(있으면 그대로 둠).
- 마지막 `0` = 물리 끔. **아래 주의 참고.**

## 4. 캐릭터에 붙이기 + 재질
```bash
python3 scripts/ue_python.py scripts/ue_hair_material.py /Game/MyChar M_MyChar_Hair 0.035 0.02 0.012
python3 scripts/ue_python.py scripts/ue_attach_groom_py.py MyCharActor \
    /Game/MyChar/Groom_MyChar_Hair /Game/MyChar/GB_Groom_MyChar_Hair /Game/MyChar/M_MyChar_Hair Groom_Hair
```
- 재질: Hair 셰이딩 모델 + Used with Hair Strands. 색은 선형 RGB(짙은 갈색 예시). `HairColor`, `Roughness`, `Scatter`, `Specular` 파라미터로 나중에 조절.
- GroomComponent를 캐릭터의 SkeletalMeshComponent 아래에 붙여서 애니메이션을 따라갑니다. 레벨도 저장합니다.
- MCP 버전(`ue_attach_groom.py`)도 있지만, 레벨을 연 직후엔 MCP가 멈출 때가 있어 Python 버전을 권장합니다.

## 5. 확인
```bash
python3 scripts/ue_python.py scripts/ue_shot_py.py out/hair_front.png 0 110 160 -6 -90
```
- 한 번에 한 장씩 찍고, 파일이 생긴 걸 확인한 뒤 다음 장을 찍으세요(요청이 겹치면 마지막 것만 저장됨).
- 정면·옆·뒤·얼굴 클로즈업을 같은 카메라로 전후 비교하세요.

## 주의
- **물리를 Python으로 켜고 저장하면 에디터가 꺼집니다**(UE 5.8.4, Interchange로 들여온 groom). 썸네일을 그릴 때 보간 데이터가 없어 assert(`GroomResources.cpp` `DataFlags_HasData`)가 납니다. 물리는 Groom 에디터 화면에서 직접 켜고, 저장 전에 한 번 확인하세요.
- 가닥 아래 원래 머리 메시가 목·어깨 쪽에서 삐져나오면 그 부분을 따로 숨기거나 메시 머리 재질을 어둡게 하세요.
- 가닥이 메시 껍데기를 그대로 따라가서 털가죽처럼 보이면 `--length`를 늘리고 `--wave`를 조금 키우세요.
