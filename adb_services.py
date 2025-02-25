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
import devices_action

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
    """在指定目录运行命令，并实时打印输出"""
    subprocess.Popen(command, cwd=directory, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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


def handle_device_setup(device_id, tcp_port, package_name, system_version):
    #print(f"Setting up device: {device_id} on port: {tcp_port}")
    """连接成功后执行设备的设置和性能测试"""
    target_device_id = f'host.docker.internal:{tcp_port}'
    connect_command = f'adb connect {target_device_id}'
    # disconnect_command = f'adb disconnect {device_id}'
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
    device_threads[target_device_id] = thread
    thread.start()

    # 插入设备信息到数据库
    db_operations = DatabaseOperations()
    device_name = "未知"
    if target_device_id.startswith("Q20"):
        if system_version == "13":
            device_name = "Q20降本"
        else:
            device_name = "Q20"
    elif target_device_id.startswith("S30"):
        device_name = "S30"
    elif target_device_id.startswith("P30"):
        device_name = "P30"

        

    try:
        db_operations.devices_info_insert(target_device_id, device_name, package_name, system_version)
    except Exception as db_e:
        print(db_e)
        print("devices_info插入数据库失败！！")

    # 执行 fps_run.py 文件，并将设备 ID 作为参数传递
    # 执行 fps_run.py 文件，并将设备 ID 作为参数传递
    if system_version == "13":
        py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "fps_run_android13.py")
    else:
        py_file = os.path.join(base_path, "mobileperf-master", "mobileperf", "android", "fps_run.py")
    py_file = py_file.replace('\r', '')  # 移除路径中的回车符
    thread_py = threading.Thread(target=run_command_in_directory, args=(f"python {py_file} {target_device_id}", sh_directory))
    threads.append(thread_py)
    thread_py.start()




@app.route('/api/report', methods=['POST'])
def report_connected():
    """报告设备信息并尝试连接"""
    data = request.json
    device_id = data.get('deviceId')
    tcp_port = data.get('tcpPort')
    system_version = data.get('systemVersion')
    memory_info = data.get('memoryInGB')
    package_list = data.get('packageList')
    # online_status = data.get('onlineStatus')
    #print(package_list)

    if device_id and tcp_port:
        print(f"接收到设备: {device_id}，端口: {tcp_port}")

        if device_id in connected_devices:
            return jsonify({"message": "设备已连接"}), 200

        connected_devices[device_id] = tcp_port

        # 尝试进行 adb 连接
        try:

            logging.info(f"成功连接设备 {device_id}，端口: {tcp_port}")
            time.sleep(2)
            # 判断设备型号
            if device_id.startswith("Q20"):
                if system_version == "13":
                    model = "Q20降本"
                else:
                    model = "Q20"
            elif device_id.startswith("S30"):
                model = "S30"
            elif device_id.startswith("Q10"):
                model = "Q10"
            elif device_id.startswith("P30"):
                model = "P30"
            else:
                model = "未知型号"
            # handle_device_setup(device_id, tcp_port)

            devices_details = {
                'device_id': device_id,
                'model': model,
                'system_version': system_version,
                'device_ram': memory_info,
                'device_status': 1,
                'tcp_port': tcp_port,
                'package_list' : package_list
            }

            # 实例化 DatabaseOperations 类
            db_operations = DatabaseOperations()
            # 调用 devices_details_insert 方法
            db_operations.devices_details_insert(devices_details)

            # 返回成功的响应
            return jsonify({"status": "success", "message": "设备数据处理成功"}), 200
        except Exception as e:
            print(f"执行 adb connect 时发生错误: {e}")
            return jsonify({"message": f"发生错误: {str(e)}"}), 500

    # return jsonify({"message": "无效请求"}), 400


def fKillProc(pid):
    """强制杀死进程"""
    print(f'尝试杀死进程 {pid}')
    killProc = f'kill -9 {pid}'
    killProcResult = subprocess.run(killProc, shell=True, capture_output=True, text=True)
    if killProcResult.returncode == 0:
        print(f'进程 {pid} 杀死成功')
    else:
        print(f'进程 {pid} 杀死失败: {killProcResult.stderr}')


def get_process_info(tcp_port):
    # 将 tcp_port 转换为字符串
    tcp_port_str = str(tcp_port)

    # 执行命令列出匹配"startup"的进程
    procStr = subprocess.run(f'ps aux | grep "[s]tartup"', shell=True, capture_output=True, text=True)

    # 解析每一行数据
    lines = procStr.stdout.strip().split('\n')
    results = []

    # 遍历每一行，检查是否包含匹配的 tcp_port
    for line in lines:
        if tcp_port_str in line:  # 仅考虑包含匹配 tcp_port 的行
            parts = line.split()  # 按空格拆分
            if len(parts) >= 2:
                pid = parts[1]  # 第二部分应该是 PID
                results.append(pid)

    return results  # 返回匹配 tcp_port 的 PID 列表


def clean_zombie_processes():
    """清除僵尸进程"""
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'status']):
        if proc.info['status'] == psutil.STATUS_ZOMBIE:
            ppid = proc.info['ppid']  # 获取僵尸进程的父进程ID
            try:
                # 尝试终止父进程
                os.kill(ppid, signal.SIGKILL)
                print(f"清除僵尸进程的父进程 PPID={ppid} (PID={proc.info['pid']})")
            except Exception as e:
                print(f"无法清除僵尸进程的父进程 PPID={ppid}：{e}")


@app.route('/api/disconnect', methods=['POST'])
def report_disconnect():
    data = request.json
    device_id = data.get('deviceId')
    tcp_port = data.get('tcpPort')

    devices_status = 0

    # del connected_devices[device_id]
    # print(f"设备 {device_id} 断开连接，端口: {tcp_port}")

    # 执行 ADB 命令断开设备连接
    try:

        devices_details = {
            'device_id': device_id,
            'device_status': devices_status
        }
        # 实例化 DatabaseOperations 类
        db_operations = DatabaseOperations()
        # 调用 devices_details_insert 方法
        db_operations.devices_details_insert(devices_details)

        # 获取与 tcp_port 匹配的进程信息
        pids = get_process_info(tcp_port)

        # 终止与 tcp_port 匹配的进程
        for pid in pids:
            try:
                subprocess.run(f'kill -9 {pid}', shell=True)
                print(f"已终止进程 PID={pid}，TCP端口为 {tcp_port}")

            except Exception as e:
                print(f"终止进程 PID={pid} 时出错: {e}")

        # 清除所有僵尸进程
        clean_zombie_processes()

        if tcp_port in connected_devices:
            del connected_devices[tcp_port]
            print(f"设备 {tcp_port} 已从连接设备中删除")
        else:
            print(f"设备 {tcp_port} 不在连接设备列表中")
        return jsonify({'message': f'设备 {tcp_port} 已成功断开'}), 200

    except Exception as e:
        logging.error(f"断开连接时发生错误: {e}")
        return jsonify({"message": "断开连接失败"}), 500


@app.route('/api/start_monkey', methods=['POST'])
def start_monkey():
    data = request.json
    device_id = data.get('deviceId')
    tcp_port = data.get('tcpPort')
    package_name = data.get('package_name')
    system_version = data.get('android_version')
    
    if device_id and tcp_port:
        print(f"接收到设备: {device_id}，端口: {tcp_port}, Android系统: {system_version}")

        if device_id in connected_devices:
            return jsonify({"message": "设备已连接"}), 200

        # connected_devices[device_id] = tcp_port

        # 尝试进行 adb 连接
        try:
            # connect_command = f'adb connect host.docker.internal:{tcp_port}'
            # connect_command = f'adb connect {device_id}'
            # result = subprocess.run(connect_command, shell=True, capture_output=True, text=True)

            logging.info(f"成功连接设备 {device_id}，端口: {tcp_port}, Android系统: {system_version}")
            time.sleep(2)

            #handle_device_setup(device_id, tcp_port)
            devices_action.handle_device_setup(device_id, tcp_port, package_name, system_version)

            # 返回成功的响应
            return jsonify({"status": "success", "message": "设备开始执行monkey脚本"}), 200


        except Exception as e:
            print(f"执行 adb connect 时发生错误: {e}")
            return jsonify({"message": f"发生错误: {str(e)}"}), 500


@app.route('/api/stop_monkey', methods=['POST'])
def stop_monkey():
    data = request.json
    device_id = data.get('deviceId')
    tcp_port = data.get('tcpPort')

    # 执行 ADB 命令断开设备连接
    try:
        disconnect_command = f'adb disconnect host.docker.internal:{tcp_port}'
        # disconnect_command = f'adb disconnect {device_id}'
        subprocess.run(disconnect_command, shell=True, capture_output=True, text=True)

        # 获取与 tcp_port 匹配的进程信息
        pids = get_process_info(tcp_port)

        # 终止与 tcp_port 匹配的进程
        for pid in pids:
            try:
                subprocess.run(f'kill -9 {pid}', shell=True)
                print(f"已终止进程 PID={pid}，TCP端口为 {tcp_port}")

            except Exception as e:
                print(f"终止进程 PID={pid} 时出错: {e}")

        # 清除所有僵尸进程
        clean_zombie_processes()

        if device_id in connected_devices:
            del connected_devices[device_id]
            print(f"设备 {device_id} 已从连接设备中删除")
        else:
            print(f"设备 {device_id} 不在连接设备列表中")
        return jsonify({'message': f'设备 {device_id} 已成功断开'}), 200

    except Exception as e:
        logging.error(f"断开连接时发生错误: {e}")
        return jsonify({"message": "断开连接失败"}), 500


if __name__ == '__main__':
    # logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.run(host='0.0.0.0', port=5100)
