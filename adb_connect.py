#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import random
import time
import requests
import json
import re
from threading import Thread, Event
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
REPORT_URL = 'http://127.0.0.1:5100/api/report'
DISCONNECT_URL = 'http://127.0.0.1:5100/api/disconnect'
connected_devices = {}

def sleep(seconds):
    """休眠指定秒数"""
    time.sleep(seconds)

def get_device_info(device_id):
    """获取设备信息"""
    try:
        # 获取系统版本号
        cmd = f"adb -s {device_id} shell getprop ro.build.version.release"
        system_version = subprocess.check_output(cmd, shell=True).decode().strip()

        # 获取内存信息
        cmd = f"adb -s {device_id} shell cat /proc/meminfo"
        memory_output = subprocess.check_output(cmd, shell=True).decode()
        memory_kb = 6005384  # 默认值
        for line in memory_output.split('\n'):
            if line.startswith('MemTotal'):
                memory_kb = int(line.split()[1])
                break
        memory_gb = round(memory_kb / 1024 / 1024)

        # 获取包名列表
        cmd = f"adb -s {device_id} shell pm list packages"
        packages = subprocess.check_output(cmd, shell=True).decode().split('\n')
        package_list = [pkg.strip() for pkg in packages if 'com.yangcong345' in pkg]

        return {
            'system_version': system_version,
            'memory_gb': memory_gb,
            'package_list': package_list,
            'online_status': '在线'
        }
    except Exception as e:
        logger.error(f"获取设备信息失败: {e}")
        return None

def create_tcp_bridge(device_id):
    """创建 TCP 桥接"""
    try:
        tcp_port = random.randint(1024, 65535)
        cmd = f"adb -s {device_id} tcpip {tcp_port}"
        subprocess.run(cmd, shell=True, check=True)
        sleep(2)  # 等待 TCP 模式生效
        return tcp_port
    except Exception as e:
        logger.error(f"创建 TCP 桥接失败: {e}")
        return None

def handle_new_device(device_id):
    """处理新连接的设备"""
    if device_id in connected_devices:
        logger.info(f"设备 {device_id} 已经连接，跳过")
        return

    logger.info(f"设备: {device_id} 连接中...")

    try:
        # 等待设备授权
        sleep(3)

        # 创建 TCP 桥接
        tcp_port = create_tcp_bridge(device_id)
        if not tcp_port:
            return

        # 获取设备信息
        device_info = get_device_info(device_id)
        if not device_info:
            return

        # 准备上报数据
        report_data = {
            'deviceId': device_id,
            'tcpPort': tcp_port,
            'systemVersion': device_info['system_version'],
            'memoryInGB': device_info['memory_gb'],
            'onlineStatus': device_info['online_status'],
            'packageList': device_info['package_list']
        }

        # 保存设备信息
        connected_devices[device_id] = report_data

        # 上报设备信息
        response = requests.post(REPORT_URL, json=report_data)
        response.raise_for_status()
        logger.info(f"成功上报设备信息: {json.dumps(report_data, ensure_ascii=False)}")

    except Exception as e:
        logger.error(f"处理设备 {device_id} 时发生错误: {e}")

def handle_disconnected_device(device_id):
    """处理断开连接的设备"""
    logger.info(f"设备: {device_id} 断开连接中...")

    if device_id in connected_devices:
        device_data = connected_devices[device_id]
        tcp_port = device_data['tcpPort']

        try:
            # 上报断开连接
            disconnect_data = {
                'deviceId': device_id,
                'tcpPort': tcp_port,
                'onlineStatus': '离线'
            }
            response = requests.post(DISCONNECT_URL, json=disconnect_data)
            response.raise_for_status()
            logger.info(f"成功上报设备断开连接: {device_id}, 端口: {tcp_port}")

        except Exception as e:
            logger.error(f"上报断开连接错误: {e}")
        finally:
            del connected_devices[device_id]
            logger.info(f"设备 {device_id} 已清理")
    else:
        logger.info(f"设备 {device_id} 不在已连接设备列表中，跳过清理")

class DeviceTracker:
    def __init__(self):
        self.stop_event = Event()
        self.last_devices = set()

    def track_devices(self):
        """监控设备连接状态"""
        while not self.stop_event.is_set():
            try:
                # 获取当前连接的设备
                output = subprocess.check_output("adb devices", shell=True).decode()
                current_devices = set()

                for line in output.split('\n')[1:]:  # 跳过第一行
                    if '\t' in line:
                        device_id, status = line.split('\t')
                        if status.strip() == 'device':
                            current_devices.add(device_id)

                # 处理新连接的设备
                for device_id in current_devices - self.last_devices:
                    handle_new_device(device_id)

                # 处理断开的设备
                for device_id in self.last_devices - current_devices:
                    handle_disconnected_device(device_id)

                self.last_devices = current_devices
                sleep(1)  # 每秒检查一次

            except Exception as e:
                logger.error(f"监控设备时发生错误: {e}")
                sleep(5)  # 发生错误时等待5秒后重试

    def start(self):
        """启动设备监控"""
        logger.info("正在开始监控设备连接状态...")
        try:
            # 启动 ADB 服务
            subprocess.run("adb start-server", shell=True, check=True)
            self.track_devices()
        except Exception as e:
            logger.error(f"启动监控时发生错误: {e}")

    def stop(self):
        """停止设备监控"""
        self.stop_event.set()

def main():
    tracker = DeviceTracker()
    try:
        tracker.start()
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在停止监控...")
        tracker.stop()

if __name__ == "__main__":
    main()
