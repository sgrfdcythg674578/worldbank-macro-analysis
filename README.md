# 全球宏观经济与市场大盘分析（World Bank WDI，2005-2025）

《商业数据分析》期末大作业 —— 基于世界银行开放数据（WDI）的全球宏观经济商业分析。
全流程 Python 实现：数据清洗 → EDA → 6 种商业分析模型 → Streamlit 交互式大屏。

## 项目亮点

- **数据源**：世界银行 WDI 官方开放数据（data.worldbank.org，官方 CSV 下载，非爬虫）
- **样本**：218 个真实国家 × 6 项宏观指标 × 2005-2025 年（2025 年为世界银行最新年度数据，2026-10-08 更新）
- **模型**：同比分析 / 结构占比 / 帕累托-ABC / 波士顿矩阵 / K-Means 聚类 / SARIMA 时间序列预测
- **可视化**：15 张业务图表（统一莫兰迪配色）+ Streamlit 交互大屏截图（11 个组件，含世界地图 choropleth、国家下钻、暗色主题、KPI 同比箭头）

## 目录结构

```
├── data/
│   ├── raw/          # WDI 官方下载的 6 指标 CSV + 元数据（18 个文件）
│   └── clean/        # 合并清洗后的面板数据（17,556 行）
├── scripts/
│   ├── 01_check_data.py      # 数据检查
│   ├── 02_merge_clean.py     # 宽表转长表 + 多指标合并清洗
│   ├── 03_eda.py             # 探索性分析（fig01~fig05）
│   ├── 04_models.py          # 6 种商业模型（fig06~fig11 + 表格）
│   ├── 05_dashboard.py       # Streamlit 交互大屏
│   ├── 06_extra_charts.py    # 补充宏观趋势图（fig12-fig15）
│   └── morandi.py            # 莫兰迪统一配色模块
├── outputs/
│   ├── figures/      # 16 张图表（150dpi，fig01-fig16）
│   └── tables/       # 模型结果表（同比/区域份额/ABC/聚类/SARIMA 等）
├── requirements.txt
├── run_all.py        # 一键复现（01→06）
└── README.md
```

## 运行方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键复现全部分析（清洗→EDA→模型）
python run_all.py

# 3. 启动交互式大屏
streamlit run scripts/05_dashboard.py
```

## 指标说明

| 指标 | WDI 代码 | 含义 |
|---|---|---|
| 人均GDP | NY.GDP.PCAP.CD | 美元现价 |
| GDP增速 | NY.GDP.MKTP.KD.ZG | 年度同比 % |
| 通胀率 | FP.CPI.TOTL.ZG | 消费者物价指数年变动 % |
| 失业率 | SL.UEM.TOTL.ZS | 总劳动力占比 % |
| 总人口 | SP.POP.TOTL | 人 |
| 出口占GDP | NE.EXP.GNFS.ZS | % |

## 核心结论（2005-2025）

1. **GDP 格局**：2025 年美国 GDP 30.8 万亿美元、中国 19.5 万亿（增速 5.0%）、印度 3.96 万亿（增速 7.6%）
2. **结构变迁**：东亚太平洋区域 GDP 份额从 2005 年 21.3% 升至 2025 年 28.1%，欧洲中亚从 35.4% 降至 27.7%
3. **市场集中度**：前 18 个国家贡献全球 GDP 的 80%（A 类 18 / B 类 36 / C 类 132）
4. **聚类画像**：高收入发达（人均 6.3 万美元）/ 新兴波动（俄巴墨土印尼）/ 中印高增长（人均 8 千美元、增速 6.3%）
5. **SARIMA 预测**：中国 GDP 增速 2026-2028 年约 5.0%（95% 置信区间，回测 MAPE=18.5%）
6. **中国贡献度**：2025 年中国以 16.5% 的全球 GDP 比重、4.96% 的增速，拉动全球增长约 0.82 个百分点，占全球增长约 28%

## 大屏功能（05_dashboard.py）

- 侧边栏筛选器：年份范围 / 区域 / 重点关注国家（全局联动）
- 4 张 KPI 卡（含同比箭头）
- 世界地图 choropleth（人均 GDP，点击国家下钻明细表）
- GDP 趋势折线 / 区域结构饼图 / 波士顿矩阵散点 / 指标相关热力图
- 中国对全球增长贡献度洞察
- 浅色 / 暗色莫兰迪主题一键切换

## 图表索引（fig01–fig16）

| 图号 | 文件名 | 图表类型 | 说明/对应 |
|---|---|---|---|
| 图1 | fig01_gdp_total_trend.png | 折线趋势图 | GDP总量变化趋势 |
| 图2 | fig02_gdp_top10_2025.png | 条形对比图 | 2025年GDP前十 |
| 图3 | fig03_china_us_growth.png | 双线对比图 | 中美增速对比 |
| 图4 | fig04_corr_heatmap.png | 相关热力图 | 六指标相关性 |
| 图5 | fig05_gdp_per_capita_box.png | 箱线分布图 | 人均GDP分布 |
| 图6 | fig06_yoy_2025.png | 同比条形图 | 模型①同比分析 |
| 图7 | fig07_region_share.png | 环形结构图 | 模型②区域结构 |
| 图8 | fig08_pareto.png | 帕累托图 | 模型③帕累托-ABC |
| 图9 | fig09_boston_matrix.png | 四象限气泡图 | 模型④波士顿矩阵 |
| 图10 | fig10_kmeans.png | 聚类散点图 | 模型⑤K-Means |
| 图11 | fig11_sarima_forecast.png | 预测带折线图 | 模型⑥SARIMA |
| 图12 | fig12_inflation_trend.png | 多线趋势图 | 补充：全球与中美通胀率走势 |
| 图13 | fig13_unemployment_trend.png | 多线趋势图 | 补充：全球与中美失业率走势 |
| 图14 | fig14_china_share.png | 折线趋势图 | 补充：中国GDP占全球比重 |
| 图15 | fig15_gdp_percapita_top10.png | 条形对比图 | 补充：2025年人均GDP前十 |
| 图16 | fig16_dashboard.png | 交互大屏截图 | Streamlit大屏（地图下钻） |

## 分工说明

本作业由个人独立完成：数据获取、清洗治理、模型构建、图表与大屏实现、论文撰写全部由本人完成，AI 仅辅助编码与文本润色（详见论文"AI 使用披露"章节）。

## 合规说明

- 全部 Python 实现，无爬虫、无 BI 软件、无 Excel 截图
- 数据来源于世界银行官方开放数据（CC BY 4.0）
- 图表配色为自研莫兰迪色板（scripts/morandi.py），全局统一
