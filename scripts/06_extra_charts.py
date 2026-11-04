# -*- coding: utf-8 -*-
"""
06_extra_charts.py 补充宏观趋势图表（论文第5章 5.5 节）
产出:
  outputs/figures/fig12_inflation_trend.png      全球与中国、美国通胀率走势
  outputs/figures/fig13_unemployment_trend.png   全球与中国、美国失业率走势
  outputs/figures/fig14_china_share.png          中国GDP占全球比重走势
  outputs/figures/fig15_gdp_percapita_top10.png  2025年人均GDP前十国家
数据口径与 03_eda.py / 04_models.py 完全一致（2005-2025、真实国家、GDP总量=人均GDP×人口）。
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import morandi
morandi.setup_matplotlib()
from morandi import MORANDI

BASE = r"D:\商业数据分析大作业"
df = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
FIG = BASE + r"\outputs\figures"
os.makedirs(FIG, exist_ok=True)

df = df[(df["Year"] >= 2005) & (df["Year"] <= 2025)].copy()
df["GDP_total_B"] = df["GDP_per_capita"] * df["Population"] / 1e9


def save(fig, name):
    fig.savefig(FIG + "\\" + name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("已出图:", name)


# ---------- fig12 全球与中国、美国通胀率走势 ----------
piv = df[df["Country Code"].isin(["WLD", "CHN", "USA"])].pivot(
    index="Year", columns="Country Code", values="Inflation")
fig, ax = plt.subplots(figsize=(9, 5))
piv.plot(ax=ax, marker="o", markersize=3,
         color=[MORANDI["blue"], MORANDI["rose"], MORANDI["purple"]])
ax.set_title("全球与中国、美国通胀率走势（2005-2025）")
ax.set_xlabel("年份"); ax.set_ylabel("通胀率（%）")
ax.legend(["世界", "中国", "美国"])
save(fig, "fig12_inflation_trend.png")

# ---------- fig13 全球与中国、美国失业率走势 ----------
piv = df[df["Country Code"].isin(["WLD", "CHN", "USA"])].pivot(
    index="Year", columns="Country Code", values="Unemployment")
fig, ax = plt.subplots(figsize=(9, 5))
piv.plot(ax=ax, marker="o", markersize=3,
         color=[MORANDI["blue"], MORANDI["rose"], MORANDI["purple"]])
ax.set_title("全球与中国、美国失业率走势（2005-2025）")
ax.set_xlabel("年份"); ax.set_ylabel("失业率（%）")
ax.legend(["世界", "中国", "美国"])
save(fig, "fig13_unemployment_trend.png")

# ---------- fig14 中国GDP占全球比重走势 ----------
chn = df[df["Country Code"] == "CHN"].set_index("Year")["GDP_total_B"]
wld = df[df["Country Code"] == "WLD"].set_index("Year")["GDP_total_B"]
share = (chn / wld * 100).dropna()
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(share.index, share.values, color=MORANDI["rose"], marker="o", markersize=3, lw=2)
ax.fill_between(share.index, share.values, color=MORANDI["pink"], alpha=0.45)
v05, v25 = share.loc[2005], share.loc[2025]
ax.annotate("2005年 %.1f%%" % v05, (2005, v05), xytext=(2006, v05 - 2.6), fontsize=9)
ax.annotate("2025年 %.1f%%" % v25, (2025, v25), xytext=(2013, v25 + 1.2), fontsize=9)
ax.set_title("中国GDP占全球比重走势（2005-2025）")
ax.set_xlabel("年份"); ax.set_ylabel("占全球GDP比重（%）")
ax.set_ylim(0, share.max() + 4)
save(fig, "fig14_china_share.png")

# ---------- fig15 2025年人均GDP前十国家 ----------
meta = pd.read_csv(BASE + r"\data\raw\Metadata_Country_API_NY.GDP.PCAP.CD_DS2_en_csv_v2_1529.csv")
agg_codes = set(meta.loc[meta["Region"].isna(), "Country Code"].dropna())
g = df[(df["Year"] == 2025) & (~df["Country Code"].isin(agg_codes))].dropna(
    subset=["GDP_per_capita"])
top10 = g.nlargest(10, "GDP_per_capita").sort_values("GDP_per_capita")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top10["Country Name"], top10["GDP_per_capita"], color=MORANDI["blue"])
for i, v in enumerate(top10["GDP_per_capita"]):
    ax.text(v + 1500, i, "%.0f" % v, va="center", fontsize=8.5)
ax.set_title("2025年人均GDP前十国家（美元）")
ax.set_xlabel("人均GDP（美元）")
ax.set_xlim(0, top10["GDP_per_capita"].max() * 1.12)
save(fig, "fig15_gdp_percapita_top10.png")

print("\n=== 补充图表完成 ===")
