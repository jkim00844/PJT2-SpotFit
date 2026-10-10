# PJT2-SpotFit

> 서울시 상권 소비 예측 및 금융 MBTI 기반 창업 상권 추천 프로젝트 (1조 KLPF)

서울 25개 자치구 · 425개 행정동의 인구·인프라·금융 데이터를 결합하여 **기대 소비 대비 실제 소비의 차이(소비 갭)**를 분석하고, 소비 잠재력과 틈새 상권을 탐색하는 통합 프로젝트 저장소입니다.

사용자의 금융 성향(금융 MBTI), 창업 예산, 위험 감수 성향을 상권 분석 결과와 결합하여 개인에게 적합한 창업 상권을 추천하고, 데이터에 기반한 창업 의사결정을 지원합니다.

## 데이터

- 원천 데이터 출처: [RAW_DATA_SOURCES.md](RAW_DATA_SOURCES.md)
- 2025년 원천 데이터 안내 (받는 방법, 파일별 기간, 주의할 점): [data/README.md](data/README.md)
- 데이터 수집 스크립트: [scripts/fetch_raw_2025.py](scripts/fetch_raw_2025.py)

```bash
git clone <이 저장소 주소>
cd PJT2-SpotFit
python scripts/fetch_raw_2025.py --only sbiz   # 저장소에 없는 소상공인 상가정보(278MB)만 추가로 받기
```
