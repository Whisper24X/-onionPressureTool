# -*- coding: utf-8 -*-

import logging
import time
import subprocess
import shutil
import os
import threading
from uiautomator import Device
import time
import psutil
import re
import platform
from flask import Flask, request, jsonify
import subprocess
import signal
import sys
import datetime
import app

# 使用 datetime.now() 来获取当前时间
current_time = datetime.datetime.now()
# 获取当前文件所在目录的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))

# 获取 mobileperf-master 目录的路径
mobileperf_dir = os.path.join(base_dir, 'mobileperf-master')

# 添加 mobileperf-master 目录到 sys.path
sys.path.append(mobileperf_dir)
# 检查路径和文件是否正确

from mobileperf.android.DB_utils import DatabaseOperations

# 创建一个线程列表用于存储每个sh文件的执行线程
threads = []

app = Flask(__name__)
# socketio = SocketIO(app)


connected_devices = {}
device_threads = {}


@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def sanitize_device_id(device_id):
    """将无效字符替换为下划线"""
    sanitized_id = re.sub(r'[^\w\-_]', '_', device_id)
    return sanitized_id


def run_command_in_directory(command, directory):
    """ Run command in a specific directory and capture output """
    result = subprocess.run(command, cwd=directory, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"stderr: {result.stderr}")
    else:
        print(f"stdout: {result.stdout}")


def get_connected_devices():
    adb_process = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = adb_process.communicate()
    device_lines = output.decode().split('\n')[1:-1]  # 提取设备列表
    devices = {}
    for line in device_lines:
        if '\tdevice' in line:
            device_id = line.split('\t')[0]
            devices[device_id] = f"host.docker.internal:{connected_devices.get(device_id)}"
    print(devices)
    return devices



target_device_id = 'Q203PRjRl0900926'
tcp_port = '1234'
connect_command = f'adb connect {target_device_id}'

subprocess.run(connect_command, shell=True, capture_output=True, text=True)

# 如果设备线程已存在且在运行，先停止旧线程
# if target_device_id in device_threads and device_threads[target_device_id].is_alive():
#     print(f"正在停止设备 {target_device_id} 的旧线程")
#     stop_events[target_device_id].set()  # 设置停止事件
#     device_threads[target_device_id].join()  # 等待线程停止

base_path = os.path.dirname(os.path.abspath(__file__))
source_mobileperf_folder = os.path.join(base_path, "mobileperf-master")

# 创建目标 MobilePerf 文件夹路径
target_mobileperf_folder = os.path.join(base_path, "R", f"_{sanitize_device_id(target_device_id)}")
shutil.rmtree(target_mobileperf_folder, ignore_errors=True)  # 删除已存在的目标文件夹
shutil.copytree(source_mobileperf_folder, target_mobileperf_folder)  # 复制源文件夹到目标文件夹
print(f"MobilePerf文件夹 {source_mobileperf_folder} 已成功复制为 {target_mobileperf_folder}")

# 修改配置文件
config_file_path = os.path.join(target_mobileperf_folder, "config.conf")
with open(config_file_path, 'r') as file:
    lines = file.readlines()
with open(config_file_path, 'w') as file:
    for line in lines:
        if line.startswith("serialnum="):
            file.write(f"serialnum={target_device_id}\n")
        elif line.startswith("monkey="):
            file.write("# " + line)  # 注释掉原来的monkey命令
            file.write("monkey=true\n")  # 写入修改后的monkey命令
        else:
            file.write(line)

sh_directory = os.path.join(base_path, "R", f"_{sanitize_device_id(target_device_id)}")
command = f"python3 mobileperf/android/startup.py {tcp_port}"  # Include tcp_port in the command
print(command)

# 创建并启动一个新的线程来执行命令并捕获输出
thread = threading.Thread(target=run_command_in_directory, args=(command, sh_directory))
# device_threads[target_device_id] = thread
# threads.append(thread)
thread.start()
thread.join()

# 插入设备信息到数据库
db_operations = DatabaseOperations()
device_name = "未知"
if target_device_id.startswith("S30"):
    device_name = "S30"
elif target_device_id.startswith("Q20"):
    device_name = "Q20"
elif target_device_id.startswith("P30"):
    device_name = "P30"

try:
    db_operations.devices_info_insert(target_device_id, device_name)
except Exception as db_e:
    print(db_e)
    print("devices_info插入数据库失败！！")

# 执行 fps_run.py 文件，并将设备 ID 作为参数传递
py_file = os.path.join(base_path, "mobileperf", "android", "fps_run.py")
py_file = py_file.replace('\r', '')  # 移除路径中的回车符
print(f"Running fps_run.py from: {py_file}")

thread_py = threading.Thread(target=run_command_in_directory,
                             args=(f"python {py_file} {target_device_id}", sh_directory))
#threads.append(thread_py)
thread_py.start()
thread_py.join()


