#!/usr/bin/env python3
"""SpotFit 원천 데이터(Raw Data) 2025년분 일괄 수집

RAW_DATA_SOURCES.md 의 공개 데이터를 2025년 범위(2025Q1~Q4 / 2025-12-31 기준)로만 받아
data/raw/ 에 저장한다. 표준 라이브러리만 쓰므로 pip 설치 없이 Windows·macOS 에서 실행된다.

사용법:
  python scripts/fetch_raw_2025.py                     # 전체 (체류인구 제외)
  python scripts/fetch_raw_2025.py --only dong trade   # 일부만
  python scripts/fetch_raw_2025.py --stay 2512         # 체류인구 2025-12 월 파일(약 470MB) 추가
  python scripts/fetch_raw_2025.py --naver-key config/naver_api_key.json
  python scripts/fetch_raw_2025.py --force             # 이미 받은 파일도 다시 받기

자동화 불가(수동): 통계청 MDIS 가계금융복지조사, 서울시 빅데이터캠퍼스 재현데이터
"""
import argparse
import codecs
import csv
import http.cookiejar
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

YEAR = "2025"
ROOT = Path(__file__).resolve().parents[1]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
QUARTER_COL = "기준_년분기_코드"

# ── 서울 열린데이터광장 (인증키 불필요) ──────────────────────────────────
SHEET_EP = "https://datafile.seoul.go.kr/bigfile/iot/sheet/csv/download.do"
FILE_EP = "https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false"

DONG = [  # 상권분석서비스 — 행정동 / 자치구 단위
    ("OA-22160", "영역_행정동"),       # 기간 없음 → 전체 유지
    ("OA-22163", "아파트_행정동"),
    ("OA-22164", "아파트_자치구"),
    ("OA-22166", "소비_행정동"),
    ("OA-22167", "소비_자치구"),
    ("OA-22169", "집객시설_행정동"),
    ("OA-22178", "길단위인구_행정동"),
    ("OA-22182", "상주인구_자치구"),
    ("OA-22183", "상주인구_행정동"),
    ("OA-22184", "직장인구_행정동"),
]
TRADE = [  # 상권분석서비스 — 상권(골목·발달·전통시장·관광특구) 단위
    ("OA-15560", "영역_상권"),         # 기간 없음 → 전체 유지
    ("OA-15568", "길단위인구_상권"),
    ("OA-15569", "직장인구_상권"),
    ("OA-15572", "추정매출_상권"),
    ("OA-15576", "상권변화지표_상권"),
    ("OA-15577", "점포_상권"),
    ("OA-15580", "집객시설_상권"),
    ("OA-15584", "상주인구_상권"),
]
# 생활데이터(서울시×SKT 가명결합): 분기 패널에 맞춰 분기말 월만.
# seq = 데이터셋 페이지 downloadFile('seq') 값 (2026-10-10 확인)
LIVING = [
    ("OA-22267", "통신정보", {"03": 20, "06": 23, "09": 26, "12": 29}),
    ("OA-22266", "관심집단", {"03": 21, "06": 24, "09": 27, "12": 30}),
]
STAY_ID = "OA-22892"  # 체류인구(250m, 내국인) — 2025년은 월 단위 zip, seq = YYMM

# ── 공공데이터포털 ──────────────────────────────────────────────────────
# 과거판 atchFileId 는 '주기성 과거 데이터' 팝업(selectDpkDetailInfo.do)에서 확인 (2026-10-10)
DG_DOWN = "https://www.data.go.kr/cmm/cmm/fileDownload.do"
SBIZ = {"page": "https://www.data.go.kr/data/15083033/fileData.do",
        "atch": "FILE_000000003676618",
        "name": "소상공인시장진흥공단_상가(상권)정보_20251231"}
NPS = {"page": "https://www.data.go.kr/data/3046077/fileData.do",
       "atch": "FILE_000000007701446",
       "name": "국민연금공단_자격 시구신고 평균소득월액_20251231"}

# ── 행정동 경계 (vuski/admdongkor, 통계청 SGIS 기반) ─────────────────────
GEO_VERSION = "ver20251231"
GEO_URL = (f"https://raw.githubusercontent.com/vuski/admdongkor/master/"
           f"{GEO_VERSION}/HangJeongDong_{GEO_VERSION}.geojson")

# ── 네이버 데이터랩 검색어 트렌드 (NAVER API HUB, 키 필요) ────────────────
NAVER_URL = "https://naverapihub.apigw.ntruss.com/search-trend/v1/search"
NAVER_CATEGORY = [  # 10대 소비 카테고리 (요청당 최대 5그룹)
    [
        {"groupName": "음식", "keywords": ["맛집", "카페", "배달음식", "식당", "외식", "고기집"]},
        {"groupName": "여가_문화", "keywords": ["전시회", "영화관", "호캉스", "팝업스토어", "콘서트", "미술관"]},
        {"groupName": "의료비", "keywords": ["피부과", "치과", "안과", "성형외과", "건강검진", "정형외과"]},
        {"groupName": "교육", "keywords": ["학원", "스터디카페", "독서실", "과외", "인강", "입시"]},
        {"groupName": "의류_신발", "keywords": ["옷 쇼핑", "아울렛", "쇼핑몰", "신발", "패션", "백화점 쇼핑"]},
    ],
    [
        {"groupName": "식료품", "keywords": ["장보기", "대형마트", "이마트", "식자재마트", "밀키트", "재래시장"]},
        {"groupName": "생활용품", "keywords": ["다이소", "올리브영", "생활용품", "인테리어소품", "무인양품"]},
        {"groupName": "유흥", "keywords": ["술집", "이자카야", "와인바", "호프", "포차", "펍"]},
        {"groupName": "교통", "keywords": ["지하철", "주차장", "KTX", "고속버스터미널", "따릉이", "택시"]},
        {"groupName": "기타", "keywords": ["미용실", "네일샵", "헬스장", "필라테스", "마사지"]},
    ],
]
NAVER_GU_TARGETED = [
    {"groupName": "강남_특화", "keywords": ["강남 맛집", "강남 피부과", "대치동 학원", "압구정 카페", "코엑스"]},
    {"groupName": "마포_특화", "keywords": ["홍대 맛집", "홍대 술집", "연남동 카페", "합정 맛집", "망원시장"]},
    {"groupName": "서대문_특화", "keywords": ["신촌 세브란스", "신촌 세브란스병원", "신촌 맛집", "연희동 맛집", "신촌 어학원"]},
    {"groupName": "금천_특화", "keywords": ["가산 아울렛", "마리오아울렛", "가산디지털단지 맛집", "현대시티아울렛 가산"]},
    {"groupName": "노원_특화", "keywords": ["중계동 학원", "은행사거리 학원", "노원역 맛집", "상계백병원", "공리단길 카페"]},
]
NAVER_GU_TOP5 = {  # 서울시_25개_자치구_네이버_검색키워드_매핑.md
    "강남구": ["강남 맛집", "압구정 카페", "대치동 학원", "강남 피부과", "신사동 가로수길"],
    "서초구": ["고터 맛집", "반포 맛집", "서초동 맛집", "양재 카페", "방배동 카페골목"],
    "송파구": ["잠실 롯데월드", "송리단길 카페", "방이동 맛집", "가락시장 회센터", "롯데월드몰"],
    "강동구": ["천호 로데오거리", "천호동 맛집", "현대백화점 천호", "명일동 학원", "강동경희대병원"],
    "중구": ["명동 쇼핑", "을지로 맛집", "힙지로 술집", "DDP 전시", "신당동 떡볶이"],
    "종로구": ["익선동 맛집", "서촌 카페", "대학로 연극", "광장시장 맛집", "인사동 갤러리"],
    "용산구": ["용리단길 맛집", "한남동 브런치", "이태원 라운지바", "용산 아이파크몰", "리움미술관"],
    "성동구": ["성수 팝업스토어", "성수동 카페", "서울숲 맛집", "왕십리 곱창", "한양대학교병원"],
    "광진구": ["건대 맛집", "건대입구 술집", "뚝섬한강공원", "동서울터미널", "건국대학교병원"],
    "동대문구": ["경동시장 장보기", "청량리 청과물시장", "회기역 파전골목", "경희의료원", "롯데백화점 청량리"],
    "중랑구": ["상봉 코스트코", "중랑천 장미축제", "상봉역 맛집", "서울의료원", "상봉 엔터식스"],
    "성북구": ["고려대 안암병원", "성북동 빵집", "성신여대 로데오", "안암 맛집", "길상사 나들이"],
    "강북구": ["수유역 맛집", "미아사거리 현대백화점", "4.19카페거리", "수유시장 장보기", "수유역 술집"],
    "도봉구": ["도봉산 등산코스", "쌍리단길 카페", "이마트 창동점", "한일병원", "창동역 포장마차"],
    "노원구": ["중계동 은행사거리 학원", "노원역 맛집", "노원 롯데백화점", "공리단길 카페", "상계백병원"],
    "은평구": ["연신내 맛집", "은평 롯데몰", "은평성모병원", "이마트 은평점", "은평 한옥마을"],
    "서대문구": ["신촌 세브란스병원", "연희동 맛집", "신촌 맛집", "현대백화점 신촌", "신촌 어학원"],
    "마포구": ["홍대 맛집", "연남동 카페", "홍대 술집", "합정 이자카야", "망원시장 장보기"],
    "양천구": ["목동 학원가", "목동 맛집", "현대백화점 목동", "이대목동병원", "목동 스터디카페"],
    "강서구": ["마곡 맛집", "서울식물원", "김포공항 주차장", "롯데몰 김포공항", "이대서울병원"],
    "구로구": ["신도림 디큐브시티", "고척스카이돔 콘서트", "구로디지털단지 맛집", "고려대 구로병원", "구디 술집"],
    "금천구": ["마리오아울렛", "가산디지털단지 맛집", "현대시티아울렛 가산", "가산 아울렛", "독산동 우시장"],
    "영등포구": ["더현대 서울", "영등포 타임스퀘어", "여의도 맛집", "문래 창작촌 카페", "여의도 회식"],
    "동작구": ["노량진 수산시장", "사당역 맛집", "중앙대학교병원", "노량진 공무원학원", "사당역 술집"],
    "관악구": ["샤로수길 맛집", "신림 순대타운", "샤로수길 카페", "양지병원", "관악산 등산"],
}
MONTHS = [f"{YEAR}-{m:02d}-01" for m in range(1, 13)]


# ── 공통 유틸 ──────────────────────────────────────────────────────────
def _open(url, data=None, referer=None, opener=None, timeout=900):
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    return (opener or urllib.request.build_opener()).open(req, timeout=timeout)


def download(url, dest, data=None, referer=None, opener=None, retries=3):
    """url → dest 스트리밍 저장. 파일 대신 HTML 에러 페이지가 오면 실패로 본다."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    for attempt in range(1, retries + 1):
        try:
            with _open(url, data, referer, opener) as r, open(tmp, "wb") as f:
                total, done, shown = int(r.headers.get("Content-Length") or 0), 0, 0
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                    done += len(chunk)
                    if total > 50 << 20 and done * 10 // total > shown:  # 큰 파일은 10% 단위 진행률
                        shown = done * 10 // total
                        print(f"      {done >> 20}MB / {total >> 20}MB", flush=True)
            with open(tmp, "rb") as f:
                head = f.read(64).lstrip().lower()
            if not head or head.startswith((b"<!doctype", b"<html")):
                raise RuntimeError("파일 대신 HTML 응답")
            tmp.replace(dest)
            return dest
        except Exception as e:
            tmp.unlink(missing_ok=True)
            if attempt == retries:
                raise
            print(f"      재시도 {attempt}/{retries - 1} ({e})")
            time.sleep(3 * attempt)


def exists(dest, force):
    if dest.exists() and not force:
        print(f"  {dest.name:<44} 건너뜀 (이미 있음, --force 로 재수집)")
        return True
    return False


def _is_utf8(head):
    try:
        codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
        return True
    except UnicodeDecodeError:
        return False


def write_utf8_bom(src, dest):
    """바이너리 스트림 → UTF-8(BOM) 텍스트. 원본이 CP949 면 변환한다."""
    first = src.read(1 << 20)
    dec = codecs.getincrementaldecoder("utf-8" if _is_utf8(first) else "cp949")()
    with open(dest, "w", encoding="utf-8-sig", newline="") as out:
        out.write(dec.decode(first).lstrip("﻿"))
        while chunk := src.read(1 << 20):
            out.write(dec.decode(chunk))
        out.write(dec.decode(b"", final=True))


def zip_name(info):
    """한글 파일명이 UTF-8 플래그 없이 CP949 로 들어간 zip 대응."""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("cp949")
    except UnicodeError:
        return info.filename


# ── 서울 열린데이터광장 ────────────────────────────────────────────────
def fetch_sheet(inf_id, name, out_dir, force):
    """시트 CSV(CP949, 전 기간) → 2025년 분기 행만 UTF-8(BOM) CSV 로 저장."""
    dest = out_dir / f"{inf_id}_{name}.csv"
    if exists(dest, force):
        return
    print(f"  {dest.name:<44} ", end="", flush=True)
    raw = out_dir / f".{inf_id}.cp949"
    download(SHEET_EP, raw,
             data={"infId": inf_id, "srvType": "S", "serviceKind": "1",
                   "isLogin": "", "stcRow": "", "fileType": "csv"},
             referer=f"https://data.seoul.go.kr/dataList/{inf_id}/S/1/datasetView.do")
    kept, quarters = 0, set()
    with open(raw, encoding="cp949", newline="") as src, \
         open(dest, "w", encoding="utf-8-sig", newline="") as dst:
        reader = csv.reader(src)
        writer = csv.writer(dst, quoting=csv.QUOTE_ALL, lineterminator="\n")
        header = next(reader)
        writer.writerow(header)
        qi = header.index(QUARTER_COL) if QUARTER_COL in header else None
        for row in reader:
            if qi is not None:
                if not row[qi].startswith(YEAR):
                    continue
                quarters.add(row[qi])
            writer.writerow(row)
            kept += 1
    raw.unlink()
    period = f"{min(quarters)}~{max(quarters)}" if quarters else "기간 없음(전체)"
    print(f"OK  {kept:>9,}행  {period}")
    if qi is not None and len(quarters) != 4:
        print(f"      ⚠ 2025년 분기가 {len(quarters)}개뿐입니다: {sorted(quarters)}")


def fetch_seoul_file(inf_id, seq, dest, force):
    if exists(dest, force):
        return
    print(f"  {dest.name:<44} ", end="", flush=True)
    download(FILE_EP, dest, data={"infId": inf_id, "seq": seq, "infSeq": 1, "seqNo": ""},
             referer=f"https://data.seoul.go.kr/dataList/{inf_id}/F/1/datasetView.do")
    print(f"OK  {dest.stat().st_size / 2**20:.1f}MB")


def run_dong(raw, args):
    for inf_id, name in DONG:
        fetch_sheet(inf_id, name, raw, args.force)


def run_trade(raw, args):
    for inf_id, name in TRADE:
        fetch_sheet(inf_id, name, raw / "상권", args.force)


def run_living(raw, args):
    for inf_id, prefix, seqs in LIVING:
        for month, seq in seqs.items():
            fetch_seoul_file(inf_id, seq, raw / "living" / f"{prefix}_{YEAR}.{month}.xlsx", args.force)


def run_stay(raw, args):
    for yymm in args.stay:
        fetch_seoul_file(STAY_ID, yymm, raw / "체류인구" / f"체류인구_내국인_250m_20{yymm}.zip", args.force)


# ── 공공데이터포털 ────────────────────────────────────────────────────
def fetch_datagokr(spec, dest):
    """세션 쿠키를 받은 뒤 atchFileId 로 파일 다운로드."""
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    _open(spec["page"], opener=opener, timeout=60).read()
    query = urllib.parse.urlencode(
        {"atchFileId": spec["atch"], "fileDetailSn": 1, "dataNm": spec["name"]})
    download(f"{DG_DOWN}?{query}", dest, referer=spec["page"], opener=opener)


def run_sbiz(raw, args):
    dest = raw / "소상공인_상가정보_서울.csv"
    if exists(dest, args.force):
        return
    print(f"  {dest.name:<44} 전국 zip 다운로드 (약 340MB)")
    zpath = raw / ".sbiz_20251231.zip"
    fetch_datagokr(SBIZ, zpath)
    with zipfile.ZipFile(zpath) as z:
        targets = [i for i in z.infolist()
                   if "서울" in zip_name(i) and zip_name(i).lower().endswith(".csv")]
        if len(targets) != 1:
            raise RuntimeError(f"서울 CSV 를 특정할 수 없음: {[zip_name(i) for i in targets]}")
        with z.open(targets[0]) as src:
            write_utf8_bom(src, dest)
    zpath.unlink()
    print(f"      ← {zip_name(targets[0])}  OK  {dest.stat().st_size / 2**20:.1f}MB")


def run_nps(raw, args):
    dest = raw / f"국민연금_시군구_평균소득월액_{YEAR}.csv"
    if exists(dest, args.force):
        return
    print(f"  {dest.name:<44} ", end="", flush=True)
    tmp = raw / ".nps.csv"
    fetch_datagokr(NPS, tmp)
    with open(tmp, "rb") as src:
        write_utf8_bom(src, dest)
    tmp.unlink()
    print("OK")


def run_geo(raw, args):
    dest = raw / "geo" / f"HangJeongDong_{GEO_VERSION}.geojson"
    if exists(dest, args.force):
        return
    print(f"  {dest.name:<44} ", end="", flush=True)
    download(GEO_URL, dest)
    print(f"OK  {dest.stat().st_size / 2**20:.1f}MB")


# ── 네이버 데이터랩 ───────────────────────────────────────────────────
def naver_keys(path):
    cid, secret = os.environ.get("NAVER_CLIENT_ID"), os.environ.get("NAVER_CLIENT_SECRET")
    key_file = Path(path) if path else ROOT / "config" / "naver_api_key.json"
    if key_file.exists():
        d = json.loads(key_file.read_text(encoding="utf-8"))
        cid, secret = d.get("client_id", cid), d.get("client_secret", secret)
    return (cid, secret) if cid and secret else None


def naver_query(keys, groups):
    """월별 검색지수 {groupName: {period: ratio}}. 검색량이 적어 빈 달은 0.0."""
    body = {"startDate": MONTHS[0], "endDate": f"{YEAR}-12-31",
            "timeUnit": "month", "keywordGroups": groups}
    req = urllib.request.Request(
        NAVER_URL, data=json.dumps(body).encode(),
        headers={"X-NCP-APIGW-API-KEY-ID": keys[0], "X-NCP-APIGW-API-KEY": keys[1],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        results = json.load(r)["results"]
    time.sleep(0.3)  # rate limit
    out = {}
    for item in results:
        got = {d["period"]: d["ratio"] for d in item.get("data", [])}
        out[item["title"]] = {m: got.get(m, 0.0) for m in MONTHS}
    return out


def write_wide(dest, series):
    with open(dest, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["period"] + [f"{g}_검색지수" for g in series])
        for m in MONTHS:
            w.writerow([m] + [series[g][m] for g in series])


def run_naver(raw, args):
    keys = naver_keys(args.naver_key)
    if not keys:
        print("  API 키 없음 → 건너뜀 (config/naver_api_key.json 또는 "
              "NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 환경변수)")
        return
    out = raw / "naver_trend"
    out.mkdir(parents=True, exist_ok=True)

    dest = out / "naver_trend_10categories_monthly.csv"
    if not exists(dest, args.force):
        series = {}
        for groups in NAVER_CATEGORY:
            series.update(naver_query(keys, groups))
        write_wide(dest, series)
        print(f"  {dest.name:<44} OK")

    dest = out / "naver_trend_gu_targeted_monthly.csv"
    if not exists(dest, args.force):
        write_wide(dest, naver_query(keys, NAVER_GU_TARGETED))
        print(f"  {dest.name:<44} OK")

    dest = out / "naver_trend_25gu_top5_monthly.csv"
    if not exists(dest, args.force):
        rows = []
        for gu, kws in NAVER_GU_TOP5.items():
            series = naver_query(keys, [{"groupName": k, "keywords": [k]} for k in kws])
            rows += [[gu, k, m, series[k][m]] for k in kws for m in MONTHS]
        with open(dest, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["자치구", "키워드", "period", "검색지수"])
            w.writerows(rows)
        print(f"  {dest.name:<44} OK  (25개 구 × 5 키워드)")


# ── 수집 결과 목록 ────────────────────────────────────────────────────
PERIOD_COLS = (QUARTER_COL, "period", "기준년월")


def write_manifest(raw):
    rows = []
    for p in sorted(raw.rglob("*")):
        if not p.is_file() or p.name.startswith(".") or p.name == "MANIFEST.csv":
            continue
        n_rows, period = "", ""
        if p.suffix == ".csv":
            with open(p, encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                pi = next((header.index(c) for c in PERIOD_COLS if c in header), None)
                values, n = set(), 0
                for row in reader:
                    n += 1
                    if pi is not None:
                        values.add(row[pi])
                n_rows = n
                if values:
                    period = f"{min(values)}~{max(values)}"
        rows.append([p.relative_to(raw).as_posix(), f"{p.stat().st_size / 2**20:.2f}", n_rows, period])
    with open(raw / "MANIFEST.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["파일", "크기_MB", "행수", "기간"])
        w.writerows(rows)
    total = sum(float(r[1]) for r in rows)
    print(f"\nMANIFEST.csv 작성: 파일 {len(rows)}개, 합계 {total:,.1f}MB")


SECTIONS = {
    "dong":   ("서울 상권분석서비스 — 행정동/자치구 10종", run_dong),
    "trade":  ("서울 상권분석서비스 — 상권 8종", run_trade),
    "living": ("서울 시민생활 데이터(SKT) — 2025 분기말 월", run_living),
    "sbiz":   ("소상공인 상가(상권)정보 — 2025-12-31 기준, 서울", run_sbiz),
    "nps":    ("국민연금 시군구 평균소득월액 — 2025-12 기준", run_nps),
    "geo":    ("행정동 경계 GeoJSON — ver20251231", run_geo),
    "naver":  ("네이버 데이터랩 검색어 트렌드 — 2025-01~12", run_naver),
}


def main():
    ap = argparse.ArgumentParser(description="SpotFit 원천 데이터 2025년분 수집")
    ap.add_argument("--only", nargs="+", choices=SECTIONS, help="일부 데이터셋만 수집")
    ap.add_argument("--stay", nargs="+", default=[], metavar="YYMM",
                    help="체류인구 월 파일 추가 (예: 2512, 개당 약 450MB)")
    ap.add_argument("--naver-key", help="네이버 API 키 JSON 경로 (기본: config/naver_api_key.json)")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "raw", help="저장 폴더")
    ap.add_argument("--force", action="store_true", help="이미 있는 파일도 다시 받기")
    args = ap.parse_args()

    raw = args.out.resolve()
    raw.mkdir(parents=True, exist_ok=True)
    print(f"저장 위치: {raw}\n")

    jobs = [(k, *SECTIONS[k]) for k in (args.only or SECTIONS)]
    if args.stay:
        jobs.append(("stay", f"서울 체류인구(250m, 내국인) — {', '.join(args.stay)}", run_stay))

    failed = []
    for key, title, fn in jobs:
        print(f"[{key}] {title}")
        try:
            fn(raw, args)
        except Exception as e:
            print(f"\n  ✗ 실패: {e}")
            failed.append(key)
        print()

    write_manifest(raw)
    if failed:
        print(f"실패한 항목: {', '.join(failed)} → python scripts/fetch_raw_2025.py --only {' '.join(failed)}")
        sys.exit(1)
    print("완료")


if __name__ == "__main__":
    main()
