import subprocess
import shutil
import os
import threading
from uiautomator import Device
import time
import psutil
import re

def sanitize_device_id(device_id):
    # 将无效字符替换为下划线
    sanitized_id = re.sub(r'[^\w\-_]', '_', device_id)
    return sanitized_id

def run_command_in_directory(command, directory):
    subprocess.run(f"cd {directory} && {command}", shell=True)

# 创建一个线程列表用于存储每个sh文件的执行线程
threads = []

# 执行adb命令以获取已连接设备列表
adb_process = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, _ = adb_process.communicate()

# 解析输出，提取设备列表和计算设备数量
device_lines = output.decode().split('\n')[1:-2]  # 提取设备列表
device_count = len(device_lines)

# 动态获取基路径（假设脚本位于项目的根目录）
base_path = os.path.dirname(os.path.abspath(__file__))

source_mobileperf_folder = os.path.join(base_path, "mobileperf-master")  # 源MobilePerf文件夹路径
#print(source_mobileperf_folder)

# 遍历每个设备并执行相应操作
for device_line in device_lines:
    if "device" in device_line:
        device_id = device_line.split('\t')[0]
        print(f"已连接设备ID: {device_id}")

        target_device_id = sanitize_device_id(device_id)
        target_mobileperf_folder = os.path.join(base_path, "R", f"_{target_device_id}")  # 目标MobilePerf文件夹路径
        shutil.rmtree(target_mobileperf_folder, ignore_errors=True)  # 删除已存在的目标MobilePerf文件夹（如果存在的话）
        shutil.copytree(source_mobileperf_folder, target_mobileperf_folder)  # 复制源MobilePerf文件夹到目标MobilePerf文件夹
        print(f"MobilePerf文件夹 {source_mobileperf_folder} 已成功复制为 {target_mobileperf_folder}")  # 打印复制文件夹的信息

        config_file_path = os.path.join(target_mobileperf_folder, "config.conf")  # 配置文件路径
        # 打开配置文件，并进行相应的修改
        with open(config_file_path, 'r') as file:
            lines = file.readlines()
        with open(config_file_path, 'w') as file:
            for line in lines:
                if line.startswith("serialnum="):
                    file.write(f"serialnum={device_id}\n")
                elif line.startswith("monkey="):
                    file.write("# " + line)  # 注释掉原来的monkey命令
                    file.write("monkey=true\n")  # 写入修改后的monkey命令
                else:
                    file.write(line)

        # 执行mtklog start命令，并将其发送到后台
        # subprocess.run(["adb", "shell", "am", "start", "-n", "com.debug.loggerui/.MainActivity"])
        # d = Device()
        # time.sleep(2)  # 增加一些延迟以等待界面加载完成
        # # 点击指定元素
        # d(resourceId='com.debug.loggerui:id/startStopToggleButton').click()
        # time.sleep(2)  # 增加一些延迟以等待界面加载完成
        # # 将mtklog退到后台
        # subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])

        # 执行run.sh文件（假设run.sh位于MobilePerf目录中）
        sh_directory = os.path.join(base_path, "R", f"_{target_device_id}")
        #print(sh_directory)
        sh_file = f"run.sh"
        # 创建并启动一个新的线程来执行命令
        thread = threading.Thread(target=run_command_in_directory, args=(f"sh {sh_file}", sh_directory))
        threads.append(thread)
        thread.start()

        # 执行fps_run.py文件，并将设备ID作为参数传递
        py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "fps_run.py")
        # 创建并启动一个新的线程来执行命令
        thread_py = threading.Thread(target=run_command_in_directory, args=(f"python {py_file} {device_id}", sh_directory))
        threads.append(thread_py)
        thread_py.start()

# 等待所有线程执行完毕
for thread in threads:
    thread.join()
