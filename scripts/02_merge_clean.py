# -*- coding: utf-8 -*-
"""
02_merge_clean.py
将6个指标CSV合并为一张"国家×年份×6指标"长表，并完成基础清洗。
- 读取：跳过World Bank前4行元信息
- 清洗：丢弃空列、指标名冗余列；数值化；年份转int
- 输出：data/clean/worldbank_macro_clean.csv (UTF-8带BOM，Excel可直接打开)
"""
import os
import pandas as pd

RAW = r"D:\商业数据分析大作业\data\raw"
CLEAN_DIR = r"D:\商业数据分析大作业\data\clean"
os.makedirs(CLEAN_DIR, exist_ok=True)

# 文件名 -> 新列名（英文，方便后续代码引用）
FILES = {
    "gdp_per_capita": "GDP_per_capita",   # 人均GDP（现价美元）
    "gdp_growth": "GDP_growth",           # GDP增速（年%）
    "inflation": "Inflation",             # 通胀率（年%）
    "unemployment": "Unemployment",       # 失业率（占劳动力%）
    "population": "Population",           # 总人口
    "exports_gdp": "Exports_pct_GDP",     # 出口占GDP比重（%）
}

frames = []
for key, col in FILES.items():
    df = pd.read_csv(RAW + "\\" + key + ".csv", skiprows=4)
    # 丢弃读取时产生的空列（如行尾逗号造成的 Unnamed 列）
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df.drop(columns=["Indicator Name", "Indicator Code"], errors="ignore")
    # 宽表(国家×年份)转长表(国家、年份、指标值)
    long = df.melt(id_vars=["Country Name", "Country Code"], var_name="Year", value_name=col)
    long["Year"] = long["Year"].astype(int)
    long[col] = pd.to_numeric(long[col], errors="coerce")  # 空值转为 NaN
    frames.append(long)

# 按 国家+年份 逐指标外连接合并
merged = frames[0]
for f in frames[1:]:
    merged = merged.merge(f, on=["Country Name", "Country Code", "Year"], how="outer")

merged = merged.sort_values(["Country Code", "Year"]).reset_index(drop=True)

print("合并后总行数:", len(merged))
print("国家/地区数:", merged["Country Code"].nunique())
print("年份范围:", int(merged["Year"].min()), "~", int(merged["Year"].max()))
print("各指标缺失率(%):")
for c in FILES.values():
    print(f"  {c}: {merged[c].isna().mean()*100:.1f}")

out = CLEAN_DIR + "\\worldbank_macro_clean.csv"
merged.to_csv(out, index=False, encoding="utf-8-sig")
print("已保存:", out)
