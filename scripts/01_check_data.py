# -*- coding: utf-8 -*-
"""检查原始数据能否正常读取"""
import pandas as pd

RAW = r"D:\商业数据分析大作业\data\raw"
FILES = ["gdp_per_capita", "gdp_growth", "inflation", "unemployment", "population", "exports_gdp"]

for name in FILES:
    df = pd.read_csv(RAW + "\\" + name + ".csv", skiprows=4)
    print(f"{name}: 国家数={df.shape[0]}, 列数={df.shape[1]}, 年份范围={df.columns[4]}~{df.columns[-1]}")
print("全部读取成功")
