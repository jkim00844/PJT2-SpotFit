# 📚 프로젝트 원천 데이터(Raw Data) 출처 및 명세서

> **프로젝트**: 서울시 상권 소비 예측 및 소비 잠재력 상권 분석 (1조 KLPF)  
> **최종 수정일**: 2026-10-10  
> **문서 목적**: 프로젝트에 사용된 모든 원천 데이터(Raw Data)의 공식 출처, 수집 URL, 파일명, 수집 방법 및 자동화 스크립트를 체계적으로 정리하여 팀원 및 재현 연구자에게 제공합니다.

---

## 📑 목차
1. [전체 데이터셋 요약표](#1-전체-데이터셋-요약표)
2. [서울 열린데이터광장 (서울시 공공데이터)](#2-서울-열린데이터광장)
   - 2.1 [서울시 상권분석서비스 (행정동 단위)](#21-서울시-상권분석서비스-행정동-단위)
   - 2.2 [서울시 상권분석서비스 (상권 단위)](#22-서울시-상권분석서비스-상권-단위)
   - 2.3 [서울 시민생활 데이터 (서울시 × SKT 가명결합)](#23-서울-시민생활-데이터-서울시--skt-가명결합)
   - 2.4 [서울 체류인구 데이터](#24-서울-체류인구-데이터)
3. [공공데이터포털 (data.go.kr)](#3-공공데이터포털)
   - 3.1 [소상공인시장진흥공단 상가(상권)정보](#31-소상공인시장진흥공단-상가상권정보)
   - 3.2 [국민연금공단 평균소득월액](#32-국민연금공단-평균소득월액)
4. [통계청 MDIS (마이크로데이터)](#4-통계청-mdis-마이크로데이터)
   - 4.1 [가계금융복지조사 마스터](#41-가계금융복지조사-마스터)
5. [서울시 빅데이터캠퍼스](#5-서울시-빅데이터캠퍼스)
6. [공간 지리정보 (GeoJSON Boundary)](#6-공간-지리정보)
7. [네이버 데이터랩 (검색 트렌드)](#7-네이버-데이터랩)
8. [데이터 자동 수집 및 재구축 파이프라인 스크립트](#8-데이터-자동-수집-및-재구축-스크립트)

---

## 1. 전체 데이터셋 요약표

| 대분류 | 데이터셋 명칭 | 주요 파일명 | 출처 기관 | 공식 제공 URL | 자동 수집 스크립트 |
|:---|:---|:---|:---|:---|:---|
| **상권분석 (행정동)** | 서울시 상권분석서비스(행정동 10종) | `OA-22160` ~ `OA-22184_*.csv` | 서울특별시 | [서울열린데이터광장](https://data.seoul.go.kr) | `scripts/fetch_seoul_open_data.sh` |
| **상권분석 (골목상권)** | 서울시 상권분석서비스(상권 8종) | `OA-15560` ~ `OA-15584_*.csv` | 서울특별시 | [서울열린데이터광장](https://data.seoul.go.kr) | `scripts/fetch_seoul_trade_area.sh` |
| **생활데이터 (가명결합)** | 행정동단위 통신정보 & 관심집단수 | `living/통신정보_*`, `관심집단_*` | 서울시 × SK텔레콤 | [서울열린데이터광장](https://data.seoul.go.kr) | `scripts/fetch_living_data.sh` |
| **체류인구** | 서울 체류인구(250m 내국인) | `체류인구_내국인_250m_*.zip` | 서울특별시 | [서울열린데이터광장](https://data.seoul.go.kr) | 수동 다운로드 |
| **상가정보** | 소상공인 상가(상권)정보 | `소상공인_상가정보_서울.csv` | 소상공인시장진흥공단 | [공공데이터포털](https://www.data.go.kr) | `scripts/download_sbiz_data.py` |
| **소득지표** | 자격 시군구신고 평균소득월액 | `국민연금_시군구_평균소득월액_*.csv` | 국민연금공단 | [공공데이터포털](https://www.data.go.kr) | 수동 다운로드 |
| **가계금융** | 가계금융복지조사(가구/가구원) | `2023~2025_가구마스터/가구원_*.csv` | 통계청·한은·금감원 | [통계청 MDIS](https://mdis.kostat.go.kr) | 수동 추출 (승인/공공용) |
| **공간경계** | 서울 행정동 공간 경계 GeoJSON | `HangJeongDong_ver20251231.geojson` | 통계청 SGIS / VWorld | [VWorld / SGIS](https://www.vworld.kr) | `dashboard/scripts/build_data.py` |
| **검색트렌드** | 25개 자치구별 검색어 트렌드 | `네이버_검색키워드_매핑.md` | 네이버 (Naver) | [Naver DataLab API](https://datalab.naver.com) | `dashboard/src/naver_data.py` |

---

## 2. 서울 열린데이터광장

### 2.1 서울시 상권분석서비스 (행정동 단위)
- **저장 위치**: `data/raw/` 및 `data/raw/KLPF_data/`
- **인증키 필요 여부**: 불필요 (공개 다운로드 가능)
- **자동 수집 스크립트**: `scripts/fetch_seoul_open_data.sh`

| 파일명 | 데이터셋 명칭 | 기준 단위 | 공식 URL |
|:---|:---|:---|:---|
| `OA-22160_영역_행정동.csv` | 서울시 상권분석서비스(영역-행정동) | 행정동 영역 코드 매핑 | [상세보기](https://data.seoul.go.kr/dataList/OA-22160/S/1/datasetView.do) |
| `OA-22163_아파트_행정동.csv` | 서울시 상권분석서비스(아파트-행정동) | 아파트 단지·가구수 | [상세보기](https://data.seoul.go.kr/dataList/OA-22163/S/1/datasetView.do) |
| `OA-22164_아파트_자치구.csv` | 서울시 상권분석서비스(아파트-자치구) | 자치구별 아파트 현황 | [상세보기](https://data.seoul.go.kr/dataList/OA-22164/S/1/datasetView.do) |
| `OA-22166_소비_행정동.csv` | 서울시 상권분석서비스(소비-행정동) | 행정동 분기별 추정 소비 | [상세보기](https://data.seoul.go.kr/dataList/OA-22166/S/1/datasetView.do) |
| `OA-22167_소비_자치구.csv` | 서울시 상권분석서비스(소비-자치구) | 자치구 분기별 추정 소비 | [상세보기](https://data.seoul.go.kr/dataList/OA-22167/S/1/datasetView.do) |
| `OA-22169_집객시설_행정동.csv` | 서울시 상권분석서비스(집객시설-행정동) | 관공서·은행·병원 등 | [상세보기](https://data.seoul.go.kr/dataList/OA-22169/S/1/datasetView.do) |
| `OA-22178_길단위인구_행정동.csv` | 서울시 상권분석서비스(길단위인구-행정동) | 유동인구 및 보행량 | [상세보기](https://data.seoul.go.kr/dataList/OA-22178/S/1/datasetView.do) |
| `OA-22182_상주인구_자치구.csv` | 서울시 상권분석서비스(상주인구-자치구) | 자치구 거주 인구수 | [상세보기](https://data.seoul.go.kr/dataList/OA-22182/S/1/datasetView.do) |
| `OA-22183_상주인구_행정동.csv` | 서울시 상권분석서비스(상주인구-행정동) | 행정동 거주 인구수 | [상세보기](https://data.seoul.go.kr/dataList/OA-22183/S/1/datasetView.do) |
| `OA-22184_직장인구_행정동.csv` | 서울시 상권분석서비스(직장인구-행정동) | 직장인(근무자) 인구 | [상세보기](https://data.seoul.go.kr/dataList/OA-22184/S/1/datasetView.do) |

---

### 2.2 서울시 상권분석서비스 (상권 단위)
- **저장 위치**: `data/raw/상권/`
- **인증키 필요 여부**: 불필요
- **자동 수집 스크립트**: `scripts/fetch_seoul_trade_area.sh`
- **특이사항**: 서울시 골목상권/발달상권 등 1,650개 개별 상권 단위 세부 지표로, 연도별 시트 및 zip 파일(CP949 인코딩)로 구성됩니다.

| 파일명 | 데이터셋 명칭 | 데이터 기간 | 공식 URL |
|:---|:---|:---|:---|
| `OA-15560_영역_상권.csv` | 서울시 상권분석서비스(영역-상권) | 1,650개 상권 영역 | [상세보기](https://data.seoul.go.kr/dataList/OA-15560/S/1/datasetView.do) |
| `OA-15568_길단위인구_상권.csv` | 서울시 상권분석서비스(길단위인구-상권) | 2021Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15568/S/1/datasetView.do) |
| `OA-15569_직장인구_상권.csv` | 서울시 상권분석서비스(직장인구-상권) | 2021Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15569/S/1/datasetView.do) |
| `OA-15572_추정매출_상권.csv` | 서울시 상권분석서비스(추정매출-상권) | 2025Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15572/S/1/datasetView.do) |
| `추정매출_상권_2023.zip` / `2024.zip` | 〃 (연도별 전체 데이터) | 2023, 2024 전체 | [상세보기](https://data.seoul.go.kr/dataList/OA-15572/S/1/datasetView.do) |
| `OA-15576_상권변화지표_상권.csv` | 서울시 상권분석서비스(상권변화지표-상권) | 2021Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15576/S/1/datasetView.do) |
| `OA-15577_점포_상권.csv` | 서울시 상권분석서비스(점포-상권) | 2025Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15577/S/1/datasetView.do) |
| `점포_상권_2023.zip` / `2024.zip` | 〃 (연도별 전체 데이터) | 2023, 2024 전체 | [상세보기](https://data.seoul.go.kr/dataList/OA-15577/S/1/datasetView.do) |
| `OA-15580_집객시설_상권.csv` | 서울시 상권분석서비스(집객시설-상권) | 2021Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15580/S/1/datasetView.do) |
| `OA-15584_상주인구_상권.csv` | 서울시 상권분석서비스(상주인구-상권) | 2021Q1 ~ 2026Q2 | [상세보기](https://data.seoul.go.kr/dataList/OA-15584/S/1/datasetView.do) |

---

### 2.3 서울 시민생활 데이터 (서울시 × SKT 가명결합)
- **저장 위치**: `data/raw/living/`
- **데이터 성격**: 서울시와 SK텔레콤이 공동 개발한 가명결합 빅데이터로, 425개 행정동별 통신/라이프스타일 지표를 수록합니다.
- **수집 주기**: 분기말 월(3·6·9·12월) 기준 수집
- **자동 수집 스크립트**: `scripts/fetch_living_data.sh`

| 파일명 | 데이터셋 명칭 | 주요 수록 변수 | 공식 URL |
|:---|:---|:---|:---|
| `통신정보_2023_전체.zip`<br>`통신정보_2024.03~2025.12.xlsx` | 행정동단위 29개 통신정보 (`OA-22267`) | 1인 가구 비율, 통화량, 데이터 사용량, 배달앱 사용도, 외출 일수 등 | [상세보기](https://data.seoul.go.kr/dataList/OA-22267/F/1/datasetView.do) |
| `관심집단_2023_전체.zip`<br>`관심집단_2024.03~2025.12.xlsx` | 행정동단위 10개 관심집단수 (`OA-22266`) | 직장인, 소상공인, 육아/가족, 실버, 1인 생활자 등 관심군 인구수 | [상세보기](https://data.seoul.go.kr/dataList/OA-22266/F/1/datasetView.do) |

---

### 2.4 서울 체류인구 데이터
- **저장 위치**: `data/raw/상권/체류인구_내국인_250m_20260911.zip`
- **데이터셋 명칭**: [내국인] 서울 체류인구(250m) (`OA-22892`)
- **공식 URL**: <https://data.seoul.go.kr/dataList/OA-22892/F/1/datasetView.do>
- **설명**: 250m 격자 단위로 집계된 내국인 실시간 체류인구 데이터 샘플

---

## 3. 공공데이터포털

### 3.1 소상공인시장진흥공단 상가(상권)정보
- **저장 위치**: `data/raw/소상공인_상가정보_서울.csv` (약 288MB, 대용량 파일로 로컬 생성)
- **제공 기관**: 소상공인시장진흥공단
- **공식 데이터셋 URL**: <https://www.data.go.kr/data/15083033/fileData.do>
- **자동 다운로드 스크립트**: [`scripts/download_sbiz_data.py`](file:///e:/패스트캠퍼스/ICB13-2_20260907/T_PJT2/scripts/download_sbiz_data.py)
  ```bash
  python scripts/download_sbiz_data.py
  ```
- **데이터 내용**: 전국 상가업소 정보 중 서울특별시 소재 업종별 점포(음식, 소매, 생활서비스 등)의 상호명, 표준산업분류코드, 도로명주소, 좌표(경도/위도) 수록

### 3.2 국민연금공단 평균소득월액
- **저장 위치**: `data/raw/국민연금_시군구_평균소득월액_2020-2024.csv`
- **제공 기관**: 국민연금공단
- **공식 데이터셋 URL**: <https://www.data.go.kr/data/3046077/fileData.do>
- **데이터 내용**: 전국 시·군·구 단위 가입자의 사업장/지역 평균 소득월액 및 등급 분포

---

## 4. 통계청 MDIS (마이크로데이터)

### 4.1 가계금융복지조사 마스터
- **저장 위치**: `수집데이터/`
- **제공 기관**: 통계청 · 한국은행 · 금융감독원
- **공식 포털**: [통계청 MDIS (MicroData Integrated Service)](https://mdis.kostat.go.kr)
- **수록 파일 목록**:
  - `2023_가구마스터_20260912_34949.csv` / `2023_가구원_20260912_61908.csv`
  - `2024_가구마스터_20260912_34949.csv` / `2024_가구원_20260912_61908.csv`
  - `2025_가구마스터_20260912_34949.csv` / `2025_가구원_20260912_61908.csv`
  - `파일설계서(공공용)_가계금융복지조사_가구마스터/가구원.xlsx`
- **데이터 내용**: 대한민국 대표 표본 가구의 소득(근로·사업·재산), 지출(식비·주거·교육·의료 등 12개 비목), 자산(부동산·금융), 부채(담보대출·신용대출·DSR) 초정밀 마이크로 서베이 데이터
- **활용 가이드 문서**: [`가계금융복지조사_데이터_EDA_및_분석가이드.md`](file:///e:/패스트캠퍼스/ICB13-2_20260907/T_PJT2/가계금융복지조사_데이터_EDA_및_분석가이드.md)

---

## 5. 서울시 빅데이터캠퍼스 (재현데이터)

- **저장 위치**: `data/raw/seoul_lifestyle_*.csv`
- **제공 기관**: 서울시 빅데이터캠퍼스 (<https://bigdata.seoul.go.kr>)
- **수록 파일**:
  - `seoul_lifestyle_금융생활_재현데이터_sample1000.csv`
  - `seoul_lifestyle_소비이동패턴_재현데이터_sample1000.csv`
- **특이사항**: 개인정보 보호를 위해 실제 데이터의 통계적 분포를 모사한 합성(재현) 데이터 샘플로, 컬럼 스키마 및 소비 이동 패턴 참조용으로 활용

---

## 6. 공간 지리정보 (GeoJSON Boundary)

- **저장 위치**: `dashboard/data/cache/HangJeongDong_ver20251231.geojson` (스크립트 자동 캐싱)
- **출처**: 대한민국 통계지리정보서비스(SGIS) 및 VWorld 국가공간정보포털
- **가공 스크립트**: [`dashboard/scripts/build_data.py`](file:///e:/패스트캠퍼스/ICB13-2_20260907/T_PJT2/dashboard/scripts/build_data.py)
- **용도**: 서울시 25개 자치구 및 425개 행정동 다각형 경계선 Folium/Choropleth 지도 렌더링

---

## 7. 네이버 데이터랩 (검색 트렌드)

- **출처**: [NAVER DataLab 통합 검색어 트렌드 API](https://datalab.naver.com)
- **관련 문서**: 
  - [`서울시_25개_자치구_네이버_검색키워드_매핑.md`](file:///e:/패스트캠퍼스/ICB13-2_20260907/T_PJT2/서울시_25개_자치구_네이버_검색키워드_매핑.md)
  - [`네이버_검색트렌드_온오프라인_소비결합_분석보고서.md`](file:///e:/패스트캠퍼스/ICB13-2_20260907/T_PJT2/네이버_검색트렌드_온오프라인_소비결합_분석보고서.md)
- **용도**: 각 자치구별 외식/상권 키워드 검색량과 오프라인 카드 소비액 간의 선행/동행 상관성 분석

---

## 8. 데이터 자동 수집 및 재구축 스크립트

저장소 내 `scripts/` 폴더에 위치한 아래 쉘/파이썬 스크립트를 실행하여 원천 데이터를 언제든 자동으로 재수집할 수 있습니다:

```bash
# 1. 서울 열린데이터광장 행정동 단위 데이터 일괄 수집
bash scripts/fetch_seoul_open_data.sh

# 2. 서울 시민생활(SKT 통신/관심집단) 가명결합 데이터 수집
bash scripts/fetch_living_data.sh

# 3. 서울 상권 단위(골목상권 추정매출/점포 등) 데이터 수집
bash scripts/fetch_seoul_trade_area.sh

# 4. 소상공인진흥공단 서울 상가정보 자동 다운로드 및 압축 해제
python scripts/download_sbiz_data.py

# 5. 수집된 원천 데이터를 결합하여 분석 패널 및 MBTI 피처 생성
python scripts/build_features.py
python scripts/cluster_mbti.py
```
