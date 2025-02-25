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
    """在指定目录执行命令"""
    try:
        # 使用 subprocess.Popen 而不是直接运行
        process = subprocess.Popen(
            command,
            cwd=directory,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return process
    except Exception as e:
        print(f"启动命令失败: {e}")
        return None

def handle_device_setup(device_id, tcp_port, package_name, system_version):
    """连接成功后执行设备的设置和性能测试"""
    target_device_id = device_id
    processes = []  # 存储启动的进程
    
    # ... (其他设置代码保持不变) ...

    # 执行 设备帧率卡顿检测
    py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "fps_run.py")
    print(f"FPS 脚本路径：{py_file}")
    py_file = py_file.replace('\r', '')
    fps_process = run_command_in_directory(f"python {py_file} {target_device_id}", sh_directory)
    if fps_process:
        processes.append(('fps', fps_process))

    # 执行 设备温度检测
    temp_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "temperature.py")
    print(f"温度监控脚本路径：{temp_file}")
    temp_file = temp_file.replace('\r', '')
    temp_process = run_command_in_directory(f"python {temp_file} {target_device_id}", sh_directory)
    if temp_process:
        processes.append(('temp', temp_process))

    return processes

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
    test_devices = [
        {
            'device_id': 'S30PQkRa0500702',
            'tcp_port': '5555',
            'package_name': 'com.yangcong345.cloud.ui.launcher',
            'system_version': '10'
        }
    ]

    all_processes = []  # 存储所有设备的进程

    try:
        # 运行测试设备
        for device in test_devices:
            print(f"\n开始设置设备: {device['device_id']}")
            processes = handle_device_setup(**device)
            all_processes.extend(processes)
            
        print("\n所有监控已启动，按 Ctrl+C 停止...")
        
        # 保持主进程运行并监控子进程
        while True:
            for name, process in all_processes:
                if process.poll() is not None:
                    print(f"{name} 进程已退出，返回码: {process.poll()}")
                    # 可以在这里重启进程
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n检测到Ctrl+C，正在停止所有监控...")
        # 停止所有进程
        for name, process in all_processes:
            if process.poll() is None:  # 如果进程还在运行
                print(f"正在停止 {name} 进程...")
                process.terminate()
                try:
                    process.wait(timeout=5)  # 等待进程结束
                except subprocess.TimeoutExpired:
                    process.kill()  # 如果进程没有及时结束，强制结束
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("监控已结束")