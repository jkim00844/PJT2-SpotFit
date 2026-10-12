"""2025 Q4 dong and trade-area-by-industry EDA from repository raw CSVs."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIGURES = Path(__file__).resolve().parent / "eda_figures"
FIGURES.mkdir(exist_ok=True)


def read(path: str) -> pd.DataFrame:
    return pd.read_csv(
        RAW / path,
        encoding="utf-8-sig",
        dtype={"상권_코드": str, "행정동_코드": str, "서비스_업종_코드": str},
    )


def q4(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["기준_년분기_코드"] == 20254].copy()


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("C:/Windows/Fonts/malgun.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def concentration_chart(shares: dict[str, float]) -> None:
    im = Image.new("RGB", (1000, 470), "#ffffff")
    d = ImageDraw.Draw(im)
    title, body, small = font(26), font(20), font(15)
    d.text((55, 30), "Q4 행정동 지출: 상위 5개 동 집중도", fill="#17243a", font=title)
    d.text((55, 75), "각 지표별 상위 5개 동이 해당 지표 합계에서 차지하는 비중", fill="#566579", font=small)
    rows = [("전체 지출", shares["total"], "#2b6cb0"),
            ("여가·문화 지출", shares["leisure"], "#8558ad"),
            ("음식 지출", shares["food"], "#2c9672")]
    for i, (label, share, color) in enumerate(rows):
        y = 140 + i * 94
        d.text((55, y + 10), label, fill="#17243a", font=body)
        d.rounded_rectangle((240, y, 830, y + 42), radius=8, fill="#edf1f5")
        d.rounded_rectangle((240, y, 240 + 590 * share, y + 42), radius=8, fill=color)
        d.text((850, y + 8), f"{share:.1%}", fill="#17243a", font=body)
    d.text((55, 435), "지표마다 상위 5개 동의 구성은 다를 수 있음", fill="#64748b", font=small)
    im.save(FIGURES / "Q4_행정동_지출집중도.png")


def food_coffee_chart(frame: pd.DataFrame, rho: float) -> None:
    im = Image.new("RGB", (1100, 660), "#ffffff")
    d = ImageDraw.Draw(im)
    title, body, small = font(25), font(17), font(14)
    d.text((70, 25), "행정동 음식 지출과 커피·음료 상권 매출", fill="#17243a", font=title)
    d.text((70, 64), f"2025 Q4 · 커피 매출이 관측된 {len(frame)}개 동 · 스피어만 ρ={rho:.3f} · 원 크기=커피 점포 수", fill="#566579", font=small)
    left, right, top, bottom = 110, 1010, 115, 535
    d.rectangle((left, top, right, bottom), outline="#a9b8ca", width=2)
    x_values = frame["음식_지출_총금액"].map(lambda n: math.log10(n + 1))
    y_values = frame["coffee_sales"].map(lambda n: math.log10(n + 1))
    x_min, x_max = math.floor(x_values.min()), math.ceil(x_values.max())
    y_min, y_max = math.floor(y_values.min()), math.ceil(y_values.max())

    def xy(x: float, y: float) -> tuple[int, int]:
        px = left + (math.log10(x + 1) - x_min) / (x_max - x_min) * (right - left)
        py = bottom - (math.log10(y + 1) - y_min) / (y_max - y_min) * (bottom - top)
        return int(px), int(py)

    for exponent in range(x_min, x_max + 1):
        x, _ = xy(10 ** exponent, 10 ** y_min)
        d.line((x, top, x, bottom), fill="#edf1f5")
        d.text((x - 17, bottom + 8), f"10^{exponent}", fill="#64748b", font=small)
    for exponent in range(y_min, y_max + 1):
        _, y = xy(10 ** x_min, 10 ** exponent)
        d.line((left, y, right, y), fill="#edf1f5")
        d.text((48, y - 9), f"10^{exponent}", fill="#64748b", font=small)
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for row in frame.itertuples():
        x, y = xy(row.음식_지출_총금액, row.coffee_sales)
        radius = min(15, 3 + math.sqrt(row.coffee_shops) / 2)
        od.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(43, 108, 176, 110))
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(im)
    d.text((310, 575), "행정동 음식 지출 (원, 로그 눈금)", fill="#17243a", font=body)
    d.text((110, 610), "세로축: 해당 동에 연결된 상권의 커피·음료 추정매출 합계 (원, 로그 눈금)", fill="#566579", font=small)
    im.save(FIGURES / "Q4_행정동_음식지출_커피매출.png")


dong_area = read("OA-22160_영역_행정동.csv")
consumption = read("OA-22166_소비_행정동.csv")
dong_foot = read("OA-22178_길단위인구_행정동.csv")
dong_resident = read("OA-22183_상주인구_행정동.csv")
dong_worker = read("OA-22184_직장인구_행정동.csv")
trade_area = read("상권/OA-15560_영역_상권.csv")
trade_sales = read("상권/OA-15572_추정매출_상권.csv")
trade_stores = read("상권/OA-15577_점포_상권.csv")
trade_foot = read("상권/OA-15568_길단위인구_상권.csv")

assert dong_area["행정동_코드"].is_unique
assert trade_area["상권_코드"].is_unique
assert trade_area["행정동_코드"].isin(dong_area["행정동_코드"]).all()

consumption_q4 = q4(consumption)
dong = consumption_q4[["행정동_코드", "행정동_코드_명", "지출_총금액",
                       "음식_지출_총금액", "여가_문화_지출_총금액"]].copy()
for frame, column in ((dong_foot, "총_유동인구_수"),
                      (dong_resident, "총_상주인구_수"),
                      (dong_worker, "총_직장_인구_수")):
    dong = dong.merge(q4(frame)[["행정동_코드", column]], on="행정동_코드",
                      how="left", validate="one_to_one")

trade_area_counts = trade_area.groupby("행정동_코드")["상권_코드"].nunique().rename("trade_area_count")
dong = dong.merge(trade_area_counts, on="행정동_코드", how="left", validate="one_to_one")
keys = ["기준_년분기_코드", "상권_코드", "서비스_업종_코드"]
panel = q4(trade_sales).merge(
    q4(trade_stores)[keys + ["전체_점포_수", "폐업_점포_수"]], on=keys,
    validate="one_to_one",
).merge(
    trade_area[["상권_코드", "행정동_코드"]], on="상권_코드", validate="many_to_one",
).merge(
    q4(trade_foot)[["상권_코드", "총_유동인구_수"]], on="상권_코드",
    how="left", validate="many_to_one",
)
assert len(panel) == len(q4(trade_sales))
assert panel["행정동_코드"].notna().all()

dong_industry = panel.groupby(
    ["행정동_코드", "서비스_업종_코드", "서비스_업종_코드_명"], as_index=False
).agg(
    trade_sales=("당월_매출_금액", "sum"),
    trade_shops=("전체_점포_수", "sum"),
    trade_closures=("폐업_점포_수", "sum"),
    trade_areas=("상권_코드", "nunique"),
)
# Dong foot traffic is joined once per dong, after the industry aggregation.
# Summing the same foot-traffic row over industry rows would multiply it.
dong_industry = dong_industry.merge(
    dong[["행정동_코드", "음식_지출_총금액", "총_유동인구_수"]],
    on="행정동_코드", validate="many_to_one",
)

shares = {
    "total": consumption_q4["지출_총금액"].nlargest(5).sum() / consumption_q4["지출_총금액"].sum(),
    "leisure": consumption_q4["여가_문화_지출_총금액"].nlargest(5).sum() / consumption_q4["여가_문화_지출_총금액"].sum(),
    "food": consumption_q4["음식_지출_총금액"].nlargest(5).sum() / consumption_q4["음식_지출_총금액"].sum(),
}
concentration_chart(shares)

coffee = dong_industry.loc[dong_industry["서비스_업종_코드_명"] == "커피-음료"].rename(
    columns={"trade_sales": "coffee_sales", "trade_shops": "coffee_shops"}
)
coffee_rho = coffee[["음식_지출_총금액", "coffee_sales"]].corr(method="spearman").iloc[0, 1]
food_coffee_chart(coffee, coffee_rho)
coffee_dong = dong.merge(
    coffee[["행정동_코드", "coffee_sales", "coffee_shops"]],
    on="행정동_코드", how="left", validate="one_to_one",
)
food_q25, food_q75 = dong["음식_지출_총금액"].quantile([.25, .75])
selected = {}
trade_selected = {}
for name in ("한식음식점", "커피-음료", "호프-간이주점"):
    group = dong_industry.loc[dong_industry["서비스_업종_코드_명"] == name]
    trade_group = panel.loc[panel["서비스_업종_코드_명"] == name]
    selected[name] = {
        "dongs_with_sales": len(group),
        "median_shops_among_observed": round(group["trade_shops"].median(), 1),
        "food_spend_vs_sales_spearman": round(group[["음식_지출_총금액", "trade_sales"]].corr(method="spearman").iloc[0, 1], 4),
        "foot_vs_sales_spearman": round(group[["총_유동인구_수", "trade_sales"]].corr(method="spearman").iloc[0, 1], 4),
    }
    trade_selected[name] = {
        "trade_areas_with_sales": len(trade_group),
        "median_shops": round(trade_group["전체_점포_수"].median(), 1),
        "foot_missing": int(trade_group["총_유동인구_수"].isna().sum()),
        "foot_vs_sales_spearman": round(trade_group[["총_유동인구_수", "당월_매출_금액"]].corr(method="spearman").iloc[0, 1], 4),
        "shops_vs_sales_spearman": round(trade_group[["전체_점포_수", "당월_매출_금액"]].corr(method="spearman").iloc[0, 1], 4),
    }

top_total = consumption_q4.nlargest(5, "지출_총금액")
category_columns = [c for c in consumption_q4.columns if c.endswith("_지출_총금액")]
summary = {
    "source_rows": {"dong_area": len(dong_area), "consumption": len(consumption),
                    "dong_foot": len(dong_foot), "dong_resident": len(dong_resident),
                    "dong_worker": len(dong_worker)},
    "q4_dong": {"total": len(dong), "foot_available": int(dong["총_유동인구_수"].notna().sum()),
                "resident_available": int(dong["총_상주인구_수"].notna().sum()),
                "worker_available": int(dong["총_직장_인구_수"].notna().sum()),
                "trade_area_dongs": int(dong["trade_area_count"].notna().sum()),
                "total_spend_trillion_krw": round(dong["지출_총금액"].sum() / 1e12, 4),
                "median_total_spend_100m_krw": round(dong["지출_총금액"].median() / 1e8, 2),
                "food_spend_trillion_krw": round(dong["음식_지출_총금액"].sum() / 1e12, 4),
                "median_food_spend_100m_krw": round(dong["음식_지출_총금액"].median() / 1e8, 2),
                "leisure_share_of_total": round(dong["여가_문화_지출_총금액"].sum() / dong["지출_총금액"].sum(), 4),
                "food_share_of_total": round(dong["음식_지출_총금액"].sum() / dong["지출_총금액"].sum(), 4),
                "top5_shares": {k: round(v, 4) for k, v in shares.items()},
                "food_vs_foot_spearman": round(dong[["음식_지출_총금액", "총_유동인구_수"]].corr(method="spearman").iloc[0, 1], 4),
                "category_sum_mismatch_rows": int((consumption_q4[category_columns].sum(axis=1) != consumption_q4["지출_총금액"]).sum())},
    "top5_total_spend_dongs": [
        {"name": row["행정동_코드_명"], "total_trillion_krw": round(row["지출_총금액"] / 1e12, 3),
         "leisure_share": round(row["여가_문화_지출_총금액"] / row["지출_총금액"], 4)}
        for _, row in top_total.iterrows()
    ],
    "top5_food_spend_dongs": [
        {"name": row["행정동_코드_명"], "food_100m_krw": round(row["음식_지출_총금액"] / 1e8, 1)}
        for _, row in consumption_q4.nlargest(5, "음식_지출_총금액").iterrows()
    ],
    "q4_trade_panel": {"rows": len(panel), "trade_areas": panel["상권_코드"].nunique(),
                       "dongs_with_sales": panel["행정동_코드"].nunique(),
                       "dong_industry_rows": len(dong_industry),
                       "trade_foot_missing_rows": int(panel["총_유동인구_수"].isna().sum())},
    "industry_dong_examples": selected,
    "industry_trade_area_examples": trade_selected,
    "coffee_food_quartiles": {
        label: {"dongs": len(group), "coffee_sales_observed": int(group["coffee_sales"].notna().sum()),
                "median_shops_when_observed": round(group["coffee_shops"].median(), 1)}
        for label, group in (("low_food", coffee_dong.loc[coffee_dong["음식_지출_총금액"] <= food_q25]),
                             ("high_food", coffee_dong.loc[coffee_dong["음식_지출_총금액"] >= food_q75]))
    },
    "coffee": {"food_spend_vs_sales_spearman": round(coffee_rho, 4),
               "food_spend_vs_shops_spearman": round(coffee[["음식_지출_총금액", "coffee_shops"]].corr(method="spearman").iloc[0, 1], 4),
               "dongs_with_at_least_10_shops": int((coffee["coffee_shops"] >= 10).sum()),
               "median_sales_per_shop_krw_at_least_10": round((coffee.loc[coffee["coffee_shops"] >= 10, "coffee_sales"] /
                                                                 coffee.loc[coffee["coffee_shops"] >= 10, "coffee_shops"]).median())},
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
