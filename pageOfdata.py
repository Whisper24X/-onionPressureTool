import streamlit as st
import pandas as pd
import glob
from plotly.subplots import make_subplots
from plotly import graph_objs as go
import time
# 加载CSV数据
@st.cache_resource
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

file_paths = glob.glob('/Users/yangcong/PycharmProjects/Perf/R/*/results/com.yangcong345.android.phone/*/cpuinfo.csv')

# 选择第一个匹配到的文件路径
selected_file_path = file_paths[0]

# 实时显示数据
st.subheader('CPU Utilization Real-time Line Chart')

chart = st.line_chart([])

# 模拟自动刷新
while True:
    new_data = load_data(selected_file_path)

    chart.add_trace(go.Scatter(x=new_data['datetime'], y=new_data['device_cpu_rate%'], mode='lines', name='CPU Utilization'))

    # 更新布局
    chart.update_layout(
        xaxis_title='Time',
        yaxis_title='Device CPU Rate',
        title='Device CPU Rate Over Time'
    )

    # 显示更新后的图表
    st.plotly_chart(chart, use_container_width=True)

    # 暂停5秒
    time.sleep(5)
