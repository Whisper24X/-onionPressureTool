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
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# 用于存储设备信息的字典
connected_devices = {}
device_threads = {}
device_processes = {}
startup_processes = {}  # 保存设备与startup进程的映射

import sys

# 获取当前文件所在目录的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))

# 获取 mobileperf-master 目录的路径
mobileperf_dir = os.path.join(base_dir, 'mobileperf-master')

# 添加 mobileperf-master 目录到 sys.path
sys.path.append(mobileperf_dir)

# 导入 DB_utils.py 中的某个函数
from mobileperf.android.DB_utils import DatabaseOperations

# 检测操作系统类型
is_windows = os.name == 'nt'
is_mac = platform.system() == 'Darwin'

# 创建一个线程列表用于存储每个sh文件的执行线程
threads = []

# 动态获取基路径（假设脚本位于项目的根目录）
base_path = os.path.dirname(os.path.abspath(__file__))
source_mobileperf_folder = os.path.join(base_path, "mobileperf-master")  # 源MobilePerf文件夹路径


# 获取所有当前的 startup 进程
def get_startup_processes():
    """获取当前运行的 startup 进程"""
    startup_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'python3' and 'startup.py' in proc.info['cmdline']:
            startup_processes.append(proc)
    return startup_processes


def sanitize_device_id(device_id):
    """将无效字符替换为下划线"""
    sanitized_id = re.sub(r'[^\w\-_]', '_', device_id)
    return sanitized_id


device_threads = {}
stop_events = {}  # 存储设备线程的停止事件


device_threads = {}
stop_event = {}  # 存储设备线程的停止事件
def run_command_in_directory(command, directory):
    """在指定目录执行命令并监听停止事件"""
    subprocess.Popen(command, cwd=directory, shell=True)

    # 循环监听 stop_event，直到收到停止信号
    # while not stop_event.is_set():
    #     retcode = process.poll()
    #     if retcode is not None:  # 如果进程已经结束，退出循环
    #         break
    #     stop_event.wait(1)  # 每秒检查一次
    #
    # # 如果 stop_event 被设置，终止子进程
    # if process.poll() is None:  # 如果进程还在运行
    #     print(f"停止命令：{command}")
    #     process.terminate()
    #     process.wait()

def handle_device_setup(device_id, tcp_port, package_name):
    """连接成功后执行设备的设置和性能测试"""
    target_device_id = f'host.docker.internal:{tcp_port}'
    # target_device_id = device_id
    connect_command = f'adb connect {target_device_id}'
    subprocess.run(connect_command, shell=True, capture_output=True, text=True)
    # 如果设备线程已存在且在运行，先停止旧线程
    if target_device_id in device_threads and device_threads[target_device_id].is_alive():
        print(f"正在停止设备 {target_device_id} 的旧线程")
        stop_events[target_device_id].set()  # 设置停止事件
        device_threads[target_device_id].join()  # 等待线程停止

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
            elif line.startswith("package="):  # 修改 package 字段
                file.write(f"package={package_name}\n")  # 使用传入的 package_name
            else:
                file.write(line)

    sh_directory = os.path.join(base_path, "R", f"_{sanitize_device_id(target_device_id)}")
    command = f"python3 mobileperf/android/startup.py {tcp_port}"
    #print(command)

    # 创建并启动一个新的线程来执行命令并捕获输出
    thread = threading.Thread(target=run_command_in_directory, args=(command, sh_directory))
    device_threads[target_device_id] = thread
    thread.start()

    # 插入设备信息到数据库
    db_operations = DatabaseOperations()
    device_name = "未知"
    if target_device_id.startswith("S30"):
        device_name = "S30"
    elif target_device_id.startswith("Q20"):
        device_name = "Q20"

    try:
        db_operations.devices_info_insert(target_device_id, device_name)
    except Exception as db_e:
        print(db_e)
        print("devices_info插入数据库失败！！")

    # 执行 设备帧率卡顿检测
    py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "fps_run.py")
    py_file = py_file.replace('\r', '')  # 移除路径中的回车符
    thread_py = threading.Thread(target=run_command_in_directory, args=(f"python {py_file} {target_device_id}", sh_directory))
    threads.append(thread_py)
    thread_py.start()

    # 执行 设备温度检测
    py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "temperature.py")
    py_file = py_file.replace('\r', '')  # 移除路径中的回车符
    thread_py = threading.Thread(target=run_command_in_directory,
                                 args=(f"python {py_file} {target_device_id}", sh_directory))
    threads.append(thread_py)
    thread_py.start()

# 等待所有线程执行完毕
for thread in threads:
    thread.join()



def get_process_info(command):
    # 执行命令
    procStr = subprocess.run(command, shell=True, capture_output=True, text=True)

    # 解析每一行数据
    lines = procStr.stdout.strip().split('\n')
    results = []

    for line in lines:
        if line:  # 确保行不为空
            parts = line.split()  # 按空格分割
            if len(parts) >= 2:  # 确保有足够的部分
                second_data = parts[1]  # 第二个数据
                last_data = parts[-1]  # 最后一个数据
                results.append((second_data, last_data))

    return results

def fKillProc(pid):
    """强制杀死进程"""
    killProc = f'kill -9 {pid}'
    killProcResult = subprocess.run(killProc, shell=True, capture_output=True, text=True)
    if killProcResult.returncode == 0:
        print(f'进程 {pid} 杀死成功')
    else:
        print(f'进程 {pid} 杀死失败: {killProcResult.stderr}')

@app.route('/api/devices_action', methods=['POST'])
def devices_action():
    """接收从axios发送的设备信息并处理"""
    data = request.get_json()
    device_id = data.get('deviceId')
    tcp_port = data.get('tcpPort')
    action = data.get('action')  # 新增 action 字段
    print(device_id, tcp_port, action)

    # if not device_id or not tcp_port:
    #     return jsonify({'error': '缺少 deviceId 或 tcpPort'}), 400

    if action == 'disconnect':
        # 在这里可以添加逻辑来处理设备断开，例如清除设备信息
        disconnect_command = f'adb disconnect host.docker.internal:{tcp_port}'
        subprocess.run(disconnect_command, shell=True, capture_output=True, text=True)

        psProc = 'ps aux | grep startup'
        process_info = get_process_info(psProc)
        logging.info(f'---------------------------------------------------------------------------------------------- 我到这里 ---------------------------------------------------------------------------------------- 我到这里')

        for second, last in process_info:
            logging.info(f'---------------------------------------------------------------------------------------------- {second} ---------------------------------------------------------------------------------------- {last}')
            if last == tcp_port:
                fKillProc(second)


        if device_id in connected_devices:
            del connected_devices[device_id]
            print(f"设备 {device_id} 已从连接设备中删除")
        else:
            print(f"设备 {device_id} 不在连接设备列表中")
        return jsonify({'message': f'设备 {device_id} 已成功断开'}), 200

    # 处理设备设置和性能测试
   # handle_device_setup(device_id, tcp_port)
    return jsonify({'message': f'设备 {device_id} 已成功设置并开始性能测试', 'tcpPort': tcp_port}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200)