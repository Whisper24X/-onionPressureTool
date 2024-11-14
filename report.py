from pyecharts.charts import Line
from pyecharts import options as opts
from datetime import datetime
import pandas as pd

from pyecharts.charts import Bar

# 读取CSV文件
df = pd.read_csv('/Users/yangcong/PycharmProjects/Perf/R/_192.168.50.102:3333/results/com.yangcong345.android.phone/2024_04_03_17_06_38/cpuinfo.csv')

# 将日期时间列解析为datetime对象
df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H-%M-%S')

# 将pandas的Timestamp类型转换为datetime类型
df['datetime'] = df['datetime'].apply(lambda x: x.to_pydatetime())

# 创建折线图
line = (
    Line()
    .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df['datetime']])
    .add_yaxis("Device CPU Rate (%)", df['device_cpu_rate%'].tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Device CPU Rate Over Time"),
        xaxis_opts=opts.AxisOpts(type_="time"),
        yaxis_opts=opts.AxisOpts(type_="value"),
        legend_opts=opts.LegendOpts(is_show=True),
        toolbox_opts=opts.ToolboxOpts(is_show=True),
        datazoom_opts=opts.DataZoomOpts(),
    )
)

# 保存为HTML文件
line.render('output.html')

# 打开生成的HTML文件
import webbrowser
webbrowser.open('output.html')
