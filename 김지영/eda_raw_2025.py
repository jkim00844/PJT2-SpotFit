"""data/raw (2025년분) EDA 그림 생성 스크립트.

실행: python 김지영/eda_raw_2025.py   (저장소 루트에서, pandas·matplotlib·openpyxl 필요)
결과: 김지영/eda_figures/*.png  ->  김지영/EDA_raw_2025.md 에서 사용
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, LogNorm, TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = Path(__file__).resolve().parent / "eda_figures"
OUT.mkdir(exist_ok=True)

# ── 스타일 (dataviz 기본 팔레트) ─────────────────────────────
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, GRAY = "#e1e0d9", "#c3c2b7", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGE = LinearSegmentedColormap.from_list(
    "div", ["#184f95", "#3987e5", "#9ec5f4", "#f0efec", "#f4a3a2", "#e34948", "#a32a2a"])
SEQ = LinearSegmentedColormap.from_list("seq", BLUE_RAMP)

plt.rcParams.update({
    "font.family": "AppleGothic", "axes.unicode_minus": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 13, "axes.titlesize": 19, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.titlelocation": "left", "axes.titlepad": 16,
})


def read(name):
    return pd.read_csv(RAW / name, encoding="utf-8-sig", low_memory=False)


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print("saved", name)


def subtitle(ax, text):
    ax.set_title(ax.get_title(loc="left"), loc="left", pad=38)
    ax.text(0, 1.02, text, transform=ax.transAxes, color=INK2, fontsize=13, va="bottom")


HALO = [pe.withStroke(linewidth=3.5, foreground=SURFACE)]


def hgrid(ax, axis="y"):
    ax.grid(True, axis=axis)
    ax.set_axisbelow(True)


K = "행정동_코드"
cons = read("OA-22166_소비_행정동.csv")
CATS = [c for c in cons.columns if c.endswith("_지출_총금액") and c != "지출_총금액"]
NICE = {c: c.replace("_지출_총금액", "").replace("_", "·") for c in CATS}
year = cons.groupby([K, "행정동_코드_명"])[["지출_총금액"] + CATS].sum().reset_index()
year = year.sort_values("지출_총금액", ascending=False).reset_index(drop=True)


# ── 01. 데이터 줌 레벨 ───────────────────────────────────────
def fig_zoom():
    rows = [
        ("자치구", "25개", "소비·아파트·상주인구(자치구), 국민연금 평균소득, 네이버 검색"),
        ("행정동", "425개", "소비·아파트·상주·직장·유동인구·집객시설, SKT 통신, 경계(geojson)"),
        ("상권", "1,650개", "추정매출·점포(개·폐업)·상권변화지표·인구·집객시설"),
        ("점포", "53만 개", "소상공인 상가정보 (2025-12-31 한 장)"),
        ("사람", "1,000명", "빅데이터캠퍼스 금융생활·소비이동 (합성 샘플)"),
    ]
    fig, ax = plt.subplots(figsize=(13, 6.4))
    ax.set_xlim(0, 13); ax.set_ylim(0, len(rows) + 0.4); ax.axis("off")
    for i, (lvl, n, files) in enumerate(rows):
        y = len(rows) - i - 0.5
        w = 3.6 - i * 0.55  # 아래로 갈수록 더 작은 단위
        x0 = 0.2 + (3.6 - w) / 2
        ax.add_patch(FancyBboxPatch((x0, y - 0.36), w, 0.72, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=BLUE_RAMP[5 - i], ec="none"))
        tc = "white" if i < 3 else INK
        ax.text(0.2 + 1.8, y + 0.07, lvl, ha="center", va="center", fontsize=19, weight="bold", color=tc)
        ax.text(0.2 + 1.8, y - 0.2, n, ha="center", va="center", fontsize=12, color=tc)
        ax.text(4.3, y, files, va="center", fontsize=14, color=INK)
    ax.annotate("", xy=(0.05, 0.25), xytext=(0.05, len(rows) - 0.1),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))
    ax.text(-0.15, len(rows) / 2, "더 잘게", rotation=90, ha="center", va="center", color=MUTED, fontsize=12)
    ax.set_title("data/raw 안에는 '크기가 다른 렌즈' 5개가 있어요")
    save(fig, "01_data_zoom.png")


# ── 02. 소비 쏠림 와플 ───────────────────────────────────────
def fig_waffle():
    tot = year["지출_총금액"].sum()
    s5 = year["지출_총금액"].head(5).sum() / tot * 100
    s21 = year["지출_총금액"].head(21).sum() / tot * 100
    blocks = [round(s5), round(s21) - round(s5)]
    blocks.append(100 - sum(blocks))
    colors = [BLUE] * blocks[0] + [ORANGE] * blocks[1] + [GRAY] * blocks[2]
    fig, ax = plt.subplots(figsize=(12, 6.6))
    for idx, col in enumerate(colors):
        r, c = divmod(idx, 10)
        ax.add_patch(FancyBboxPatch((c, 9 - r), 0.86, 0.86, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=col, ec="none"))
    ax.set_xlim(-0.2, 21); ax.set_ylim(-0.3, 10.2); ax.set_aspect("equal"); ax.axis("off")
    top5 = ", ".join(year["행정동_코드_명"].head(5))
    legend = [
        (BLUE, f"{blocks[0]}칸", "상위 5개 동", top5),
        (ORANGE, f"{blocks[1]}칸", "6~21위 동 (16개)", "회현동, 서초3동, 대치4동, 여의동 …"),
        (GRAY, f"{blocks[2]}칸", "나머지 404개 동", "서울 동의 95%"),
    ]
    for i, (col, n, lbl, desc) in enumerate(legend):
        y = 8.3 - i * 2.9
        ax.add_patch(FancyBboxPatch((11, y), 0.86, 0.86, boxstyle="round,pad=0,rounding_size=0.12", fc=col, ec="none"))
        ax.text(12.2, y + 0.62, f"{lbl}  ·  {n}", fontsize=16, weight="bold", color=INK, va="center")
        ax.text(12.2, y - 0.05, desc, fontsize=12, color=INK2, va="center")
    ax.set_title("서울에서 쓴 돈 100원 중 60원은 동 5곳에서 결제됐어요")
    ax.text(0, -0.25, "2025년 1~4분기 행정동 '지출_총금액' 합계 기준 (425개 동)", color=MUTED, fontsize=11, va="top")
    save(fig, "02_spending_waffle.png")


# ── 지도 공통 ───────────────────────────────────────────────
# 상권분석 데이터는 분동 전 이름을 쓴다 → 2025-12 경계에서 해당 조각을 묶어서 그린다
OLD_DONG = {11230536: ["11230515", "11230533"],   # 용신동 = 신설동 + 용두동
            11740520: ["11740525", "11740526"],   # 상일동 = 상일제1동 + 상일제2동
            11680740: ["11680675"]}               # 일원2동 = 개포3동


def load_polys():
    gj = json.loads((RAW / "geo" / "HangJeongDong_ver20251231.geojson").read_text())
    polys = {}
    for f in gj["features"]:
        p = f["properties"]
        if p["sido"] != "11":
            continue
        g = f["geometry"]
        parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        polys.setdefault(p["adm_cd2"][:8], []).extend(np.array(pt[0]) for pt in parts)
    for new, olds in OLD_DONG.items():
        polys[str(new)] = sum((polys.pop(o) for o in olds), [])
    return polys


POLYS = load_polys()
GU_POLYS = None


def draw_map(ax, values, cmap, norm):
    verts, cols, empty = [], [], []
    for code, rings in POLYS.items():
        v = values.get(int(code), np.nan)
        if pd.isna(v):
            empty.extend(rings)
            continue
        for ring in rings:
            verts.append(ring)
            cols.append(cmap(norm(v)))
    ax.add_collection(PolyCollection(verts, facecolors=cols, edgecolors=SURFACE, linewidths=0.4))
    if empty:
        ax.add_collection(PolyCollection(empty, facecolors=SURFACE, edgecolors=MUTED, linewidths=0.6, hatch="////"))
    ax.autoscale_view(); ax.set_aspect(1 / np.cos(np.deg2rad(37.55))); ax.axis("off")


def centroid(code):
    ring = max(POLYS[str(code)], key=len)
    return ring[:, 0].mean(), ring[:, 1].mean()


def map_label(ax, code, text, offset):
    ax.annotate(text, centroid(code), xytext=offset, textcoords="offset points", fontsize=12, color=INK,
                weight="bold", path_effects=HALO, arrowprops=dict(arrowstyle="-", color=INK, lw=1))


# ── 03. 총 지출 지도 ────────────────────────────────────────
def fig_map_spending():
    vals = year.set_index(K)["지출_총금액"] / 1e8
    fig, ax = plt.subplots(figsize=(12, 9.4))
    norm = LogNorm(vals.min(), vals.max())
    draw_map(ax, vals.to_dict(), SEQ, norm)
    offsets = {"소공동": (-30, 60), "구로3동": (-90, -50), "문래동": (-95, 45), "역삼1동": (40, 55), "역삼2동": (55, -45)}
    for _, r in year.head(5).iterrows():
        map_label(ax, r[K], f"{r['행정동_코드_명']} {r['지출_총금액']/1e12:.1f}조", offsets[r["행정동_코드_명"]])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=SEQ)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.02, aspect=40)
    cb.set_label("2025년 지출_총금액 (억 원, 로그 눈금)", color=INK2); cb.outline.set_visible(False)
    ax.set_title("진한 곳 = 지출이 많이 잡힌 동 (도심·업무지구)")
    save(fig, "03_map_spending.png")


# ── 04. 합계의 함정: 서울 합계 vs 보통 동 ─────────────────────
def fig_composition():
    total_share = year[CATS].sum() / year["지출_총금액"].sum() * 100
    median_share = (year[CATS].div(year["지출_총금액"], axis=0) * 100).median()
    order = median_share.sort_values().index
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(12, 7.2))
    h = 0.38
    ax.barh(y + h / 2 + 0.02, total_share[order], height=h, color=GRAY, label="서울 전체 합계 기준")
    ax.barh(y - h / 2 - 0.02, median_share[order], height=h, color=BLUE, label="보통 동 (동별 비중의 중앙값)")
    for yi, c in zip(y, order):
        ax.text(median_share[c] + 0.8, yi - h / 2 - 0.02, f"{median_share[c]:.0f}%", va="center", fontsize=11, color=INK)
        ax.text(total_share[c] + 0.8, yi + h / 2 + 0.02, f"{total_share[c]:.0f}%", va="center", fontsize=11, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([NICE[c] for c in order], color=INK, fontsize=13)
    ax.set_xlabel("지출에서 차지하는 비중 (%)"); hgrid(ax, "x")
    ax.legend(loc="lower right", frameon=False, fontsize=12)
    ax.set_title("합계로 보면 '여가·문화'가 63%, 보통 동은 식료품·음식이 절반")
    subtitle(ax, "합계는 상위 몇 개 동(소공동·구로3동·문래동, 여가·문화 98~99%)이 끌고 간 숫자예요")
    save(fig, "04_spending_mix.png")


# ── 05. 소비와 같이 움직이는 것 ───────────────────────────────
def dong_table():
    p = read("OA-22183_상주인구_행정동.csv").groupby(K)[["총_상주인구_수", "총_가구_수"]].mean()
    w = read("OA-22184_직장인구_행정동.csv").groupby(K)["총_직장_인구_수"].mean()
    fl = read("OA-22178_길단위인구_행정동.csv").groupby(K)["총_유동인구_수"].mean()
    a = read("OA-22163_아파트_행정동.csv").groupby(K)[["아파트_평균_시가", "아파트_단지_수"]].mean()
    f = read("OA-22169_집객시설_행정동.csv").fillna(0).groupby(K)[["집객시설_수", "지하철_역_수", "은행_수"]].mean()
    ar = read("OA-22160_영역_행정동.csv").set_index(K)["영역_면적"]
    return pd.concat([year.set_index(K)["지출_총금액"], p, w, fl, a, f, ar], axis=1)


DONG = dong_table()


def fig_correlation():
    labels = {"집객시설_수": "집객시설 수", "은행_수": "은행 수", "총_직장_인구_수": "직장인 수",
              "총_유동인구_수": "유동인구", "총_가구_수": "가구 수", "총_상주인구_수": "사는 사람 수",
              "지하철_역_수": "지하철역 수", "영역_면적": "동 면적", "아파트_단지_수": "아파트 단지 수",
              "아파트_평균_시가": "아파트 평균 시가"}
    come = {"집객시설_수", "은행_수", "총_직장_인구_수", "총_유동인구_수", "지하철_역_수"}
    rho = DONG.corr(method="spearman")["지출_총금액"].drop("지출_총금액").sort_values()
    fig, ax = plt.subplots(figsize=(12, 7))
    cols = [BLUE if k in come else ORANGE for k in rho.index]
    ax.barh(range(len(rho)), rho.values, color=cols, height=0.62)
    for i, v in enumerate(rho.values):
        ax.text(v + 0.012, i, f"{v:.2f}", va="center", fontsize=12, color=INK)
    ax.set_yticks(range(len(rho))); ax.set_yticklabels([labels[k] for k in rho.index], color=INK, fontsize=13)
    ax.set_xlim(0, 0.85); ax.set_xlabel("지출_총금액과의 순위 상관 (Spearman ρ, 425개 동)"); hgrid(ax, "x")
    ax.barh([0], [0], color=BLUE, label="오는 사람·시설"); ax.barh([0], [0], color=ORANGE, label="사는 사람·집")
    ax.legend(loc="lower right", frameon=False, fontsize=13)
    ax.set_title("돈은 '사는 곳'보다 '오는 곳'에서 쓰여요")
    subtitle(ax, "1에 가까울수록 같이 커지고 같이 작아진다는 뜻")
    save(fig, "05_what_moves_with_spending.png")


# ── 06. 분기 흐름 ─────────────────────────────────────────
SALES = read("상권/OA-15572_추정매출_상권.csv")
STORES = read("상권/OA-15577_점포_상권.csv")


def fig_quarters():
    q = ["20251", "20252", "20253", "20254"]
    series = {
        "행정동 지출": cons.groupby("기준_년분기_코드")["지출_총금액"].sum(),
        "상권 추정매출": SALES.groupby("기준_년분기_코드")["당월_매출_금액"].sum(),
        "상권 점포 수": STORES.groupby("기준_년분기_코드")["전체_점포_수"].sum(),
    }
    fig, ax = plt.subplots(figsize=(12, 6.6))
    for (name, s), col in zip(series.items(), [BLUE, ORANGE, AQUA]):
        idx = s / s.iloc[0] * 100
        ax.plot(range(4), idx.values, color=col, lw=2.4, marker="o", ms=8, mec=SURFACE, mew=2, label=name)
        ax.text(3.12, idx.iloc[-1], f"{name}  {idx.iloc[-1]-100:+.1f}%", va="center", fontsize=13, color=INK)
    ax.axhline(100, color=AXIS, lw=1)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"2025 {x[-1]}분기" for x in q], color=INK2)
    ax.set_xlim(-0.2, 4.4); ax.set_ylabel("1분기 = 100"); hgrid(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=12)
    ax.set_title("1년 동안 쓰는 돈은 늘고, 가게 수는 조금 줄었어요")
    save(fig, "06_quarter_trend.png")


# ── 07. 언제 돈을 쓰나 ────────────────────────────────────
def fig_when():
    tcols = [c for c in SALES.columns if c.startswith("시간대_") and c.endswith("_매출_금액")]
    tl = ["새벽\n0~6", "아침\n6~11", "점심\n11~14", "오후\n14~17", "저녁\n17~21", "밤\n21~24"]
    days = ["월", "화", "수", "목", "금", "토", "일"]
    dcols = [f"{d}요일_매출_금액" for d in days]
    ts = SALES[tcols].sum() / SALES[tcols].sum().sum() * 100
    ds = SALES[dcols].sum() / SALES[dcols].sum().sum() * 100
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw=dict(wspace=0.25))
    for ax, s, lab, title in [(a1, ts, tl, "하루 중 (시간대별 매출 비중)"), (a2, ds, days, "일주일 중 (요일별 매출 비중)")]:
        top = s.values.argmax()
        cols = [BLUE if i == top else "#9ec5f4" for i in range(len(s))]
        ax.bar(range(len(s)), s.values, color=cols, width=0.68)
        for i, v in enumerate(s.values):
            ax.text(i, v + 0.4, f"{v:.0f}%", ha="center", fontsize=11, color=INK if i == top else INK2)
        ax.set_xticks(range(len(s))); ax.set_xticklabels(lab, color=INK2)
        ax.set_yticks([]); ax.spines["left"].set_visible(False)
        ax.set_title(title, fontsize=15)
    fig.suptitle("점심~저녁(11~21시)이 매출의 77%, 일요일은 확 줄어요", x=0.125, ha="left",
                 fontsize=19, weight="bold", color=INK, y=1.04)
    save(fig, "07_when_people_spend.png")


# ── 08. 열리는 가게 vs 닫히는 가게 ────────────────────────────
def fig_open_close():
    q = STORES.groupby("서비스_업종_코드_명")[["전체_점포_수", "개업_점포_수", "폐업_점포_수"]].sum()
    q = q[q["전체_점포_수"] >= 20000]
    q["개업률"] = q["개업_점포_수"] / q["전체_점포_수"] * 100
    q["폐업률"] = q["폐업_점포_수"] / q["전체_점포_수"] * 100
    fig, ax = plt.subplots(figsize=(12, 8.4))
    grow = q["개업률"] > q["폐업률"]
    for mask, col, lbl in [(grow, BLUE, "열리는 곳이 더 많은 업종"), (~grow, ORANGE, "닫히는 곳이 더 많은 업종")]:
        ax.scatter(q.loc[mask, "개업률"], q.loc[mask, "폐업률"], s=q.loc[mask, "전체_점포_수"] / 260,
                   color=col, alpha=0.85, edgecolor=SURFACE, linewidth=2, label=lbl)
    lim = 6.2
    ax.plot([0, lim], [0, lim], color=AXIS, lw=1.2)
    ax.text(5.0, 5.25, "열림 = 닫힘", color=MUTED, fontsize=11, rotation=33)
    big = q["전체_점포_수"].nlargest(6).index
    show = {"전자상거래업": (8, 4), "호프-간이주점": (-10, 12), "커피-음료": (-70, 14), "한식음식점": (22, -22),
            "패스트푸드점": (6, 8), "분식전문점": (14, 2), "일식음식점": (8, 4), "피부관리실": (-40, 12),
            "편의점": (8, 4), "세무사사무소": (8, -4), "일반의원": (8, -4), "미용실": (8, -14)}
    for name in big:
        show.setdefault(name, (10, 6))
    for name, off in show.items():
        ax.annotate(name, (q.loc[name, "개업률"], q.loc[name, "폐업률"]), xytext=off,
                    textcoords="offset points", fontsize=11, color=INK, path_effects=HALO)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim); hgrid(ax, "both")
    ax.set_xlabel("개업률 (%, 분기 평균)"); ax.set_ylabel("폐업률 (%, 분기 평균)")
    lg = ax.legend(loc="lower right", frameon=False, fontsize=12)
    for h in getattr(lg, "legend_handles", None) or lg.legendHandles:
        h.set_sizes([90])
    ax.set_title("선 위에 있는 업종은 1년 내내 '닫히는 가게'가 더 많았어요")
    subtitle(ax, "점 크기 = 점포 수 · 2025년 4개 분기 합계, 점포-분기 2만 이상 업종만")
    save(fig, "08_open_vs_close.png")


# ── 09. 상권변화지표 ───────────────────────────────────────
def fig_change_index():
    ch = read("상권/OA-15576_상권변화지표_상권.csv")
    q4 = ch[ch["기준_년분기_코드"] == 20254]["상권_변화_지표_명"].value_counts()
    desc = {"정체": "오래 버티고, 문 닫는 곳도 오래 버팀 (HH)", "다이나믹": "새 가게도 금방, 문 닫는 것도 금방 (LL)",
            "상권축소": "있는 가게는 오래됐는데 새로 닫는 곳은 빨리 닫음 (HL)", "상권확장": "새로 생기는 가게가 많은 젊은 상권 (LH)"}
    order = ["정체", "다이나믹", "상권축소", "상권확장"]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.barh(range(4)[::-1], [q4[o] for o in order], color=BLUE, height=0.6)
    for i, o in enumerate(order):
        yy = 3 - i
        ax.text(q4[o] + 8, yy, f"{q4[o]}곳", va="center", fontsize=14, weight="bold", color=INK)
        ax.text(700, yy, desc[o], va="center", fontsize=12, color=INK2)
    ax.set_yticks(range(4)[::-1]); ax.set_yticklabels(order, fontsize=14, color=INK)
    ax.set_xlim(0, 1320); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    ax.set_title("2025년 4분기, 서울 상권 1,650곳의 '체질'")
    subtitle(ax, "상권변화지표 = 운영 중인 가게·폐업한 가게의 평균 영업기간을 서울 평균과 비교한 4분류")
    save(fig, "09_district_change.png")


# ── 10. 소상공인 점포 ──────────────────────────────────────
def fig_sbiz():
    s = pd.read_csv(RAW / "소상공인_상가정보_서울.csv", encoding="utf-8-sig",
                    usecols=["상권업종대분류명", "시군구명"])
    big = s["상권업종대분류명"].value_counts().sort_values()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw=dict(width_ratios=[1, 1.15], wspace=0.35))
    a1.barh(range(len(big)), big.values / 1e4, color=BLUE, height=0.62)
    for i, v in enumerate(big.values):
        a1.text(v / 1e4 + 0.2, i, f"{v/1e4:.1f}만", va="center", fontsize=11, color=INK)
    a1.set_yticks(range(len(big))); a1.set_yticklabels(big.index, fontsize=12, color=INK)
    a1.set_xticks([]); a1.spines["bottom"].set_visible(False); a1.set_title("업종 대분류별", fontsize=15)
    gu = s["시군구명"].value_counts().sort_values()
    cols = [BLUE if g == "강남구" else "#9ec5f4" for g in gu.index]
    a2.barh(range(len(gu)), gu.values / 1e4, color=cols, height=0.7)
    for i, v in enumerate(gu.values):
        if i >= len(gu) - 3 or i < 2:
            a2.text(v / 1e4 + 0.1, i, f"{v/1e4:.1f}만", va="center", fontsize=10, color=INK)
    a2.set_yticks(range(len(gu))); a2.set_yticklabels(gu.index, fontsize=10, color=INK)
    a2.set_xticks([]); a2.spines["bottom"].set_visible(False); a2.set_title("자치구별", fontsize=15)
    fig.suptitle(f"서울 가게 {len(s)/1e4:.1f}만 곳: 4곳 중 1곳은 음식점, 강남구에만 8곳 중 1곳",
                 x=0.125, ha="left", fontsize=19, weight="bold", color=INK, y=1.02)
    save(fig, "10_stores_snapshot.png")


# ── 11. 국민연금 평균소득 ──────────────────────────────────
def fig_income():
    n = read("국민연금_시군구_평균소득월액_2025.csv")
    seoul = n[n["시군구"].str.startswith("서울")].copy()
    seoul["구"] = seoul["시군구"].str.replace("서울특별시", "")
    seoul = seoul.sort_values("평균소득월액")
    fig, ax = plt.subplots(figsize=(12, 8))
    top3 = set(seoul["구"].tail(3))
    cols = [BLUE if g in top3 else "#9ec5f4" for g in seoul["구"]]
    ax.barh(range(len(seoul)), seoul["평균소득월액"] / 1e4, color=cols, height=0.7)
    nat = n["평균소득월액"].median() / 1e4
    ax.axvline(nat, color=ORANGE, lw=1.8)
    ax.text(nat + 1, -1.3, f"전국 시군구 중앙값 {nat:.0f}만 원", color=INK, fontsize=12)
    for i, (g, v) in enumerate(zip(seoul["구"], seoul["평균소득월액"])):
        if i < 3 or i >= len(seoul) - 3:
            ax.text(v / 1e4 + 1, i, f"{v/1e4:.0f}만", va="center", fontsize=11, color=INK)
    ax.set_yticks(range(len(seoul))); ax.set_yticklabels(seoul["구"], fontsize=11, color=INK)
    ax.set_xlim(100, 190); ax.set_xlabel("국민연금 가입자 평균소득월액 (만 원, 2025-12)"); hgrid(ax, "x")
    lo, hi = seoul.iloc[0], seoul.iloc[-1]
    ax.set_title(f"월 소득(국민연금 기준): 1등 {hi['구']} {hi['평균소득월액']/1e4:.0f}만, 꼴찌 {lo['구']} {lo['평균소득월액']/1e4:.0f}만 원")
    save(fig, "11_income_by_gu.png")


# ── 12. 네이버 검색 계절성 ─────────────────────────────────
def fig_naver():
    nt = read("naver_trend/naver_trend_10categories_monthly.csv").set_index("period")
    nt.columns = [c.replace("_검색지수", "").replace("_", "·") for c in nt.columns]
    dev = (nt / nt.mean() - 1) * 100  # 자기 평균 대비 %
    fig, ax = plt.subplots(figsize=(13, 6.6))
    lim = np.nanmax(np.abs(dev.values))
    im = ax.imshow(dev.T.values, cmap=DIVERGE, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
    ax.set_xticks(range(12)); ax.set_xticklabels([f"{i}월" for i in range(1, 13)], color=INK2)
    ax.set_yticks(range(len(dev.columns))); ax.set_yticklabels(dev.columns, color=INK, fontsize=12)
    for (i, j), v in np.ndenumerate(dev.T.values):
        if abs(v) >= 15:
            ax.text(j, i, f"{v:+.0f}", ha="center", va="center", fontsize=10,
                    color="white" if abs(v) > lim * 0.55 else INK)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02); cb.outline.set_visible(False)
    cb.set_label("그 카테고리의 1년 평균 대비 (%)", color=INK2)
    ax.set_title("검색이 몰리는 달: 7월 여가·문화 +49%, 4월 교육 +36%, 1월(설) 식료품 +34%")
    subtitle(ax, "카테고리끼리 높이 비교 X — 각 줄을 자기 평균과만 비교한 그림 (빨강 = 평소보다 많이 검색)")
    save(fig, "12_naver_season.png")


# ── 13. SKT 통신: 나이별 생활 ───────────────────────────────
def fig_skt():
    t = pd.read_excel(RAW / "living" / "통신정보_2025.12.xlsx")
    metrics = [("배달 서비스 사용일수", "배달 앱"), ("쇼핑 서비스 사용일수", "쇼핑 앱"), ("금융 서비스 사용일수", "금융 앱")]
    g = t.groupby("연령대").apply(lambda d: pd.Series(
        {m: np.average(d[m], weights=d["총인구수"]) for m, _ in metrics}))
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), gridspec_kw=dict(wspace=0.3))
    for ax, (m, lbl) in zip(axes, metrics):
        s = g[m]
        ax.plot(s.index, s.values, color=BLUE, lw=2.4, marker="o", ms=7, mec=SURFACE, mew=2)
        peak = s.idxmax()
        ax.annotate(f"최고 {peak}대 · {s.max():.0f}", (peak, s.max()), xytext=(0, 12),
                    textcoords="offset points", fontsize=11, color=INK, ha="center")
        ax.set_title(lbl, fontsize=15); hgrid(ax); ax.set_ylim(0, s.max() * 1.25)
        ax.set_xticks([20, 30, 40, 50, 60, 70]); ax.set_xticklabels(["20대", "30", "40", "50", "60", "70+"], color=INK2)
    axes[0].set_ylabel("사용일수 (원본 단위, 인구 가중 평균)")
    fig.suptitle("배달·쇼핑·금융 앱은 30~40대가 제일 많이 쓰고, 60대부터 뚝 떨어져요",
                 x=0.125, ha="left", fontsize=19, weight="bold", color=INK, y=1.06)
    save(fig, "13_skt_age.png")


# ── 14. 빅데이터캠퍼스 합성 샘플 ─────────────────────────────
def fig_synthetic():
    b = read("bigdata_campus/seoul_lifestyle_금융생활_재현데이터_sample1000.csv")
    b = b[(b["추정연소득"] > 0) & (b["카드소비금액"] > 0)]
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.scatter(b["추정연소득"], b["카드소비금액"], s=34, color=BLUE, alpha=0.55, edgecolor=SURFACE, linewidth=1)
    ax.set_xscale("log"); ax.set_yscale("log"); hgrid(ax, "both")
    xt = [15000, 30000, 60000, 120000, 240000]
    ax.set_xticks(xt); ax.set_xticklabels([f"{v:,}" for v in xt]); ax.minorticks_off()
    yt = [10, 100, 1000, 10000, 100000]
    ax.set_yticks(yt); ax.set_yticklabels([f"{v:,}" for v in yt])
    ax.set_xlabel("추정연소득 (원본 단위, 로그)"); ax.set_ylabel("카드소비금액 (원본 단위, 로그)")
    rho = b[["추정연소득", "카드소비금액"]].corr(method="spearman").iloc[0, 1]
    ax.set_title(f"번 만큼 쓰긴 하지만 들쭉날쭉해요 (순위 상관 {rho:.2f})")
    subtitle(ax, f"빅데이터캠퍼스 '재현(합성)' 데이터 {len(b)}명 — 진짜 사람이 아니에요, 모양 연습용")
    save(fig, "14_synthetic_income_vs_card.png")


# ── 15. 소비 갭 맛보기 ─────────────────────────────────────
def fig_gap_preview():
    d = DONG[["지출_총금액", "총_상주인구_수", "총_직장_인구_수", "총_유동인구_수", "집객시설_수"]].dropna()
    X = np.column_stack([np.ones(len(d))] + [np.log1p(d[c]) for c in d.columns[1:]])
    y = np.log(d["지출_총금액"])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    ratio = np.exp(resid)  # 실제 / 기대
    names = year.set_index(K)["행정동_코드_명"]
    fig, ax = plt.subplots(figsize=(12, 9.4))
    lim = np.nanmax(np.abs(resid))
    norm = TwoSlopeNorm(0, -lim, lim)
    draw_map(ax, resid.to_dict(), DIVERGE, norm)
    offsets = [(50, 30), (-100, -45), (-100, 40), (-70, -75), (40, -50), (-120, 35)]
    for code, off in zip(list(resid.nlargest(3).index) + list(resid.nsmallest(3).index), offsets):
        fmt = f"×{ratio[code]:.0f}" if resid[code] > 0 else f"×{ratio[code]:.2f}"
        map_label(ax, code, f"{names[code]} {fmt}", off)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=DIVERGE)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.02, aspect=40)
    ticks = [-3, -2, -1, 0, 1, 2, 3]
    cb.set_ticks([t for t in ticks if abs(t) <= lim])
    cb.set_ticklabels([f"×{np.exp(t):.2g}" for t in ticks if abs(t) <= lim])
    cb.outline.set_visible(False); cb.set_label("실제 지출 ÷ 기대 지출  (빗금 = 직장인구 데이터 없는 11개 동)", color=INK2)
    ax.set_title("소비 갭 맛보기: 빨강 = 기대보다 더 씀, 파랑 = 덜 씀")
    subtitle(ax, f"아주 단순한 모델(사는 사람·직장인·유동인구·집객시설 → 지출, 로그 회귀, R²={r2:.2f})의 잔차")
    save(fig, "15_gap_preview_map.png")
    out = pd.DataFrame({"행정동": names[resid.index], "실제/기대": ratio.round(2)}).sort_values("실제/기대")
    print("R2", round(r2, 3), "beta", np.round(beta, 3))
    print(out.head(8).to_string()); print(out.tail(8).to_string())


# ── 16. 데이터마다 다른 동 개수 ──────────────────────────────
def fig_dong_counts():
    t = pd.read_excel(RAW / "living" / "통신정보_2025.12.xlsx", usecols=["행정동코드"])
    s = pd.read_csv(RAW / "소상공인_상가정보_서울.csv", encoding="utf-8-sig", usecols=["행정동코드"])
    counts = [
        ("상권분석 소비·상주·유동·집객", cons[K].nunique()),
        ("상권분석 아파트", read("OA-22163_아파트_행정동.csv")[K].nunique()),
        ("상권분석 직장인구", read("OA-22184_직장인구_행정동.csv")[K].nunique()),
        ("SKT 통신정보·관심집단", t["행정동코드"].nunique()),
        ("행정동 경계 geojson (2025-12)", len(POLYS) + sum(len(v) - 1 for v in OLD_DONG.values())),
        ("소상공인 상가정보 (코드 기준)", s["행정동코드"].nunique()),
    ][::-1]
    fig, ax = plt.subplots(figsize=(12, 5.4))
    vals = [v for _, v in counts]
    cols = [BLUE if v == 425 else ORANGE for v in vals]
    ax.axvline(425, color=AXIS, lw=1.2)
    ax.hlines(range(len(counts)), 425, vals, color=cols, lw=2)
    ax.scatter(vals, range(len(counts)), s=160, color=cols, edgecolor=SURFACE, linewidth=2, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + (0.7 if v >= 425 else -0.7), i, f"{v}개", va="center", ha="left" if v >= 425 else "right",
                fontsize=13, weight="bold", color=INK)
    ax.set_yticks(range(len(counts))); ax.set_yticklabels([n for n, _ in counts], fontsize=13, color=INK)
    ax.set_xlim(408, 433); ax.set_xticks([410, 415, 420, 425, 430]); hgrid(ax, "x")
    ax.set_title("같은 서울인데 파일마다 '동 개수'가 달라요")
    subtitle(ax, "세로선 = 상권분석 기준 425개 · 적으면 빠진 동, 많으면 2025년에 쪼개진 동이 따로 있음")
    save(fig, "16_dong_counts.png")


if __name__ == "__main__":
    for fn in [fig_zoom, fig_waffle, fig_map_spending, fig_composition, fig_correlation, fig_quarters,
               fig_when, fig_open_close, fig_change_index, fig_sbiz, fig_income, fig_naver, fig_skt,
               fig_synthetic, fig_gap_preview, fig_dong_counts]:
        fn()
