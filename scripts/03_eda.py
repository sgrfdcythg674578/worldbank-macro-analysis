# -*- coding: utf-8 -*-
"""
03_eda.py 探索性分析(EDA) + 确定分析口径
产出:
  outputs/figures/fig01~fig05 第一批图表
  outputs/tables/ 汇总表
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import morandi
morandi.setup_matplotlib()
from morandi import MORANDI, DIVERGING

BASE = r"D:\商业数据分析大作业"
df = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
FIG = BASE + r"\outputs\figures"
TAB = BASE + r"\outputs\tables"
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)
print("原始大表:", df.shape)

# ============ 口径1：年份窗口收窄到近20年 ============
df = df[(df["Year"] >= 2005) & (df["Year"] <= 2025)].copy()
print("\n收窄到2005-2025后:", df.shape)
print("各指标缺失率(%):")
MISS = ["GDP_per_capita", "GDP_growth", "Inflation", "Unemployment", "Population", "Exports_pct_GDP"]
for c in MISS:
    print(f"  {c}: {df[c].isna().mean()*100:.1f}")

# ============ 口径2：区分"真实国家"与"地区聚合"(World/大洲/收入组) ============
meta = pd.read_csv(BASE + r"\data\raw\Metadata_Country_API_NY.GDP.PCAP.CD_DS2_en_csv_v2_1529.csv")
agg_codes = set(meta.loc[meta["Region"].isna(), "Country Code"].dropna())
df["is_country"] = ~df["Country Code"].isin(agg_codes)
n_country = df.loc[df["is_country"], "Country Code"].nunique()
print(f"\n真实国家数: {n_country}（另有 {df['Country Code'].nunique()-n_country} 个聚合体：World/大洲/收入组）")

# ============ 派生指标：GDP总量（十亿美元）= 人均GDP × 人口 ============
df["GDP_total_B"] = df["GDP_per_capita"] * df["Population"] / 1e9

# ============ 关键发现1：最新年GDP规模Top15 ============
top = (df[(df["Year"] == 2025) & df["is_country"]]
       .dropna(subset=["GDP_total_B"]).nlargest(15, "GDP_total_B"))
print("\n2025年GDP总量Top15（十亿美元）:")
print(top[["Country Name", "GDP_total_B", "GDP_growth"]].round(1).to_string(index=False))
top.to_csv(TAB + r"\top15_gdp_2025.csv", index=False, encoding="utf-8-sig")

# ============ 关键发现2：2005-2025 中美 vs 世界增速均值 ============
g = df[(df["is_country"]) & (df["Country Code"].isin(["CHN", "USA"])) | (df["Country Code"] == "WLD")]
g = g[["Country Code", "Year", "GDP_growth"]].dropna()
avg_growth = g.groupby("Country Code")["GDP_growth"].mean().round(2)
print("\n2005-2025平均GDP增速(%):")
print(avg_growth.to_string())

# ============ 关键发现3：指标相关矩阵 ============
corr = df[df["is_country"]][MISS].corr()
print("\n指标相关系数矩阵:")
print(corr.round(2).to_string())
corr.round(3).to_csv(TAB + r"\corr_matrix.csv", encoding="utf-8-sig")

# ============ 图表 ============
def save(fig, name):
    fig.savefig(FIG + "\\" + name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("已出图:", name)

# fig01 全球+中美GDP总量趋势（折线=模板）
piv = df[df["Country Code"].isin(["WLD", "CHN", "USA"])].pivot(index="Year", columns="Country Code", values="GDP_total_B")
fig, ax = plt.subplots(figsize=(9, 5))
piv.plot(ax=ax, marker="o", markersize=3, color=[MORANDI["blue"], MORANDI["rose"], MORANDI["purple"]])
ax.set_title("全球与中国、美国GDP总量趋势（2005-2025）")
ax.set_xlabel("年份"); ax.set_ylabel("GDP总量（十亿美元）")
ax.legend(["世界", "中国", "美国"])
save(fig, "fig01_gdp_total_trend.png")

# fig02 2024 GDP Top10（横向柱状=模板）
top10 = top.head(10).sort_values("GDP_total_B")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top10["Country Name"], top10["GDP_total_B"], color=MORANDI["blue"])
ax.set_title("2025年GDP总量Top10国家")
ax.set_xlabel("GDP总量（十亿美元）")
save(fig, "fig02_gdp_top10_2025.png")

# fig03 中美GDP增速对比（折线）
piv2 = df[df["Country Code"].isin(["CHN", "USA"])].pivot(index="Year", columns="Country Code", values="GDP_growth")
fig, ax = plt.subplots(figsize=(9, 5))
piv2.plot(ax=ax, marker="o", markersize=3, color=[MORANDI["rose"], MORANDI["blue"]])
ax.set_title("中国 vs 美国 GDP增速（2005-2025）")
ax.set_xlabel("年份"); ax.set_ylabel("GDP增速（%）")
ax.legend(["中国", "美国"])
save(fig, "fig03_china_us_growth.png")

# fig04 指标相关矩阵热力图（热力图=模板）
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr.values, cmap=DIVERGING, vmin=-1, vmax=1)
ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns)
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center", fontsize=8)
ax.set_title("宏观经济指标相关系数矩阵（2005-2025）")
fig.colorbar(im, shrink=0.8)
save(fig, "fig04_corr_heatmap.png")

# fig05 人均GDP分布（箱线图=模板，2025年）
gdp_latest = df[(df["Year"] == 2025) & df["is_country"]]["GDP_per_capita"].dropna()
fig, ax = plt.subplots(figsize=(7, 5))
box = ax.boxplot(gdp_latest, orientation="vertical", patch_artist=True,
                 boxprops=dict(facecolor=MORANDI["purple"], edgecolor=MORANDI["navy"]),
                 medianprops=dict(color=MORANDI["navy"], lw=1.5),
                 whiskerprops=dict(color=MORANDI["navy"]),
                 capprops=dict(color=MORANDI["navy"]))
ax.set_xticks([1]); ax.set_xticklabels(["2025年人均GDP（美元）"])
ax.set_title("全球国家人均GDP分布（2025，n=%d）" % len(gdp_latest))
save(fig, "fig05_gdp_per_capita_box.png")

print("\n=== EDA 完成 ===")
