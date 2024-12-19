import logging
import time
import subprocess
import shutil
import os
import threading
import re
import platform
from flask import Flask, request, jsonify
import subprocess
import signal
import sys
import datetime
from mobileperf.android.DB_utils import DatabaseOperations

# 获取当前文件所在目录的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))

# 获取 mobileperf-master 目录的路径
mobileperf_dir = os.path.join(base_dir, 'mobileperf-master')

# 添加 mobileperf-master 目录到 sys.path
sys.path.append(mobileperf_dir)

# 创建一个线程列表用于存储每个sh文件的执行线程
threads = []

app = Flask(__name__)

connected_devices = {}
device_threads = {}


# Helper functions

def sanitize_device_id(device_id):
    """Sanitize device id by replacing invalid characters with underscores."""
    sanitized_id = re.sub(r'[^\w\-_]', '_', device_id)
    return sanitized_id


def run_command_in_directory(command, directory):
    """Run command in the specified directory and print its output in real-time."""
    subprocess.Popen(command, cwd=directory, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_connected_devices():
    """Get list of connected devices via ADB."""
    adb_process = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = adb_process.communicate()
    device_lines = output.decode().split('\n')[1:-1]  # Extract device list
    devices = {}
    for line in device_lines:
        if '\tdevice' in line:
            device_id = line.split('\t')[0]
            devices[device_id] = f"host.docker.internal:{connected_devices.get(device_id)}"
    print(devices)
    return devices


def connect_device(device_id, tcp_port):
    """Connect to the device via adb using the device ID and tcp port."""
    target_device_id = f'host.docker.internal:{tcp_port}'
    connect_command = f'adb connect {target_device_id}'
    subprocess.run(connect_command, shell=True, capture_output=True, text=True)


def copy_mobileperf_folder(device_id, tcp_port):
    """Copy the MobilePerf folder to a new location and modify configuration files."""
    sanitized_device_id = sanitize_device_id(f'host.docker.internal:{tcp_port}')
    source_mobileperf_folder = os.path.join(base_dir, "mobileperf-master")
    target_mobileperf_folder = os.path.join(base_dir, "R", f"_{sanitized_device_id}")

    shutil.rmtree(target_mobileperf_folder, ignore_errors=True)  # Delete existing folder
    shutil.copytree(source_mobileperf_folder, target_mobileperf_folder)  # Copy new folder

    print(f"MobilePerf folder successfully copied to {target_mobileperf_folder}")
    return target_mobileperf_folder


def modify_config_file(target_mobileperf_folder, device_id):
    """Modify the configuration file for the device."""
    config_file_path = os.path.join(target_mobileperf_folder, "config.conf")
    with open(config_file_path, 'r') as file:
        lines = file.readlines()

    with open(config_file_path, 'w') as file:
        for line in lines:
            if line.startswith("serialnum="):
                file.write(f"serialnum={device_id}\n")
            elif line.startswith("monkey="):
                file.write("# " + line)  # Comment out old monkey command
                file.write("monkey=true\n")  # Write new monkey command
            else:
                file.write(line)


def run_device_tests(target_mobileperf_folder, tcp_port):
    """Run the startup script and FPS test for the device."""
    sh_directory = os.path.join(base_dir, "R", f"_{sanitize_device_id(f'host.docker.internal:{tcp_port}')}")

    command = f"python3 mobileperf/android/startup.py {tcp_port}"
    print(command)
    thread = threading.Thread(target=run_command_in_directory, args=(command, sh_directory))
    thread.start()
    thread.join()

    # Execute FPS test
    py_file = os.path.join(base_dir, "mobileperf-master", "mobileperf", "android", "fps_run.py")
    py_file = py_file.replace('\r', '')  # Remove carriage returns from path
    thread_py = threading.Thread(target=run_command_in_directory,
                                 args=(f"python {py_file} {device_id}", sh_directory))
    thread_py.start()
    thread_py.join()


def insert_device_info_to_db(device_id):
    """Insert device information into the database."""
    db_operations = DatabaseOperations()
    device_name = "未知"

    if device_id.startswith("S30"):
        device_name = "S30"
    elif device_id.startswith("Q20"):
        device_name = "Q20"
    elif device_id.startswith("P30"):
        device_name = "P30"

    try:
        db_operations.devices_info_insert(device_id, device_name)
    except Exception as db_e:
        print(db_e)
        print("Failed to insert device info into the database!")


# Main setup function
def handle_device_setup_test(device_id, tcp_port):
    """Main function to handle device setup and run tests."""
    # Connect the device
    connect_device(device_id, tcp_port)

    # Copy MobilePerf folder and modify config file
    target_mobileperf_folder = copy_mobileperf_folder(device_id, tcp_port)

    # Modify the configuration file for the device
    modify_config_file(target_mobileperf_folder, device_id)

    # Run device tests (startup + fps)
    run_device_tests(target_mobileperf_folder, tcp_port)

    # Insert device information into the database
    insert_device_info_to_db(device_id)

if __name__ == "__main__":
    handle_device_setup_test()