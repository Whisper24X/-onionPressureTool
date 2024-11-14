import os
import pandas as pd
from pyecharts.charts import Line, Page
from pyecharts import options as opts
import glob
from apscheduler.schedulers.background import BackgroundScheduler
import webbrowser
running = True  # 设置一个标志来控制循环是否继续
# def visualize_csv_files():
#     directory = "/Users/yangcong/PycharmProjects/Perf/R/_192.168.50.102:3333/results/com.yangcong345.android.phone/"
#     pattern = f"{directory}*/cpuinfo.csv"
#     meminfo_pattern = f"{directory}*/meminfo.csv"
#     fps_pattern = f"{directory}*/fps.csv"
#
#     csv_files = glob.glob(pattern)
#     meminfo_files = glob.glob(meminfo_pattern)
#     fps_files = glob.glob(fps_pattern)
#     for csv_file, meminfo_file, fps_file in zip(csv_files, meminfo_files, fps_files):
#         output_directory = os.path.dirname(csv_file)
#         generate_html(csv_file, meminfo_file, fps_file, output_directory)





def generate_html(csv_file, meminfo_file, fps_file, output_directory):

    #print(csv_file)
    df = pd.read_csv(csv_file)
    df_meminfo = pd.read_csv(meminfo_file)
    df_fps = pd.read_csv(fps_file)
    # print(df)
    # print(df_meminfo)
    # print(df_fps)
    # Convert 'datetime' column to pandas Timestamp objects
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H-%M-%S')
    df['device_cpu_rate%'] = df['device_cpu_rate%'] / 8
    df['pid_cpu%'] = df['pid_cpu%'] / 8
    df_meminfo['datatime'] = pd.to_datetime(df_meminfo['datatime'], format='%Y-%m-%d %H-%M-%S')
    df_meminfo['pid_pss(MB)'] = df_meminfo['pid_pss(MB)'] / 6
    df_fps['datetime'] = pd.to_datetime(df_fps['datetime'], format='%Y-%m-%d %H-%M-%S')

    # 计算数据的平均值
    cpu_mean = df['device_cpu_rate%'].mean()
    cpu_pid_mean = df['pid_cpu%'].mean()
    meminfo_mean = df_meminfo['pid_pss(MB)'].mean()
    fps_mean = df_fps['fps'].mean()
    jank_mean = df_fps['jank'].mean()


    # Create the line chart
    line_cpu = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='white'))
        .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df['datetime']])
        .add_yaxis("CPU_设备占比率(%)", df['device_cpu_rate%'].tolist(), label_opts=opts.LabelOpts(is_show=False), symbol='none',markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(y=cpu_mean, name="Average CPU")]
        ), linestyle_opts=opts.LineStyleOpts(width=1))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="CPU_设备占比率"),
            xaxis_opts=opts.AxisOpts(type_="time"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(is_show=True),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),

        )
    )
    # Create the line chart
    line_cpu_pid = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='white'))
        .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df['datetime']])
        .add_yaxis("CPU_pid_进程cpu占比(%)", df['pid_cpu%'].tolist(), label_opts=opts.LabelOpts(is_show=False),
                   symbol='none', markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(y=cpu_pid_mean, name="Average CPU")]
            ))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="CPU_进程占比率"),
            xaxis_opts=opts.AxisOpts(type_="time"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(is_show=True),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),

        )
    )
    # Create the line chart
    line_meminfo = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='white'))
        .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df_meminfo['datatime']])
        .add_yaxis("pid_pss(MB)", df_meminfo['pid_pss(MB)'].tolist(), label_opts=opts.LabelOpts(is_show=False), symbol='none', markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(y=meminfo_mean, name="Average CPU")]
        ))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Meminfo_进程占用"),
            xaxis_opts=opts.AxisOpts(type_="time"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(is_show=True),
            toolbox_opts=opts.ToolboxOpts(),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross")
        )
    )
    # Create the line chart
    line_fps = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='white'))
        .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df_fps['datetime']])
        .add_yaxis("fps帧率", df_fps['fps'].tolist(), label_opts=opts.LabelOpts(is_show=False), symbol='none', markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(y=fps_mean, name="Average CPU")]
        ))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="FPS"),
            xaxis_opts=opts.AxisOpts(type_="time"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(is_show=True),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross")

        )
    )

    # Create the line chart
    line_jank = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='white'))
        .add_xaxis([d.strftime('%Y-%m-%d %H:%M:%S') for d in df_fps['datetime']])
        .add_yaxis("jank", df_fps['jank'].tolist(), label_opts=opts.LabelOpts(is_show=False), symbol='none',
                   markline_opts=opts.MarkLineOpts(
                       data=[opts.MarkLineItem(y=jank_mean, name="Average CPU")]
                   ))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Jank_卡顿"),
            xaxis_opts=opts.AxisOpts(type_="time"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(is_show=True),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross")

        )
    )
    # Combine the charts into one page
    page = Page()
    page.add(line_cpu)
    page.add(line_cpu_pid)
    page.add(line_meminfo)
    page.add(line_fps)
    page.add(line_jank)

    # Save as HTML file
    output_file = os.path.join(output_directory, "report.html")
    page.render(output_file)



# def visualize_csv_files():
#     directory = "/Users/yangcong/PycharmProjects/Perf/R/"
#     folders = [f.path for f in os.scandir(directory) if f.is_dir()]
#     #print(folders)
#     for folder in folders:
#         pattern = f"{folder}/results/com.yangcong345.android.phone/*/cpuinfo.csv"
#         meminfo_pattern = f"{folder}/results/com.yangcong345.android.phone/*/meminfo.csv"
#         fps_pattern = f"{folder}/results/com.yangcong345.android.phone/*/fps.csv"
#         #print(pattern)
#         csv_files = glob.glob(pattern)
#         meminfo_files = glob.glob(meminfo_pattern)
#         fps_files = glob.glob(fps_pattern)
#         # print(f"Folder: {folder}")
#         # print(f"csv_files: {csv_files}")
#         # print(f"meminfo_files: {meminfo_files}")
#         # print(f"fps_files: {fps_files}")
#         if csv_files:  # Check if csv_files is not empty
#             for csv_file, meminfo_file, fps_file in zip(csv_files, meminfo_files, fps_files):
#                 output_directory = os.path.dirname(csv_file)
#                 generate_html(csv_file, meminfo_file, fps_file, output_directory)
def visualize_csv_files():
    dir = r"C:\Users\yangcong\PycharmProjects\Perf\R"
    folders = [f.path for f in os.scandir(dir) if f.is_dir()]
    for folder in folders:
        pattern = rf"{folder}\results\com.yangcong345.android.phone\*\cpuinfo.csv"
        meminfo_pattern = rf"{folder}\results\com.yangcong345.android.phone\*\meminfo.csv"
        fps_pattern = rf"{folder}\results\com.yangcong345.android.phone\fps_data.csv"

        csv_files = glob.glob(pattern)
        meminfo_files = glob.glob(meminfo_pattern)
        fps_files = glob.glob(fps_pattern)
        #print(meminfo_files)
        if csv_files:
            #print("当前文件夹路径:", folder)  # 添加这行来打印当前文件夹的路径
            for csv_file, meminfo_file, fps_file in zip(csv_files, meminfo_files, fps_files):
                #print("CSV 文件路径:", csv_file)  # 添加这行来打印 CSV 文件的路径
                output_directory = os.path.dirname(csv_file)
                print(output_directory)
                generate_html(csv_file, meminfo_file, fps_file, output_directory)


def job():

    visualize_csv_files()
    if not running:  # 如果标志为 False，则停止调度器
        scheduler.shutdown()

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'interval', seconds=2)
    scheduler.start()

    job()  # 初始执行一次 job 函数，以便立即生成图表

    # 模拟程序运行，设置一个条件来终止循环
    input("Press Enter to stop refreshing: ")
    running = False
