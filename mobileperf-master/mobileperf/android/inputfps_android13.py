from fpslis import IFpsListener
from datetime import datetime
import csv
import os
import glob


def get_config_value(file_path, key):
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip().startswith(key):
                return line.split('=')[1].strip()
    return None
class FpsListenserImpl(IFpsListener):
    def __init__(self):
        self.package = get_config_value("config.conf", "package")

    @staticmethod
    def get_parent_directory(path, levels=1):
        for _ in range(levels):
            path = os.path.dirname(path)
        return path

    def report_fps_info(self, fps_info, devices, pagename):
        print('\n')
        print("当前设备是：" + devices)
        print("当前进程是：" + str(fps_info.pkg_name))
        print("当前窗口是：" + str(fps_info.window_name))
        print("当前手机窗口刷新时间：" + str(fps_info.time))
        print("当前窗口fps是：" + str(fps_info.fps))
        print("当前2s获取总帧数：" + str(fps_info.total_frames))
        print("当前窗口丢帧数>16.67ms）是：" + str(fps_info.jankys_more_than_16))
        print(fps_info.jankys_ary)
        print("当前窗口卡顿数(>166.7ms)是：" + str(fps_info.jankys_more_than_166))
        print('\n')
        # 动态获取基路径（假设脚本位于项目的根目录）
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 获取上三级目录路径
        target_dir = FpsListenserImpl.get_parent_directory(base_path, levels=3)

        source_mobileperf_folder = os.path.join(target_dir)  # 源MobilePerf文件夹路径

        target_device_id = devices.replace(':', '_').replace('.', '_')
        file_path = os.path.join(source_mobileperf_folder, "R", f"_{target_device_id}", "results", pagename, "fps_data.csv")


        #file_path = f"/Users/yangcong/PycharmProjects/Perf/R/_{target_device_id}/results/com.yangcong345.android.phone/fps_data.csv"
        # 检查文件是否存在，如果不存在则写入标题

        # Check if file exists and is empty
        file_exists = os.path.isfile(file_path)
        is_empty = not file_exists or os.stat(file_path).st_size == 0

        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            if is_empty:
                writer.writerow(["datetime", "activity window", "fps", "jank"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H-%M-%S"),  # Assuming fps_info.time is a datetime object
                str(fps_info.pkg_name) + "/" + str(fps_info.window_name),
                # str(fps_info.fps),
                int(fps_info.fps),
                str(fps_info.jankys_more_than_166)
            ])
