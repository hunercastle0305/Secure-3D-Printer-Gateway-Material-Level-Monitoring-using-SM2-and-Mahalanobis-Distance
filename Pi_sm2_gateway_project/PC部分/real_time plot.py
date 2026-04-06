import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os

# 全局字体设置
plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文黑体
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

#  1. 系统参数配置
CSV_FILE = "3D_printer_resin_log.csv"  # 必须与监控脚本的文件名完全一致
THRESHOLD = 3.81  # 马氏距离告警红线
WINDOW_SIZE = 60  # 增加横向视野，显示最新一分钟的数据点

# 设定绘图风格
try:
    plt.style.use('ggplot')
except:
    pass

# 初始化监控仪表盘 (上下分屏)
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 7))
fig.suptitle('基于国密SM2的 3D打印机树脂槽余量安全监测中心', fontsize=16, fontweight='bold')


def animate(i):
    """高频刷新的前端渲染逻辑"""
    if not os.path.exists(CSV_FILE):
        return

    try:
        # 高效读取 CSV 尾部数据
        df = pd.read_csv(CSV_FILE)
        if df.empty or len(df) < 2:
            return

        df_plot = df.tail(WINDOW_SIZE)
        x = df_plot.index

        # 匹配 cloud_monitor.py 中的表头
        y_dist = df_plot['液面距离(cm)']
        y_md = df_plot['异常波动指数(MD)']

        # ==========================================
        # 仪表盘 1：物理量直接观测 (液面深度下降趋势)
        # ==========================================
        ax1.clear()
        ax1.plot(x, y_dist, label='超声波探头距液面距离 (cm)', color='#2980b9', linewidth=2, marker='o', markersize=4)
        ax1.set_title('【感知层】设备耗材余量实时动态 (距离越大说明树脂越少)', fontsize=11)
        ax1.set_ylabel('液面物理距离 (cm)', fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(loc='upper left')

        # ==========================================
        # 仪表盘 2：AI 算法隐性故障诊断
        # ==========================================
        ax2.clear()
        ax2.plot(x, y_md, label='系统状态波动指数 (MD)', color='#27ae60', linewidth=2)

        # 绘制工业告警红线
        ax2.axhline(y=THRESHOLD, color='#c0392b', linestyle='--', linewidth=2,
                    label=f'危急告警线 (Threshold={THRESHOLD})')

        # 发生异常时（如漏液），自动将图表对应区域染成警示红色
        ax2.fill_between(x, y_md, THRESHOLD, where=(y_md > THRESHOLD), color='#e74c3c', alpha=0.35)

        ax2.set_title('【分析层】基于马氏距离的非预期消耗告警 (防漏液/防探头污染)', fontsize=11)
        ax2.set_ylabel('马氏距离 MD', fontsize=10)
        ax2.set_xlabel('监控时序节点', fontsize=10)

        # 保证告警尖峰完整显示，动态调整 Y 轴上限
        max_md = y_md.max() if pd.notna(y_md.max()) else 0
        ax2.set_ylim(0, max(max_md + 1, THRESHOLD + 2))
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend(loc='upper left')

        # 优化版面间距
        plt.tight_layout()
        plt.subplots_adjust(top=0.90)

    except Exception as e:
        # 忽略由于同时读写 CSV 带来的偶发锁异常
        pass


# 2. 启动渲染引擎
ani = animation.FuncAnimation(fig, animate, interval=1000, save_count=100)
print(">>> 工业监控可视化大屏准备就绪，正在等待数据流注入...")
plt.show()