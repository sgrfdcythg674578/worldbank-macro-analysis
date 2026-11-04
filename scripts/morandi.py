# -*- coding: utf-8 -*-
"""
morandi.py 莫兰迪统一配色与图表样式（全项目共用）
所有图表（EDA/模型/大屏）统一从这里取色，保证"配色协调统一"。
"""
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# 莫兰迪色板（低饱和、柔和）
MORANDI = {
    "blue":   "#8FA9C4",   # 雾蓝
    "pink":   "#D4A5B8",   # 豆沙粉
    "purple": "#B5A8C7",   # 雾紫
    "sage":   "#A3B5A6",   # 灰绿
    "sand":   "#C9B79C",   # 奶茶
    "teal":   "#8FAFAE",   # 灰青
    "taupe":  "#BFB0A3",   # 暖灰
    "navy":   "#5B7A95",   # 深雾蓝（强调/主色）
    "rose":   "#C07D8F",   # 深豆沙（强调/主色）
    "mint":   "#B7C9B9",   # 浅绿
}

# 标准系列循环顺序（按出现频率高的先排）
PALETTE = ["#8FA9C4", "#D4A5B8", "#B5A8C7", "#A3B5A6", "#C9B79C", "#8FAFAE", "#BFB0A3"]

# 软发散色带：豆沙粉 -> 米白 -> 雾蓝（用于相关热力图等）
DIVERGING = LinearSegmentedColormap.from_list(
    "morandi_div", ["#D4A5B8", "#F4EEF1", "#8FA9C4"])

# 软连续色带：浅粉 -> 雾紫 -> 雾蓝 -> 深雾蓝（用于地图/连续值）
SEQUENTIAL = ["#E9DDE0", "#B5A8C7", "#8FA9C4", "#5B7A95"]


def setup_matplotlib():
    """统一 matplotlib 样式：莫兰迪米白底、柔和网格、统一字体。"""
    mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["figure.facecolor"] = "white"
    mpl.rcParams["axes.facecolor"] = "#F7F4F2"
    mpl.rcParams["axes.edgecolor"] = "#C9BCB0"
    mpl.rcParams["axes.labelcolor"] = "#4A4A4A"
    mpl.rcParams["axes.titlecolor"] = "#3D3D3D"
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.color"] = "#E5DDD6"
    mpl.rcParams["grid.linewidth"] = 0.6
    mpl.rcParams["xtick.color"] = "#6B6B6B"
    mpl.rcParams["ytick.color"] = "#6B6B6B"
