# -*- coding: utf-8 -*-
"""
run_all.py 一键复现脚本
依次运行：数据检查 -> 合并清洗 -> EDA -> 商业模型分析
交互大屏（05_dashboard.py）需单独启动：streamlit run scripts\\05_dashboard.py
"""
import subprocess
import sys
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["01_check_data.py", "02_merge_clean.py", "03_eda.py", "04_models.py", "06_extra_charts.py"]


def main():
    print("项目根目录:", BASE)
    for name in SCRIPTS:
        print("=" * 60)
        print("运行:", name)
        t0 = time.time()
        r = subprocess.run([sys.executable, "-u", os.path.join(BASE, "scripts", name)], cwd=BASE)
        if r.returncode != 0:
            print("!! %s 运行失败，已终止。" % name)
            sys.exit(1)
        print("完成 %s，耗时 %.1f 秒" % (name, time.time() - t0))
    print("=" * 60)
    print("全部完成！")
    print("  - 分析图表: outputs/figures/")
    print("  - 分析表格: outputs/tables/")
    print("  - 交互大屏: streamlit run scripts\\05_dashboard.py")


if __name__ == "__main__":
    main()
