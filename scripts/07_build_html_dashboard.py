# -*- coding: utf-8 -*-
"""
生成独立交互式大屏 dashboard.html（双击即可在浏览器打开，无需 Python）。
数据内嵌 + Plotly.js CDN；含侧边栏筛选、KPI、世界地图、折线/饼图/波士顿矩阵/热力图/明细表。
"""
import json
import os
import pandas as pd

BASE = r"D:\商业数据分析大作业"
OUT = BASE + r"\dashboard.html"

# 内嵌本地 Plotly 库（断网可用）
import plotly
PLOTLY_JS = open(os.path.join(os.path.dirname(plotly.__file__), "package_data", "plotly.min.js"),
                 encoding="utf-8").read().replace("</script", "<\\/script")

REGION_CN = {"East Asia & Pacific": "东亚与太平洋", "Europe & Central Asia": "欧洲与中亚",
             "Latin America & Caribbean": "拉美与加勒比", "Middle East & North Africa": "中东与北非",
             "North America": "北美", "South Asia": "南亚",
             "Sub-Saharan Africa": "撒哈拉以南非洲"}

df = pd.read_csv(BASE + r"\data\clean\worldbank_macro_clean.csv")
meta = pd.read_csv(BASE + r"\data\raw\Metadata_Country_API_NY.GDP.PCAP.CD_DS2_en_csv_v2_1529.csv")
agg = set(meta.loc[meta["Region"].isna(), "Country Code"].dropna())
df["is_country"] = ~df["Country Code"].isin(agg)
meta["Region_cn"] = meta["Region"].map(REGION_CN)
df = df.merge(meta[["Country Code", "Region_cn"]], on="Country Code", how="left")
df = df[(df["Year"] >= 2005) & (df["Year"] <= 2025)].copy()
df["GDP_total_B"] = (df["GDP_per_capita"] * df["Population"] / 1e9).round(3)

# 紧凑行格式: [name, code, year, region_cn, is_country, gdp_total_B, gdp_pc, growth, infl, unemp, pop, exp]
rows = []
for _, r in df.iterrows():
    rows.append([
        r["Country Name"], r["Country Code"], int(r["Year"]),
        r["Region_cn"] if pd.notna(r["Region_cn"]) else "",
        bool(r["is_country"]),
        None if pd.isna(r["GDP_total_B"]) else round(float(r["GDP_total_B"]), 3),
        None if pd.isna(r["GDP_per_capita"]) else round(float(r["GDP_per_capita"]), 1),
        None if pd.isna(r["GDP_growth"]) else round(float(r["GDP_growth"]), 2),
        None if pd.isna(r["Inflation"]) else round(float(r["Inflation"]), 2),
        None if pd.isna(r["Unemployment"]) else round(float(r["Unemployment"]), 2),
        None if pd.isna(r["Population"]) else int(r["Population"]),
        None if pd.isna(r["Exports_pct_GDP"]) else round(float(r["Exports_pct_GDP"]), 2),
    ])

DATA_JSON = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>全球宏观经济与市场大盘分析大屏</title>
<script>__PLOTLY_JS__</script>
<style>
  * { box-sizing: border-box; }
  body { margin:0; font-family:"Microsoft YaHei","PingFang SC",sans-serif; background:#F7F4F2; color:#4A4A4A; }
  .wrap { display:flex; min-height:100vh; }
  .side { width:260px; background:#FFFFFF; border-right:1px solid #E8E2DE; padding:18px; flex-shrink:0; }
  .main { flex:1; padding:20px 26px; }
  h1 { font-size:26px; margin:6px 0 4px; color:#3A3A3A; }
  .cap { color:#8A8080; font-size:12px; margin-bottom:16px; }
  .side h3 { font-size:14px; margin:16px 0 8px; color:#5B7A95; }
  .kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:16px; }
  .kpi { background:#fff; border-radius:10px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .kpi .lab { font-size:12px; color:#9A9090; }
  .kpi .val { font-size:26px; font-weight:700; color:#3A3A3A; margin-top:4px; }
  .kpi .d { font-size:12px; margin-top:4px; }
  .up { color:#5E8F6E; } .down { color:#C07D8F; }
  .panel { background:#fff; border-radius:10px; padding:12px 16px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .panel h3 { margin:6px 0 8px; font-size:15px; color:#5B5A5A; }
  .info { background:#EEF2F6; border-left:4px solid #8FA9C4; padding:10px 14px; border-radius:6px; margin-bottom:16px; font-size:14px; }
  table { border-collapse:collapse; width:100%; font-size:12px; }
  th,td { border:1px solid #EAE3DE; padding:5px 8px; text-align:right; }
  th { background:#F0EBE7; cursor:pointer; position:sticky; top:0; }
  th:hover { background:#E4DCD6; }
  td:first-child,th:first-child,td:nth-child(2),th:nth-child(2),td:nth-child(3),th:nth-child(3) { text-align:left; }
  .chk { max-height:180px; overflow:auto; font-size:13px; line-height:1.7; }
  .chk label { display:block; cursor:pointer; }
  input[type=range] { width:100%; }
  .rng { display:flex; justify-content:space-between; font-size:12px; color:#8A8080; }
</style>
</head>
<body>
<div class="wrap">
  <div class="side">
    <h3>筛选器（全局联动）</h3>
    <label style="font-size:13px">年份范围：<b id="yrLab"></b></label>
    <div style="margin:8px 0 2px">起 <input type="range" id="yr0" min="2005" max="2025" value="2010"></div>
    <div>止 <input type="range" id="yr1" min="2005" max="2025" value="2025"></div>
    <h3>区域</h3>
    <div class="chk" id="regionBox"></div>
    <h3>重点关注国家（折线图）</h3>
    <div class="chk" id="countryBox"></div>
    <p class="cap" style="margin-top:18px">世界银行WDI开放数据<br>2005–2025 · 莫兰迪配色</p>
  </div>
  <div class="main">
    <h1>🌐 全球宏观经济与市场大盘分析大屏</h1>
    <div class="cap">数据源：世界银行 WDI 开放数据（官方CSV下载）｜指标：人均GDP/增速/通胀/失业/人口/出口占比｜2005–2025（2025为最新年度）</div>
    <div class="kpis" id="kpis"></div>
    <div class="info" id="chnBox"></div>
    <div class="panel"><h3 id="mapTitle">世界人均GDP分布</h3><div id="map" style="height:430px"></div></div>
    <div class="panel"><h3>GDP总量趋势（重点国家，十亿美元）</h3><div id="line" style="height:380px"></div></div>
    <div class="panel"><h3 id="pieTitle">全球GDP区域结构</h3><div id="pie" style="height:360px"></div></div>
    <div class="panel"><h3 id="bosTitle">波士顿矩阵：市场份额 × 平均增速（气泡=GDP规模）</h3><div id="bos" style="height:420px"></div></div>
    <div class="panel"><h3>六指标相关矩阵（国家截面）</h3><div id="heat" style="height:420px"></div></div>
    <div class="panel"><h3 id="tabTitle">国家×指标明细表（点列头排序）</h3><div style="max-height:380px;overflow:auto" id="table"></div></div>
    <div class="cap">交互说明：左侧筛选器驱动全部图表与KPI；地图可悬停查看国家；表格点列头排序；折线/饼图/矩阵均可悬停查看数值。</div>
  </div>
</div>
<script>
const ROWS = __DATA__;
// 列: name,code,year,region,country,gdpTotalB,gdpPc,growth,inf,unemp,pop,exp
const PAL = ["#8FA9C4","#D4A5B8","#B5A8C7","#A3B5A6","#C9B79C","#8FAFAE","#BFB0A3","#C07D8F","#B7C9B9","#5B7A95"];
const FEATS = ["gdpPc","growth","inf","unemp","pop","exp"];
const FEAT_CN = ["人均GDP(美元)","GDP增速(%)","通胀率(%)","失业率(%)","总人口","出口占GDP(%)"];

function uniqRegions(){ return [...new Set(ROWS.filter(r=>r[4]&&r[3]).map(r=>r[3]))].sort(); }
function uniqCountries(){ return [...new Set(ROWS.filter(r=>r[4]).map(r=>r[0]))].sort(); }

const regionBox = document.getElementById("regionBox");
uniqRegions().forEach(r=>{
  const lab=document.createElement("label");
  lab.innerHTML=`<input type="checkbox" class="reg" value="${r}" checked> ${r}`;
  regionBox.appendChild(lab);
});
const countryBox=document.getElementById("countryBox");
const DEF=["China","United States","India","Germany","Japan","United Kingdom"];
uniqCountries().forEach(c=>{
  const lab=document.createElement("label");
  lab.innerHTML=`<input type="checkbox" class="cty" value="${c}" ${DEF.includes(c)?"checked":""}> ${c}`;
  countryBox.appendChild(lab);
});

function chosenRegions(){ return [...document.querySelectorAll(".reg:checked")].map(e=>e.value); }
function chosenCountries(){ return [...document.querySelectorAll(".cty:checked")].map(e=>e.value); }

function render(){
  const y0=+document.getElementById("yr0").value, y1=+document.getElementById("yr1").value;
  document.getElementById("yrLab").textContent = y0+"–"+y1;
  const regs=new Set(chosenRegions());
  let d = ROWS.filter(r=>r[2]>=y0&&r[2]<=y1 && (!r[4] || regs.has(r[3])));
  const lastY=Math.max(...d.map(r=>r[2]));
  const ly=d.filter(r=>r[2]===lastY);
  const py=d.filter(r=>r[2]===lastY-1);

  // KPI
  const wld=ly.find(r=>r[1]==="WLD");
  const wldPrev=py.find(r=>r[1]==="WLD");
  const avgG=d.filter(r=>r[4]&&r[7]!=null).reduce((s,r)=>s+r[7],0)/Math.max(1,d.filter(r=>r[4]&&r[7]!=null).length);
  const chn=ly.find(r=>r[1]==="CHN");
  const chnPrev=py.find(r=>r[1]==="CHN");
  const eap=ly.filter(r=>r[3]==="东亚与太平洋").reduce((s,r)=>s+(r[5]||0),0);
  const tot=ly.reduce((s,r)=>s+(r[5]||0),0);
  const peap=py.filter(r=>r[3]==="东亚与太平洋").reduce((s,r)=>s+(r[5]||0),0);
  const ptot=py.reduce((s,r)=>s+(r[5]||0),0);
  const kpis=[
    ["全球GDP总量（"+lastY+"年，万亿美元）", wld&&wld[5]!=null?(wld[5]/1000).toFixed(1):"-", wldPrev&&wldPrev[5]?(wld[5]/wldPrev[5]-1)*100:null, "%"],
    ["区域平均GDP增速（"+y0+"–"+lastY+"）", avgG.toFixed(2)+"%", null, ""],
    ["中国GDP增速（"+lastY+"年）", chn&&chn[7]!=null?chn[7].toFixed(2)+"%":"-", chnPrev&&chnPrev[7]!=null&&chn?chn[7]-chnPrev[7]:null, "pp"],
    ["东亚太平洋GDP份额（"+lastY+"年）", (eap/tot*100).toFixed(1)+"%", ptot?eap/tot*100-peap/ptot*100:null, "pp"]
  ];
  document.getElementById("kpis").innerHTML=kpis.map(k=>{
    let d="";
    if(k[2]!=null&&isFinite(k[2])){ const up=k[2]>=0; d=`<div class="d ${up?"up":"down"}">${up?"▲":"▼"} ${Math.abs(k[2]).toFixed(k[3]==="pp"?2:1)}${k[3]}</div>`; }
    return `<div class="kpi"><div class="lab">${k[0]}</div><div class="val">${k[1]}</div>${d}</div>`;
  }).join("");

  // 中国贡献
  if(wld&&chn&&wld[7]&&chn[5]!=null&&wld[5]&&wld[7]!==0){
    const share=chn[5]/wld[5]*100;
    const contrib=chn[7]*share/100;
    const pct=contrib/wld[7]*100;
    document.getElementById("chnBox").innerHTML=`🌏 <b>中国对全球增长的贡献（${lastY}年）</b>：中国占全球GDP <b>${share.toFixed(1)}%</b>，以 <b>${chn[7].toFixed(1)}%</b> 的增速拉动全球增长 <b>${contrib.toFixed(2)} 个百分点</b>，约占全球增长总量的 <b>${pct.toFixed(0)}%</b>。`;
  } else document.getElementById("chnBox").innerHTML="";

  // 地图
  document.getElementById("mapTitle").textContent="世界人均GDP分布（"+lastY+"年，悬停查看国家）";
  const mc=ly.filter(r=>r[4]&&r[6]!=null).map(r=>({location:r[1], z:Math.log10(Math.max(1,r[6])), name:r[0]}));
  Plotly.react("map",[{type:"choropleth", locationmode:"ISO-3", locations:mc.map(m=>m.location), z:mc.map(m=>m.z),
    text:mc.map(m=>m.name), hovertemplate:"%{text}<br>人均GDP: %{z:.2f}（对数）<extra></extra>",
    colorscale:[[0,"#E9DDE0"],[0.5,"#B5A8C7"],[0.8,"#8FA9C4"],[1,"#5B7A95"]], colorbar:{len:0.5, thickness:12}}],
    {geo:{projection:{type:"natural earth"}, bgcolor:"rgba(0,0,0,0)", showframe:false, countrycolor:"#C9BCB0"},
     margin:{l:0,r:0,t:10,b:0}, paper_bgcolor:"#fff"}, {responsive:true});

  // 折线
  const ctys=chosenCountries();
  const traces=ctys.map((c,i)=>{
    const rows=d.filter(r=>r[0]===c&&r[5]!=null).sort((a,b)=>a[2]-b[2]);
    return {x:rows.map(r=>r[2]), y:rows.map(r=>r[5]), mode:"lines+markers", name:c, line:{color:PAL[i%PAL.length]}};
  });
  Plotly.react("line",traces,{margin:{l:50,r:20,t:10,b:40},legend:{orientation:"h",y:-0.25},paper_bgcolor:"#fff",
    plot_bgcolor:"#FAF7F4", yaxis:{title:"GDP（十亿美元）"}, xaxis:{title:"年份"}},{responsive:true});

  // 饼
  const byReg={};
  ly.forEach(r=>{ if(r[4]&&r[5]!=null) byReg[r[3]]=(byReg[r[3]]||0)+r[5]; });
  document.getElementById("pieTitle").textContent="全球GDP区域结构（"+lastY+"年）";
  Plotly.react("pie",[{type:"pie", labels:Object.keys(byReg), values:Object.values(byReg), hole:0.4,
    marker:{colors:PAL}}],{margin:{l:10,r:10,t:10,b:10},legend:{orientation:"h",y:-0.1},paper_bgcolor:"#fff"},{responsive:true});

  // 波士顿矩阵
  const avgGMap={};
  d.filter(r=>r[4]&&r[7]!=null).forEach(r=>{ avgGMap[r[1]]=(avgGMap[r[1]]||[]); avgGMap[r[1]].push(r[7]); });
  Object.keys(avgGMap).forEach(k=>avgGMap[k]=avgGMap[k].reduce((a,b)=>a+b,0)/avgGMap[k].length);
  const bo=ly.filter(r=>r[4]&&r[5]!=null&&avgGMap[r[1]]!=null).map(r=>({
    x:avgGMap[r[1]], y:r[5]/tot*100, size:Math.max(5,r[5]/200), name:r[0],
    color:DEF.includes(r[0])?"#C07D8F":"#BFB0A3"}));
  document.getElementById("bosTitle").textContent="波士顿矩阵：市场份额 × 平均增速（气泡=GDP规模，"+lastY+"年）";
  Plotly.react("bos",[{type:"scatter", mode:"markers", x:bo.map(b=>b.x), y:bo.map(b=>b.y),
    text:bo.map(b=>b.name), marker:{size:bo.map(b=>b.size), color:bo.map(b=>b.color), opacity:0.75},
    hovertemplate:"%{text}<br>增速:%{x:.1f}% 份额:%{y:.2f}%<extra></extra>"}],
    {margin:{l:50,r:20,t:10,b:40},paper_bgcolor:"#fff",plot_bgcolor:"#FAF7F4",
     xaxis:{title:"平均GDP增速(%)"}, yaxis:{title:"全球GDP份额(%)",type:"log"}},{responsive:true});

  // 热力图
  const sub=d.filter(r=>r[4]);
  const corr=[];
  for(let i=0;i<6;i++){ const row=[]; for(let j=0;j<6;j++){
    const xs=sub.map(r=>r[5+i]), ys=sub.map(r=>r[5+j]);
    row.push(pearson(xs,ys)); } corr.push(row); }
  function pearson(a,b){ const n=a.length; let sx=0,sy=0,sxy=0,sxx=0,syy=0,c=0;
    for(let i=0;i<n;i++){ if(a[i]==null||b[i]==null) continue; sx+=a[i]; sy+=b[i]; sxy+=a[i]*b[i]; sxx+=a[i]*a[i]; syy+=b[i]*b[i]; c++; }
    if(c<2) return 0; const cov=sxy/c-sx/c*sy/c; return cov/(Math.sqrt(sxx/c-Math.pow(sx/c,2))*Math.sqrt(syy/c-Math.pow(sy/c,2))||1); }
  Plotly.react("heat",[{type:"heatmap", z:corr, x:FEAT_CN, y:FEAT_CN, zmin:-1, zmax:1,
    colorscale:[[0,"#D4A5B8"],[0.5,"#F4EEF1"],[1,"#8FA9C4"]],
    text:corr.map(r=>r.map(v=>v.toFixed(2))), texttemplate:"%{text}"}],
    {margin:{l:120,r:20,t:10,b:60},paper_bgcolor:"#fff"},{responsive:true});

  // 明细表
  document.getElementById("tabTitle").textContent="国家×指标明细表（"+lastY+"年，点列头排序）";
  const rowsT=ly.filter(r=>r[4]&&r[5]!=null).map(r=>[r[1],r[0],r[3],r[5].toFixed(1),r[6]?r[6].toFixed(0):"-",
    r[7]!=null?r[7].toFixed(2):"-",r[8]!=null?r[8].toFixed(2):"-",r[9]!=null?r[9].toFixed(2):"-",r[11]!=null?r[11].toFixed(1):"-"]);
  rowsT.sort((a,b)=>b[3]-a[3]);
  window._tabRows=rowsT; window._sortIdx=0; window._sortDesc=true;
  drawTable();
}

function drawTable(){
  const head=["代码","国家","区域","GDP总量(十亿$)","人均GDP($)","增速(%)","通胀(%)","失业(%)","出口/GDP(%)"];
  let h="<table><thead><tr>";
  head.forEach((h,i)=>h+=`<th data-i="${i}">${h}</th>`);
  h+="</tr></thead><tbody>";
  window._tabRows.forEach(r=>{ h+="<tr>"+r.map(c=>`<td>${c}</td>`).join("")+"</tr>"; });
  h+="</tbody></table>";
  document.getElementById("table").innerHTML=h;
  document.querySelectorAll("th").forEach(th=>th.onclick=()=>{
    const i=+th.dataset.i; window._sortDesc=(!window._sortIdx||window._sortIdx!==i)?true:!window._sortDesc;
    window._sortIdx=i;
    window._tabRows.sort((a,b)=>{ const x=parseFloat(a[i]),y=parseFloat(b[i]);
      if(isNaN(x)||isNaN(y)) return String(a[i]).localeCompare(String(b[i]));
      return window._sortDesc?y-x:x-y; });
    drawTable();
  });
}

["yr0","yr1"].forEach(id=>document.getElementById(id).oninput=render);
document.querySelectorAll(".reg,.cty").forEach(e=>e.onchange=render);
render();
</script>
</body>
</html>
"""

out_html = HTML.replace("__DATA__", DATA_JSON).replace("__PLOTLY_JS__", PLOTLY_JS)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out_html)
print("written:", OUT, "size_kb=", round(len(out_html)/1024))
