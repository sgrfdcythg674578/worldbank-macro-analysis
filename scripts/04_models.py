# -*- coding: utf-8 -*-
"""
04_models.py 商业分析模型（6个，对应评分标准2.2）
1) 同比分析（2024 vs 2023）
2) 结构占比变化（区域GDP份额 2005 vs 2024）
3) 帕累托/ABC 分类（国家GDP集中度）
4) 波士顿矩阵（份额×增速气泡，四象限）
5) K-Means 国家聚类（6指标）
6) SARIMA 预测（中国GDP增速，95%CI + 回测MAPE/RMSE）
每个模型输出1张业务图 + 结论（print）。
"""
import os
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import morandi
morandi.setup_matplotlib()
from morandi import MORANDI, PALETTE
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import statsmodels.api as sm

BASE = r"D:\商业数据分析大作业"
df = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
FIG = BASE + r"\outputs\figures"
TAB = BASE + r"\outputs\tables"
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

meta = pd.read_csv(BASE + r"\data\raw\Metadata_Country_API_NY.GDP.PCAP.CD_DS2_en_csv_v2_1529.csv")
agg_codes = set(meta.loc[meta["Region"].isna(), "Country Code"].dropna())
df["is_country"] = ~df["Country Code"].isin(agg_codes)
REGION_CN = {"East Asia & Pacific": "东亚与太平洋", "Europe & Central Asia": "欧洲与中亚",
             "Latin America & Caribbean": "拉美与加勒比", "Middle East & North Africa": "中东与北非",
             "North America": "北美", "South Asia": "南亚", "Sub-Saharan Africa": "撒哈拉以南非洲"}
meta["Region_cn"] = meta["Region"].map(REGION_CN)

df = df[(df["Year"] >= 2005) & (df["Year"] <= 2025)].copy()
df["GDP_total_B"] = df["GDP_per_capita"] * df["Population"] / 1e9

def save(fig, name):
    fig.savefig(FIG + "\\" + name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("已出图:", name)

print("=" * 60)
print("模型1：同比分析（2025 vs 2024 GDP总量增速）")
print("=" * 60)
y23 = df[(df["Year"] == 2024) & df["is_country"]][["Country Code", "GDP_total_B"]]
y24 = df[(df["Year"] == 2025) & df["is_country"]][["Country Code", "Country Name", "GDP_total_B"]]
yoy = y24.merge(y23, on="Country Code", suffixes=("_24", "_23"))
yoy["YoY_pct"] = (yoy["GDP_total_B_24"] - yoy["GDP_total_B_23"]) / yoy["GDP_total_B_23"] * 100
top = yoy.nlargest(15, "GDP_total_B_24")
fig, ax = plt.subplots(figsize=(8, 6))
top_sorted = top.sort_values("YoY_pct")
ax.barh(top_sorted["Country Name"], top_sorted["YoY_pct"], color=[MORANDI["blue"] if v >= 0 else MORANDI["pink"] for v in top_sorted["YoY_pct"]])
ax.axvline(0, color="gray", lw=0.8)
ax.set_title("主要经济体2025年GDP同比增速（%）")
ax.set_xlabel("同比增速（%）")
save(fig, "fig06_yoy_2025.png")
print("增速最高:", top.sort_values("YoY_pct", ascending=False).head(3)[["Country Name", "YoY_pct"]].round(1).to_string(index=False))
print("负增长:", top[top["YoY_pct"] < 0]["Country Name"].tolist())
yoy.to_csv(TAB + r"\yoy_2024.csv", index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print("模型2：结构占比变化（区域GDP份额 2005 vs 2025）")
print("=" * 60)
r05 = df[(df["Year"] == 2005) & df["is_country"]].merge(meta[["Country Code", "Region_cn"]], on="Country Code")
r24 = df[(df["Year"] == 2025) & df["is_country"]].merge(meta[["Country Code", "Region_cn"]], on="Country Code")
def region_share(d):
    s = d.groupby("Region_cn")["GDP_total_B"].sum().sort_values(ascending=False)
    return (s / s.sum() * 100).round(1)
share05, share24 = region_share(r05), region_share(r24)
regions = sorted(set(share05.index) | set(share24.index), key=lambda r: -share24.get(r, 0))
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(2); bottom = np.zeros(2)
for i, r in enumerate(regions):
    v = [share05.get(r, 0), share24.get(r, 0)]
    ax.bar(x, v, bottom=bottom, label=r, width=0.55, color=PALETTE[i % len(PALETTE)])
    bottom += v
ax.set_xticks(x); ax.set_xticklabels(["2005年", "2025年"])
ax.set_ylabel("全球GDP占比（%）"); ax.set_title("全球GDP区域结构变化（2005 vs 2025）")
ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
save(fig, "fig07_region_share.png")
share = pd.DataFrame({"2005_share": share05, "2025_share": share24}).fillna(0).round(1)
print(share.sort_values("2025_share", ascending=False).to_string())
share.to_csv(TAB + r"\region_share.csv", encoding="utf-8-sig")
print("东亚与太平洋份额变化: %.1f%% -> %.1f%%" % (share05.get("东亚与太平洋", 0), share24.get("东亚与太平洋", 0)))

print("\n" + "=" * 60)
print("模型3：帕累托/ABC（2025年GDP集中度）")
print("=" * 60)
g24 = y24.dropna(subset=["GDP_total_B"]).sort_values("GDP_total_B", ascending=False).reset_index(drop=True)
g24["cum_share"] = g24["GDP_total_B"].cumsum() / g24["GDP_total_B"].sum() * 100
g24["rank"] = np.arange(1, len(g24) + 1)
n80 = (g24["cum_share"] <= 80).sum()
n95 = (g24["cum_share"] <= 95).sum()
print(f"前{n80}个国家贡献80%的全球GDP；前{n95}个国家贡献95%")
g24["ABC"] = np.where(g24["cum_share"] <= 80, "A", np.where(g24["cum_share"] <= 95, "B", "C"))
abc = g24.groupby("ABC").agg(国家数=("Country Name", "count"), GDP占比=("cum_share", "max")).round(1)
print(abc.to_string())
fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(g24["rank"], g24["GDP_total_B"], width=0.8, color=MORANDI["blue"])
ax1.set_xlabel("国家排名（按GDP降序）"); ax1.set_ylabel("GDP总量（十亿美元）")
ax2 = ax1.twinx()
ax2.plot(g24["rank"], g24["cum_share"], color=MORANDI["rose"], marker="o", markersize=2, lw=1.5)
ax2.axhline(80, color="gray", ls="--", lw=0.8)
ax2.set_ylabel("累计占比（%）"); ax2.set_ylim(0, 105)
ax1.set_title("全球GDP帕累托图（2025）：市场集中度")
save(fig, "fig08_pareto.png")
g24.to_csv(TAB + r"\abc_2024.csv", index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print("模型4：波士顿矩阵（份额×增速）")
print("=" * 60)
growth = df[df["is_country"]].groupby("Country Code")["GDP_growth"].mean()
b = g24[g24["rank"] <= 60].copy()
b["share_pct"] = b["GDP_total_B"] / g24["GDP_total_B"].sum() * 100
b["avg_growth"] = b["Country Code"].map(growth)
b = b.dropna(subset=["avg_growth"])
med_s, med_g = b["share_pct"].median(), b["avg_growth"].median()
b["quadrant"] = np.where((b["share_pct"] >= med_s) & (b["avg_growth"] >= med_g), "明星",
                 np.where((b["share_pct"] >= med_s) & (b["avg_growth"] < med_g), "金牛",
                 np.where((b["share_pct"] < med_s) & (b["avg_growth"] >= med_g), "问题", "瘦狗")))
fig, ax = plt.subplots(figsize=(10, 7))
qc = {"明星": MORANDI["rose"], "金牛": MORANDI["blue"], "问题": MORANDI["purple"], "瘦狗": MORANDI["sage"]}
for q in qc:
    sub = b[b["quadrant"] == q]
    ax.scatter(sub["avg_growth"], sub["share_pct"], s=sub["GDP_total_B"] / 40, alpha=0.65,
               c=qc[q], label=f"{q}(n={len(sub)})")
for _, row in b.nlargest(12, "GDP_total_B").iterrows():
    ax.annotate(row["Country Name"], (row["avg_growth"], row["share_pct"]), fontsize=8,
                xytext=(2, 2), textcoords="offset points")
ax.axvline(med_g, color="gray", ls="--", lw=0.8); ax.axhline(med_s, color="gray", ls="--", lw=0.8)
ax.set_xlabel("平均GDP增速 2010-2025（%）"); ax.set_ylabel("2025年全球GDP份额（%）")
ax.set_title("波士顿矩阵：全球主要经济体（份额×增速）")
ax.legend()
save(fig, "fig09_boston_matrix.png")
for q in qc:
    names = b[b["quadrant"] == q].nlargest(5, "GDP_total_B")["Country Name"].tolist()
    print(f"  {q}: {'、'.join(names)}")
b.to_csv(TAB + r"\boston_top60.csv", index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print("模型5：K-Means 国家聚类（2025截面，6指标）")
print("=" * 60)
feat = ["GDP_per_capita", "GDP_growth", "Inflation", "Unemployment", "Population", "Exports_pct_GDP"]
cross = df[(df["Year"] == 2025) & df["is_country"]][["Country Code", "Country Name", "GDP_total_B"] + feat].dropna()
X = StandardScaler().fit_transform(cross[feat])
km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)
cross["cluster"] = km.labels_
pca = PCA(n_components=2, random_state=42)
xy = pca.fit_transform(X)
cross["pc1"], cross["pc2"] = xy[:, 0], xy[:, 1]
order = cross.groupby("cluster")["GDP_per_capita"].mean().sort_values(ascending=False).index
label_map = {c: f"集群{i+1}" for i, c in enumerate(order)}
cross["cluster_name"] = cross["cluster"].map(label_map)
fig, ax = plt.subplots(figsize=(9, 6))
for i, name in enumerate(sorted(cross["cluster_name"].unique())):
    sub = cross[cross["cluster_name"] == name]
    ax.scatter(sub["pc1"], sub["pc2"], label=name, alpha=0.75, s=22,
               color=PALETTE[i % len(PALETTE)], edgecolor="white", linewidths=0.5)
for _, row in cross.nlargest(14, "GDP_total_B").iterrows():
    ax.annotate(row["Country Name"], (row["pc1"], row["pc2"]), fontsize=8)
ax.set_xlabel("PC1（%.0f%%方差）" % (pca.explained_variance_ratio_[0] * 100))
ax.set_ylabel("PC2（%.0f%%方差）" % (pca.explained_variance_ratio_[1] * 100))
ax.set_title("K-Means 国家聚类（2025，K=3，PCA投影）")
ax.legend()
save(fig, "fig10_kmeans.png")
prof = cross.groupby("cluster_name")[feat].mean().round(1)
print(prof.to_string())
prof.to_csv(TAB + r"\cluster_profile.csv", encoding="utf-8-sig")
cross[["Country Code", "Country Name", "cluster_name"]].to_csv(TAB + r"\cluster_result.csv", index=False, encoding="utf-8-sig")
for name, row in prof.iterrows():
    topn = cross[cross["cluster_name"] == name].nlargest(6, "GDP_total_B")["Country Name"].tolist()
    print(f"  {name} 代表国家: {'、'.join(topn)}")

print("\n" + "=" * 60)
print("模型6：SARIMA 预测（中国GDP增速）")
print("=" * 60)
# 注意：SARIMA 需要完整历史序列，重新加载未收窄年份的干净数据
# 口径：中国1990年以来（改革开放后增速较稳定），数据截止2025，预测2026-2028
full = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
chn = full[(full["Country Code"] == "CHN") & (full["Year"] >= 1990) & (full["Year"] <= 2025)][["Year", "GDP_growth"]].dropna()
y = chn.set_index("Year")["GDP_growth"].astype(float)
print("中国GDP增速序列: %d~%d, n=%d" % (y.index.min(), y.index.max(), len(y)))
best, best_aic = None, np.inf
for p in range(3):
    for q in range(3):
        try:
            m = sm.tsa.SARIMAX(y, order=(p, 1, q), trend="c").fit(disp=False, maxiter=200)
            if m.aic < best_aic:
                best, best_aic = (p, q), m.aic
        except Exception:
            pass
print("AIC最优阶数: p=%d, q=%d, AIC=%.1f" % (best[0], best[1], best_aic))
# 回测：1990-2014拟合，预测2015-2019（避开疫情冲击，展示常态拟合能力）
train, test = y.loc[:2014], y.loc[2015:2019]
m_bt = sm.tsa.SARIMAX(train, order=(best[0], 1, best[1]), trend="c").fit(disp=False, maxiter=200)
fc_bt = m_bt.get_forecast(steps=len(test)).predicted_mean
mape = np.mean(np.abs((test.values - fc_bt.values) / test.values)) * 100
rmse = np.sqrt(np.mean((test.values - fc_bt.values) ** 2))
print("回测(2015-2019): MAPE=%.2f%%, RMSE=%.2f个百分点" % (mape, rmse))
# 全样本拟合 + 预测2025-2027
m_full = sm.tsa.SARIMAX(y, order=(best[0], 1, best[1]), trend="c").fit(disp=False, maxiter=200)
f = m_full.get_forecast(steps=3)
pred = f.predicted_mean; ci = f.conf_int()
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(y.index, y.values, color=MORANDI["navy"], label="实际增速")
ax.plot(fc_bt.index, fc_bt.values, color=MORANDI["sand"], ls="--", marker="o", ms=3, label="回测预测(2015-2019)")
ax.plot(pred.index, pred.values, color=MORANDI["rose"], marker="o", label="预测(2026-2028)")
ax.fill_between(pred.index, ci.iloc[:, 0], ci.iloc[:, 1], color=MORANDI["rose"], alpha=0.18, label="95%置信区间")
ax.axvline(2025.5, color="gray", ls=":", lw=0.8)
ax.set_title("中国GDP增速 SARIMA 预测（含95%置信区间）")
ax.set_xlabel("年份"); ax.set_ylabel("GDP增速（%）"); ax.legend()
save(fig, "fig11_sarima_forecast.png")
print("2026-2028预测（%）：")
for yr, v, lo, hi in zip(pred.index, pred.values, ci.iloc[:, 0], ci.iloc[:, 1]):
    print(f"  {yr}: 点预测 {v:.2f}  [95%CI: {lo:.2f} ~ {hi:.2f}]")
with open(TAB + r"\sarima_metrics.txt", "w", encoding="utf-8") as fh:
    fh.write(f"order=({best[0]},1,{best[1]}), AIC={best_aic:.1f}\nMAPE={mape:.2f}%, RMSE={rmse:.2f}\n")

print("\n" + "=" * 60)
print("补充：中国对全球GDP增长的贡献（2025）")
print("=" * 60)
wld = df[(df["Country Code"] == "WLD") & (df["Year"] == 2025)][["GDP_total_B", "GDP_growth"]].iloc[0]
chn = df[(df["Country Code"] == "CHN") & (df["Year"] == 2025)][["GDP_total_B", "GDP_growth"]].iloc[0]
chn_share = chn["GDP_total_B"] / wld["GDP_total_B"] * 100          # 中国占全球GDP比重
contrib_pp = chn["GDP_growth"] * chn_share / 100                   # 拉动全球增长（百分点）
contrib_pct = contrib_pp / wld["GDP_growth"] * 100 if wld["GDP_growth"] else np.nan  # 占全球增长的比重
print(f"中国GDP: {chn['GDP_total_B']:.0f} 十亿美元（增速 {chn['GDP_growth']:.2f}%）")
print(f"全球GDP: {wld['GDP_total_B']:.0f} 十亿美元（增速 {wld['GDP_growth']:.2f}%）")
print(f"中国占全球GDP比重: {chn_share:.1f}%")
print(f"中国拉动全球增长: {contrib_pp:.2f} 个百分点，约占全球增长的 {contrib_pct:.0f}%")
contri = pd.DataFrame({
    "指标": ["中国GDP(十亿美元)", "全球GDP(十亿美元)", "中国GDP增速(%)", "全球GDP增速(%)",
             "中国占全球GDP比重(%)", "中国拉动全球增长(百分点)", "占全球增长的比重(%)"],
    "2025": [chn["GDP_total_B"], wld["GDP_total_B"], chn["GDP_growth"], wld["GDP_growth"],
             chn_share, contrib_pp, contrib_pct]})
contri.to_csv(TAB + r"\china_contribution.csv", index=False, encoding="utf-8-sig")
print("已保存: china_contribution.csv")

print("\n=== 模型分析完成 ===")
