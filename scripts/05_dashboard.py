# -*- coding: utf-8 -*-
"""
05_dashboard.py 商业分析交互式大屏（Streamlit）
运行方式:  streamlit run D:\\商业数据分析大作业\\scripts\\05_dashboard.py
组件清单（>=6，全部联动 + 下钻）:
  1. 筛选器：年份范围  2. 筛选器：区域  3. 筛选器：重点关注国家
  4. KPI卡×4（含同比箭头）  5. 世界地图 choropleth（点击国家下钻）
  6. 趋势折线图  7. 区域结构饼图  8. 波士顿矩阵散点
  9. 相关热力图  10. 中国对全球增长贡献度  11. 明细数据表（支持下钻）
  + 主题切换：浅色·莫兰迪 / 暗色·莫兰迪
数据：世界银行 WDI（2005-2025，218个国家×6指标）
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="全球宏观经济商业分析大屏", layout="wide")

BASE = r"D:\商业数据分析大作业"

# ============ 莫兰迪统一色板（大屏与图表共用） ============
MORANDI = {
    "blue": "#8FA9C4", "pink": "#D4A5B8", "purple": "#B5A8C7",
    "sage": "#A3B5A6", "sand": "#C9B79C", "teal": "#8FAFAE",
    "taupe": "#BFB0A3", "navy": "#5B7A95", "rose": "#C07D8F", "mint": "#B7C9B9",
}
PALETTE = ["#8FA9C4", "#D4A5B8", "#B5A8C7", "#A3B5A6", "#C9B79C", "#8FAFAE", "#BFB0A3"]
BG_LIGHT, BG_DARK = "#F7F4F2", "#1B1E28"
PANEL_LIGHT, PANEL_DARK = "#FFFFFF", "#232734"

REGION_CN = {"East Asia & Pacific": "东亚与太平洋", "Europe & Central Asia": "欧洲与中亚",
             "Latin America & Caribbean": "拉美与加勒比", "Middle East & North Africa": "中东与北非",
             "North America": "北美", "South Asia": "南亚", "Sub-Saharan Africa": "撒哈拉以南非洲"}
FEAT = ["GDP_per_capita", "GDP_growth", "Inflation", "Unemployment", "Population", "Exports_pct_GDP"]
FEAT_CN = {"GDP_per_capita": "人均GDP(美元)", "GDP_growth": "GDP增速(%)", "Inflation": "通胀率(%)",
           "Unemployment": "失业率(%)", "Population": "总人口", "Exports_pct_GDP": "出口占GDP(%)"}


@st.cache_data
def load_data():
    df = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
    meta = pd.read_csv(BASE + r"\data\raw\Metadata_Country_API_NY.GDP.PCAP.CD_DS2_en_csv_v2_1529.csv")
    agg = set(meta.loc[meta["Region"].isna(), "Country Code"].dropna())
    df["is_country"] = ~df["Country Code"].isin(agg)
    meta["Region_cn"] = meta["Region"].map(REGION_CN)
    df = df.merge(meta[["Country Code", "Region_cn"]], on="Country Code", how="left")
    df["GDP_total_B"] = df["GDP_per_capita"] * df["Population"] / 1e9
    return df


def style(fig, dark, h=380, legend_h=False):
    """统一应用莫兰迪主题样式。"""
    fig.update_layout(template="plotly_dark" if dark else "plotly_white",
                      paper_bgcolor=(PANEL_DARK if dark else PANEL_LIGHT),
                      plot_bgcolor=(BG_DARK if dark else "#FAF7F4"),
                      height=h, font=dict(color="#E6E2DC" if dark else "#4A4A4A"))
    if legend_h:
        fig.update_layout(legend=dict(orientation="h", y=-0.25))
    return fig


df = load_data()

# ============ 主题切换（浅色/暗色·莫兰迪） ============
theme = st.sidebar.radio("主题风格", ["浅色·莫兰迪", "暗色·莫兰迪"], index=0)
dark = theme.startswith("暗色")
if dark:
    st.markdown("""
    <style>
    .stApp { background-color:#1B1E28; }
    [data-testid="stSidebar"] { background-color:#232734; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp { background-color:#F7F4F2; }</style>", unsafe_allow_html=True)

st.title("🌐 全球宏观经济与市场大盘分析大屏")
st.caption("数据源：世界银行 WDI 开放数据（data.worldbank.org，官方CSV下载）| 指标：人均GDP/增速/通胀/失业/人口/出口占比 | 2005-2025（2025年为世界银行最新年度数据）")

# ============ 侧边栏筛选器（组件1-3） ============
st.sidebar.header("筛选器（联动全局）")
yrs = st.sidebar.slider("① 年份范围", 2005, 2025, (2010, 2025))
all_regions = sorted(df["Region_cn"].dropna().unique())
sel_regions = st.sidebar.multiselect("② 区域", all_regions, default=all_regions)
all_countries = sorted(df[df["is_country"]]["Country Name"].dropna().unique())
sel_countries = st.sidebar.multiselect(
    "③ 重点关注国家", all_countries,
    default=["China", "United States", "India", "Germany", "Japan", "United Kingdom"])

d = df[(df["Year"] >= yrs[0]) & (df["Year"] <= yrs[1]) & (df["Region_cn"].isin(sel_regions))].copy()
if d.empty:
    st.warning("当前筛选条件下无数据，请调整筛选器。")
    st.stop()
last_year = d["Year"].max()
ly = d[d["Year"] == last_year]
py = d[d["Year"] == last_year - 1] if last_year > 2005 else pd.DataFrame()

# ============ KPI卡片（组件4，含同比箭头） ============
def kpi_delta(cur, prev, is_pp=False):
    if pd.isna(cur) or prev is None or pd.isna(prev) or prev == 0:
        return None
    return (cur - prev) if is_pp else (cur / prev - 1) * 100

w = ly[ly["Country Code"] == "WLD"]["GDP_total_B"]
k1 = w.values[0] if len(w) else ly["GDP_total_B"].sum()
k2 = d[d["is_country"]]["GDP_growth"].mean()
chn = ly[ly["Country Code"] == "CHN"]["GDP_growth"]
k3 = chn.values[0] if len(chn) else float("nan")
eap = ly[ly["Region_cn"] == "东亚与太平洋"]["GDP_total_B"].sum()
k4 = eap / ly["GDP_total_B"].sum() * 100 if ly["GDP_total_B"].sum() > 0 else float("nan")

p1 = py[py["Country Code"] == "WLD"]["GDP_total_B"]
pk1 = p1.values[0] if len(p1) else None
pk2 = py[py["is_country"]]["GDP_growth"].mean() if len(py) else None
pchn = py[py["Country Code"] == "CHN"]["GDP_growth"]
pk3 = pchn.values[0] if len(pchn) else None
peap = py[py["Region_cn"] == "东亚与太平洋"]["GDP_total_B"].sum()
pk4 = peap / py["GDP_total_B"].sum() * 100 if len(py) and py["GDP_total_B"].sum() > 0 else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("全球GDP总量（%d年，万亿美元）" % last_year, f"{k1/1000:.1f}" if pd.notna(k1) else "-",
          delta=f"{kpi_delta(k1, pk1):+.1f}%" if kpi_delta(k1, pk1) is not None else None,
          delta_color="normal")
c2.metric("区域平均GDP增速（%s-%d）" % (yrs[0], last_year), f"{k2:.2f}%" if pd.notna(k2) else "-",
          delta=f"{kpi_delta(k2, pk2, True):+.2f}pp" if kpi_delta(k2, pk2, True) is not None else None,
          delta_color="normal")
c3.metric("中国GDP增速（%d年）" % last_year, f"{k3:.2f}%" if pd.notna(k3) else "-",
          delta=f"{kpi_delta(k3, pk3, True):+.2f}pp" if kpi_delta(k3, pk3, True) is not None else None,
          delta_color="normal")
c4.metric("东亚太平洋GDP份额（%d年）" % last_year, f"{k4:.1f}%" if pd.notna(k4) else "-",
          delta=f"{kpi_delta(k4, pk4, True):+.2f}pp" if kpi_delta(k4, pk4, True) is not None else None,
          delta_color="normal")

# ============ 世界地图 choropleth（组件5，点击国家下钻） ============
st.subheader("世界人均GDP分布（%d年，点击国家下钻）" % last_year)
map_df = ly[ly["is_country"]].dropna(subset=["GDP_per_capita"]).copy()
map_df["人均GDP_log10"] = np.log10(map_df["GDP_per_capita"].clip(lower=1))
fig_map = px.choropleth(
    map_df, locations="Country Code", color="人均GDP_log10",
    hover_name="Country Name", custom_data=["Country Code"],
    color_continuous_scale=["#E9DDE0", "#B5A8C7", "#8FA9C4", "#5B7A95"],
    projection="natural earth",
    labels={"人均GDP_log10": "人均GDP(美元,对数)"})
fig_map.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False, showcountries=True,
                               countrycolor="#C9BCB0" if not dark else "#4A4A55"),
                      coloraxis_colorbar=dict(len=0.5, thickness=12))
style(fig_map, dark, h=430)
ev = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", key="map_sel", width="stretch")
sel_cc = None
try:
    pts = ev.selection.points
    if pts and pts[0].get("customdata"):
        sel_cc = pts[0]["customdata"][0]
except Exception:
    sel_cc = None

# ============ 中国对全球增长贡献度（组件10） ============
wld_g = ly[ly["Country Code"] == "WLD"]["GDP_growth"]
chn_g = ly[ly["Country Code"] == "CHN"]["GDP_growth"]
if len(wld_g) and len(chn_g) and pd.notna(wld_g.values[0]) and pd.notna(chn_g.values[0]) and wld_g.values[0] != 0:
    chn_share = (chn["GDP_total_B"].values[0] if len(chn) else 0) / (wld["GDP_total_B"].values[0] if len(w) else 1) * 100
    contrib_pp = chn_g.values[0] * chn_share / 100
    contrib_pct = contrib_pp / wld_g.values[0] * 100
    st.info(f"🌏 **中国对全球增长的贡献（{last_year}年）**：中国占全球GDP **{chn_share:.1f}%**，"
            f"以 **{chn_g.values[0]:.1f}%** 的增速拉动全球增长 **{contrib_pp:.2f} 个百分点**，"
            f"约占全球增长总量的 **{contrib_pct:.0f}%**。")

# ============ 趋势折线图（组件6） ============
st.subheader("GDP总量趋势（重点关注国家，十亿美元）")
sub = d[d["Country Name"].isin(sel_countries)].dropna(subset=["GDP_total_B"])
fig1 = px.line(sub, x="Year", y="GDP_total_B", color="Country Name", markers=True,
               color_discrete_sequence=PALETTE,
               labels={"Year": "年份", "GDP_total_B": "GDP总量（十亿美元）"})
style(fig1, dark, h=380, legend_h=True)
st.plotly_chart(fig1, width="stretch")

# ============ 区域结构饼图（组件7） ============
st.subheader("全球GDP区域结构（%d年）" % last_year)
reg_sum = ly.groupby("Region_cn")["GDP_total_B"].sum().reset_index()
reg_sum["占比%"] = (reg_sum["GDP_total_B"] / reg_sum["GDP_total_B"].sum() * 100).round(1)
fig2 = px.pie(reg_sum, names="Region_cn", values="GDP_total_B", hole=0.4,
              color_discrete_sequence=PALETTE)
style(fig2, dark, h=380, legend_h=True)
st.plotly_chart(fig2, width="stretch")

# ============ 波士顿矩阵散点（组件8） ============
st.subheader("波士顿矩阵：市场份额×增速（气泡=GDP规模，%d年）" % last_year)
grow = d[d["is_country"]].groupby("Country Code")["GDP_growth"].mean().rename("avg_growth")
bo = ly[ly["is_country"]].dropna(subset=["GDP_total_B"]).merge(grow, on="Country Code", how="left")
bo["share_pct"] = bo["GDP_total_B"] / bo["GDP_total_B"].sum() * 100
bo["重点"] = np.where(bo["Country Name"].isin(sel_countries), "重点国家", "其他")
bo = bo.dropna(subset=["avg_growth"])
if len(bo):
    fig3 = px.scatter(bo, x="avg_growth", y="share_pct", size="GDP_total_B",
                      color="重点", hover_name="Country Name", log_y=False,
                      color_discrete_map={"重点国家": MORANDI["rose"], "其他": MORANDI["taupe"]},
                      labels={"avg_growth": "平均GDP增速(%)", "share_pct": "全球GDP份额(%)"})
    style(fig3, dark, h=420)
    st.plotly_chart(fig3, width="stretch")

# ============ 相关热力图（组件9，莫兰迪发散色带） ============
st.subheader("指标相关矩阵（国家截面）")
corr = d[d["is_country"]][FEAT].corr()
fig4 = go.Figure(go.Heatmap(
    z=corr.values, x=[FEAT_CN[f] for f in FEAT], y=[FEAT_CN[f] for f in FEAT],
    zmin=-1, zmax=1,
    colorscale=[[0, "#D4A5B8"], [0.5, "#F4EEF1"], [1, "#8FA9C4"]],
    text=corr.round(2).values, texttemplate="%{text}",
    textfont=dict(color="#3D3D3D")))
style(fig4, dark, h=420)
st.plotly_chart(fig4, width="stretch")

# ============ 明细表（组件11，支持地图下钻） ============
st.subheader("国家×指标明细表（%d年，可按列排序/搜索）" % last_year)
tab = ly[ly["is_country"]].dropna(subset=["GDP_total_B"]).copy()
tab["GDP总量(十亿美元)"] = tab["GDP_total_B"].round(1)
tab["人均GDP(美元)"] = tab["GDP_per_capita"].round(0)
tab["GDP增速(%)"] = tab["GDP_growth"].round(2)
tab["通胀率(%)"] = tab["Inflation"].round(2)
tab["失业率(%)"] = tab["Unemployment"].round(2)
tab["出口占GDP(%)"] = tab["Exports_pct_GDP"].round(1)
show = tab[["Country Code", "Country Name", "Region_cn", "GDP总量(十亿美元)", "人均GDP(美元)",
            "GDP增速(%)", "通胀率(%)", "失业率(%)", "出口占GDP(%)"]]

cleared = st.button("✕ 清除下钻")
sel_name = None
if sel_cc and not cleared:
    sel_name = ly.loc[ly["Country Code"] == sel_cc, "Country Name"]
    sel_name = sel_name.values[0] if len(sel_name) else sel_cc
    st.success(f"已下钻到：**{sel_name}**（点击世界地图上的国家，明细表已联动）")
    show = show[show["Country Code"] == sel_cc]
elif cleared:
    st.caption("已清除下钻，显示全部国家。")

st.dataframe(show.sort_values("GDP总量(十亿美元)", ascending=False), width="stretch",
             column_config={"Country Name": "国家", "Country Code": "代码", "Region_cn": "区域"})
st.caption("联动说明：侧边栏筛选器驱动全部图表与KPI；点击世界地图任一国家可下钻明细表；"
           "波士顿矩阵气泡大小=GDP规模；KPI卡显示同比变化（△）。")
