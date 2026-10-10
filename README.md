# PJT2-SpotFit

서울시 상권 소비 예측 및 소비 잠재력 상권 분석 (1조 KLPF)

- 원천 데이터 출처: [RAW_DATA_SOURCES.md](RAW_DATA_SOURCES.md)
- 2025년 원천 데이터 안내 (받는 방법, 파일별 기간, 주의할 점): [data/README.md](data/README.md)
- 데이터 수집 스크립트: [scripts/fetch_raw_2025.py](scripts/fetch_raw_2025.py)

```bash
git clone <이 저장소 주소>
cd PJT2-SpotFit
python scripts/fetch_raw_2025.py --only sbiz   # 저장소에 없는 소상공인 상가정보(278MB)만 추가로 받기
```
