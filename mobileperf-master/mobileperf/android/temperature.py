#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import time
import sys
from datetime import datetime
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DB_utils import DatabaseOperations

class TemperatureCollector:
    def __init__(self, device_id):
        self.device_id = device_id
        self.db = DatabaseOperations()
        self.stop_flag = False
        self.temperature_buffer = []  # 用于数据平滑
        self.buffer_size = 5  # 平滑窗口大小

    def get_device_temperature(self):
        """获取设备温度"""
        try:
            # 获取电池温度
            cmd_battery = f"adb -s {self.device_id} shell cat /sys/class/power_supply/battery/temp"
            battery_temp = subprocess.check_output(cmd_battery, shell=True).decode().strip()
            battery_temp = float(battery_temp) / 10  # 转换为摄氏度
            
            # 获取CPU温度
            cmd_cpu = f"adb -s {self.device_id} shell cat /sys/class/thermal/thermal_zone0/temp"
            cpu_temp = subprocess.check_output(cmd_cpu, shell=True).decode().strip()
            cpu_temp = float(cpu_temp) / 1000  # 转换为摄氏度

            # 获取其他温度传感器数据
            sensors_data = {}
            try:
                cmd_sensors = f"adb -s {self.device_id} shell dumpsys thermalservice"
                sensors_output = subprocess.check_output(cmd_sensors, shell=True).decode()
                # 解析温度传感器数据
                for line in sensors_output.split('\n'):
                    if 'Temperature' in line and ':' in line:
                        name, value = line.split(':')
                        try:
                            temp = float(value.strip())
                            sensors_data[name.strip()] = temp
                        except ValueError:
                            continue
            except:
                pass

            return battery_temp, cpu_temp, sensors_data
        except Exception as e:
            print(f"获取温度失败: {e}")
            return None, None, {}

    def smooth_temperature(self, temp):
        """平滑温度数据"""
        if temp is None:
            return None
            
        self.temperature_buffer.append(temp)
        if len(self.temperature_buffer) > self.buffer_size:
            self.temperature_buffer.pop(0)
            
        return sum(self.temperature_buffer) / len(self.temperature_buffer)

    def start_monitoring(self):
        """开始温度监控"""
        print(f"开始监控设备 {self.device_id} 的温度...")
        print("时间\t\t\t电池温度(°C)\tCPU温度(°C)")
        print("-" * 50)

        try:
            while not self.stop_flag:
                current_time = datetime.now()
                battery_temp, cpu_temp, sensors_data = self.get_device_temperature()
                
                if battery_temp is not None and cpu_temp is not None:
                    # 平滑处理
                    smoothed_battery = self.smooth_temperature(battery_temp)
                    smoothed_cpu = self.smooth_temperature(cpu_temp)
                    
                    if smoothed_battery and smoothed_cpu:
                        print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}\t"
                              f"{smoothed_battery:.1f}\t\t{smoothed_cpu:.1f}")
                        
                        try:
                            # 获取最新的device_ids
                            latest_ids = self.db.get_latest_ids(self.device_id)
                            
                            # 准备温度数据
                            temp_data = {
                                "device_id": self.device_id,
                                "device_ids": latest_ids,
                                "datetime": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                                "temperature": {
                                    "battery": smoothed_battery,
                                    "cpu": smoothed_cpu,
                                    #"sensors": sensors_data
                                }
                            }
                            
                            # 插入温度数据
                            self.db.insert_temperature(temp_data)
                            
                        except Exception as e:
                            print(f"数据库操作失败: {str(e)}")
                
                time.sleep(1)  # 每秒更新一次

        except KeyboardInterrupt:
            print("\n停止温度监控")
        except Exception as e:
            print(f"监控过程发生错误: {e}")

    def stop_monitoring(self):
        """停止温度监控"""
        self.stop_flag = True

def main():
    if len(sys.argv) != 2:
        print("Usage: python temperature.py <device_id>")
        sys.exit(1)

    device_id = sys.argv[1]
    collector = TemperatureCollector(device_id)
    
    try:
        collector.start_monitoring()
    except KeyboardInterrupt:
        collector.stop_monitoring()
        print("\n温度监控已停止")

if __name__ == "__main__":
    # 直接指定设备ID并创建收集器实例
    collector = TemperatureCollector("P300PSgSk0900266")
    
    try:
        collector.start_monitoring()
    except KeyboardInterrupt:
        collector.stop_monitoring()
        print("\n温度监控已停止")
