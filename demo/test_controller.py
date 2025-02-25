#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import logging
import subprocess
import threading
import glob
import shutil
from datetime import datetime
import csv  # 添加到文件顶部的导入语句中

class DeviceController:
    def __init__(self, device_id):
        self.device_id = device_id
        self.package_name = None  # 初始化为 None，后续从 APK 获取
        self.apk_path = None  # 初始化为 None，后续从 GUI 设置
        self.install_times = 10  # 默认安装次数
        self.clear_times = 10    # 默认清除次数
        self.current_screen_file = None
        
        # 支持的包名列表
        self.supported_packages = [
            'com.yangcong345.cloud.toolbox',
            'com.yangcong345.cloud.plan'  # 新增包名
        ]
        
        # 初始化监控线程为 None
        self.temp_monitor_thread = None
        self.log_monitor_thread = None
        self.screen_record_process = None
        self.stop_monitor = False
        self.monitoring = False
        
        # 创建日志目录
        self.log_dir = os.path.join("demo", "logs", device_id)
        self.screen_dir = os.path.join("demo", "screen", device_id)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.screen_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 监控状态
        self.screen_recording = False
        
    def setup_environment(self, config):
        """设置测试环境"""
        try:
            # 设置网络环境
            network = config.get('network')
            if network == 'wifi_disabled':
                self.disable_wifi()
            elif network == '2g':
                self.set_network_2g()
            elif network == 'wifi_normal':
                self.enable_wifi()
            
            # 启动监控
            if config.get('screen_record'):
                self.start_screen_record()
            if config.get('log_monitor'):
                self.start_log_monitor()
            if config.get('temp_monitor'):
                self.start_temp_monitor()
                
            logging.info("环境设置完成")
            
        except Exception as e:
            logging.error(f"环境设置失败: {e}")
            raise

    def set_wifi_state(self, enabled):
        """设置 WIFI 状态"""
        try:
            if enabled:
                cmd = f"adb -s {self.device_id} shell svc wifi enable"
                subprocess.run(cmd, shell=True, check=True)
                logging.info("WIFI状态: 已启用")
            else:
                cmd = f"adb -s {self.device_id} shell svc wifi disable"
                subprocess.run(cmd, shell=True, check=True)
                logging.info("WIFI状态: 已禁用")
            
            # 检查WIFI状态
            check_cmd = f"adb -s {self.device_id} shell settings get global wifi_on"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            wifi_state = "开启" if result.stdout.strip() == "1" else "关闭"
            logging.info(f"当前WIFI状态: {wifi_state}")
            return True
        except Exception as e:
            logging.error(f"设置WIFI状态失败: {e}")
            return False

    def set_network_state(self, network_type):
        """设置网络状态"""
        try:
            # 获取当前网络状态
            check_cmd = f"adb -s {self.device_id} shell settings get global preferred_network_mode"
            before = subprocess.run(check_cmd, shell=True, capture_output=True, text=True).stdout.strip()
            logging.info(f"设置前网络模式: {before}")
            
            # 设置网络模式
            if network_type == '2g':
                cmd = f"adb -s {self.device_id} shell settings put global preferred_network_mode 1"
                mode_desc = "2G (GSM/GPRS/EDGE)"
            elif network_type == '4g':
                cmd = f"adb -s {self.device_id} shell settings put global preferred_network_mode 9"
                mode_desc = "4G (LTE)"
            subprocess.run(cmd, shell=True, check=True)
            
            # 检查设置后的状态
            after = subprocess.run(check_cmd, shell=True, capture_output=True, text=True).stdout.strip()
            logging.info(f"设置后网络模式: {after}")
            logging.info(f"网络环境已切换为: {mode_desc}")
            
            # 等待网络切换完成
            time.sleep(2)
            
            # 检查网络连接
            ping_cmd = f"adb -s {self.device_id} shell ping -c 1 8.8.8.8"
            ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
            if ping_result.returncode == 0:
                logging.info("网络连接正常")
            else:
                logging.warning("网络连接可能不稳定")
            
            return True
        except Exception as e:
            logging.error(f"设置网络状态失败: {e}")
            return False

    def start_screen_record(self):
        """启动屏幕录制"""
        try:
            # 生成录屏文件名（不带扩展名，用于分段）
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 电脑上的最终保存路径
            self.screen_file = os.path.join(self.screen_dir, f"screen_{self.timestamp}.mp4")
            # 创建临时目录用于存放分段视频
            self.temp_dir = os.path.join(self.screen_dir, f"temp_{self.timestamp}")
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # 启动录屏循环线程
            self.stop_recording = False
            self.recording_thread = threading.Thread(target=self._record_screen_segments)
            self.recording_thread.start()
            
            logging.info(f"录屏已启动，最终文件将保存至: {self.screen_file}")
            
        except Exception as e:
            logging.error(f"启动录屏失败: {e}")
            raise

    def _record_screen_segments(self):
        """录制屏幕分段视频"""
        segment_duration = 120  # 2分钟一段
        segment_index = 0
        merged_file = None  # 用于跟踪当前合并的文件
        
        while not self.stop_recording:
            try:
                # 生成当前段的文件名
                segment_file = os.path.join(self.temp_dir, f"segment_{segment_index}.mp4")
                device_file = f"/sdcard/segment_{segment_index}.mp4"
                
                # 清理可能存在的旧文件
                subprocess.run(f"adb -s {self.device_id} shell rm -f {device_file}", shell=True)
                
                # 启动录制命令
                cmd = (f"adb -s {self.device_id} shell screenrecord "
                       f"--bit-rate 8000000 "     # 8Mbps 比特率
                       f"--time-limit {segment_duration} "  # 分段时长
                       f"--verbose "               # 显示详细信息
                       f"--size 1280x720 "         # 设置分辨率
                       f"{device_file}")
                
                logging.info(f"开始录制第 {segment_index + 1} 段视频")
                process = subprocess.Popen(cmd, shell=True)
                
                # 等待录制完成或手动停止
                start_time = time.time()
                while time.time() - start_time < segment_duration and not self.stop_recording:
                    time.sleep(1)
                
                # 停止当前段的录制
                process.terminate()
                process.wait(timeout=5)
                
                # 等待文件写入完成
                time.sleep(3)
                
                # 检查设备上是否有文件
                check_cmd = f"adb -s {self.device_id} shell ls {device_file}"
                if subprocess.run(check_cmd, shell=True, capture_output=True).returncode == 0:
                    # 将视频文件从设备复制到电脑
                    pull_cmd = f"adb -s {self.device_id} pull {device_file} {segment_file}"
                    result = subprocess.run(pull_cmd, shell=True, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists(segment_file):
                        logging.info(f"第 {segment_index + 1} 段视频已保存")
                        
                        try:
                            if segment_index == 0:
                                # 第一个片段直接作为合并文件
                                shutil.copy2(segment_file, self.screen_file)
                                merged_file = self.screen_file
                            else:
                                # 创建临时合并文件
                                temp_merge_file = os.path.join(self.temp_dir, "temp_merge.mp4")
                                
                                # 创建文件列表
                                list_file = os.path.join(self.temp_dir, "files.txt")
                                with open(list_file, 'w', encoding='utf-8') as f:
                                    f.write(f"file '{os.path.abspath(merged_file)}'\n")
                                    f.write(f"file '{os.path.abspath(segment_file)}'\n")
                                
                                # 使用 concat demuxer 合并视频
                                merge_cmd = (
                                    f'ffmpeg -f concat -safe 0 -i "{list_file}" '
                                    f'-c copy "{temp_merge_file}"'
                                )
                                
                                # 执行合并命令
                                try:
                                    subprocess.run(
                                        merge_cmd, 
                                        shell=True, 
                                        check=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        encoding='utf-8'
                                    )
                                    
                                    # 检查合并是否成功
                                    if os.path.exists(temp_merge_file) and os.path.getsize(temp_merge_file) > 0:
                                        # 更新合并文件
                                        if os.path.exists(self.screen_file):
                                            os.remove(self.screen_file)
                                        shutil.move(temp_merge_file, self.screen_file)
                                        merged_file = self.screen_file
                                        logging.info(f"已成功合并第 {segment_index + 1} 段视频")
                                    else:
                                        raise Exception("合并后的文件无效")
                                    
                                except subprocess.CalledProcessError as e:
                                    logging.error(f"合并命令执行失败: {e.stderr}")
                                    raise
                                
                        except Exception as e:
                            logging.error(f"合并第 {segment_index + 1} 段视频失败: {str(e)}")
                            # 如果合并失败，保留当前合并的文件
                            if merged_file and os.path.exists(merged_file):
                                if merged_file != self.screen_file:
                                    shutil.copy2(merged_file, self.screen_file)
                        
                        # 清理设备上的临时文件
                        subprocess.run(f"adb -s {self.device_id} shell rm -f {device_file}", shell=True)
                        segment_index += 1
                    else:
                        logging.error(f"保存第 {segment_index + 1} 段视频失败: {result.stderr}")
                else:
                    logging.error(f"设备上未找到视频文件: {device_file}")
                
            except Exception as e:
                logging.error(f"录制第 {segment_index + 1} 段视频时出错: {e}")
                time.sleep(1)

    def stop_screen_record(self):
        """停止屏幕录制"""
        try:
            if hasattr(self, 'recording_thread'):
                # 设置停止标志
                self.stop_recording = True
                # 等待录制线程结束
                self.recording_thread.join(timeout=10)
                
                # 检查临时目录是否存在
                if not os.path.exists(self.temp_dir):
                    logging.error(f"临时目录不存在: {self.temp_dir}")
                    return
                
                # 查找所有分段视频
                segments = glob.glob(os.path.join(self.temp_dir, "segment_*.mp4"))
                if segments:
                    logging.info(f"找到 {len(segments)} 个视频片段")
                    
                    # 创建文件列表，使用绝对路径
                    list_file = os.path.join(self.temp_dir, "files.txt")
                    with open(list_file, 'w', encoding='utf-8') as f:
                        for segment in sorted(segments):
                            abs_path = os.path.abspath(segment)
                            f.write(f"file '{abs_path}'\n")
                    logging.info("已创建文件列表")
                    
                    # 合并视频
                    merge_cmd = (f'ffmpeg -f concat -safe 0 -i "{list_file}" '
                               f'-c copy "{self.screen_file}"')
                    
                    try:
                        result = subprocess.run(
                            merge_cmd, 
                            shell=True, 
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        
                        # 检查合并后的文件
                        if os.path.exists(self.screen_file):
                            size = os.path.getsize(self.screen_file)
                            if size > 0:
                                logging.info(f"合并后的视频大小: {size/1024/1024:.2f}MB")
                                logging.info(f"录屏文件已成功保存至: {self.screen_file}")
                            else:
                                logging.error("合并后的视频文件大小为0")
                                # 如果合并失败，复制最后一个片段
                                shutil.copy2(segments[-1], self.screen_file)
                                logging.info("已使用最后一个片段作为录屏文件")
                        else:
                            logging.error("合并视频失败，文件未生成")
                            
                    except subprocess.CalledProcessError as e:
                        logging.error(f"合并视频失败: {e.stderr}")
                        # 如果合并失败，复制最后一个片段
                        shutil.copy2(segments[-1], self.screen_file)
                        logging.info("合并失败，已使用最后一个片段作为录屏文件")
                        
                else:
                    logging.error(f"未找到任何视频片段在目录: {self.temp_dir}")
                
                # 清理临时文件
                try:
                    shutil.rmtree(self.temp_dir)
                    logging.info("已清理临时文件")
                except Exception as e:
                    logging.error(f"清理临时文件失败: {e}")
                
        except Exception as e:
            logging.error(f"停止录屏失败: {e}")
            # 确保清理临时文件
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    def start_log_monitor(self):
        """启动日志监控"""
        try:
            # 限制日志文件大小为 100MB，超过后自动滚动
            logcat_file = os.path.join(self.log_dir, "logcat.txt")
            cmd = f"adb -s {self.device_id} logcat -v threadtime -r 102400 -n 5 > {logcat_file}"
            self.logcat_process = subprocess.Popen(cmd, shell=True,
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
            logging.info("日志监控已启动")
        except Exception as e:
            logging.error(f"启动日志监控失败: {e}")
            raise

    def start_temp_monitor(self):
        """启动温度监控"""
        if not self.temp_monitor_thread:
            self.stop_monitor = False
            self.temp_monitor_thread = threading.Thread(target=self._monitor_temperature)
            self.temp_monitor_thread.daemon = True
            self.temp_monitor_thread.start()

    def _monitor_temperature(self):
        """监控温度"""
        last_log_time = 0
        
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 创建温度日志文件
        temp_log_file = os.path.join(self.log_dir, f"{self.device_id}_{current_time}temperature.log")
        
        while not self.stop_monitor:
            try:
                current_time = time.time()
                cmd = f"adb -s {self.device_id} shell dumpsys battery | grep temperature"
                output = subprocess.check_output(cmd, shell=True).decode()
                
                # 解析温度值
                temp = float(output.split(':')[1].strip()) / 10
                
                # 判断温度状态
                status = "正常"
                if temp >= 45:
                    status = "过热"
                elif temp >= 40:
                    status = "偏高"
                
                # 每60秒记录一次日志
                if current_time - last_log_time >= 60:  # 改为60秒
                    log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 温度: {temp}°C, 状态: {status}"
                    # 写入温度日志文件
                    with open(temp_log_file, 'a', encoding='utf-8') as f:
                        f.write(log_message + '\n')
                    logging.info(f"设备温度监控 - 温度: {temp}°C, 状态: {status}")
                    last_log_time = current_time
                
                time.sleep(5)  # 每5秒检查一次温度，但只每分钟记录一次日志
                
            except Exception as e:
                error_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 温度监控异常: {e}"
                with open(temp_log_file, 'a', encoding='utf-8') as f:
                    f.write(error_msg + '\n')
                logging.error(f"温度监控异常: {e}")
                time.sleep(5)  # 出错后等待5秒再重试

    def stop_temp_monitor(self):
        """停止温度监控"""
        if hasattr(self, 'temp_monitoring'):
            self.temp_monitoring = False
            if hasattr(self, 'temp_monitor_thread'):
                self.temp_monitor_thread.join(timeout=5)

    def get_device_temperature(self):
        """获取设备温度"""
        try:
            # 尝试 dumpsys battery
            cmd = f"adb -s {self.device_id} shell dumpsys battery | grep temperature"
            output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
            return float(output.split(':')[1].strip()) / 10
        except:
            try:
                # 尝试 thermal zone
                cmd = f"adb -s {self.device_id} shell cat /sys/class/thermal/thermal_zone0/temp"
                output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
                return float(output) / 1000
            except:
                return None

    def get_temperature_status(self, temp):
        """获取温度状态"""
        if temp > 45:
            return "过高"
        elif temp < 20:
            return "过低"
        return "正常"

    def install_app(self):
        """安装应用"""
        try:
            # 打印当前实例的状态
            logging.info("当前安装配置:")
            logging.info(f"设备ID: {self.device_id}")
            logging.info(f"APK路径: {self.apk_path}")
            logging.info(f"包名: {self.package_name}")
            
            if not self.apk_path:
                raise ValueError("APK路径未设置")
            
            if not os.path.exists(self.apk_path):
                raise ValueError(f"APK文件不存在: {self.apk_path}")
            
            if not self.apk_path.endswith('.apk'):
                raise ValueError(f"不是有效的APK文件: {self.apk_path}")
            
            if not self.package_name:
                raise ValueError("未设置包名")
            
            # 直接安装应用，不进行卸载
            logging.info(f"开始安装APK: {self.apk_path}")
            cmd = f"adb -s {self.device_id} install -r \"{self.apk_path}\""  # 添加引号处理路径中的空格
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if "Success" in result.stdout:
                logging.info("应用安装成功")
                
                # 安装成功后启动应用
                logging.info("正在启动新安装的应用...")
                time.sleep(2)  # 等待安装完成
                
                try:
                    self.launch_app()
                    logging.info("应用启动成功")
                    return True
                except Exception as e:
                    logging.error(f"应用启动失败: {e}")
                    # 启动失败不影响安装结果
                    return True
            else:
                logging.error(f"应用安装失败: {result.stderr}")
                return False
            
        except Exception as e:
            logging.error(f"安装应用失败: {e}")
            return False

    def get_package_name(self, apk_path):
        """从APK文件获取包名"""
        try:
            # 首先尝试使用 aapt2
            try:
                cmd = f"aapt2 dump badging {apk_path} | grep package:\ name"
                output = subprocess.check_output(cmd, shell=True).decode()
                package_name = output.split("'")[1]
                logging.info(f"使用 aapt2 获取到包名: {package_name}")
                return package_name
            except:
                logging.info("aapt2 获取包名失败，尝试使用 aapt...")
            
            # 如果 aapt2 失败，尝试使用 aapt
            try:
                cmd = f"aapt dump badging {apk_path} | grep package:\ name"
                output = subprocess.check_output(cmd, shell=True).decode()
                package_name = output.split("'")[1]
                logging.info(f"使用 aapt 获取到包名: {package_name}")
                return package_name
            except:
                logging.info("aapt 获取包名失败，尝试使用 adb...")
            
            # 如果 aapt 也失败，使用 adb 安装并获取包名
            logging.info("尝试通过安装 APK 获取包名...")
            
            # 先安装 APK
            install_cmd = f"adb -s {self.device_id} install -r {apk_path}"
            subprocess.check_call(install_cmd, shell=True)
            
            # 获取最近安装的包名
            cmd = f"adb -s {self.device_id} shell pm list packages -3 -f | grep {os.path.basename(apk_path)}"
            output = subprocess.check_output(cmd, shell=True).decode()
            package_name = output.split('=')[-1].strip()
            
            if not package_name:
                raise ValueError("无法获取包名")
            
            logging.info(f"通过安装获取到包名: {package_name}")
            return package_name
        
        except Exception as e:
            logging.error(f"获取包名失败: {e}")
            raise ValueError(f"获取包名失败: {e}")

    def run_monkey(self, duration_minutes=2):
        """执行monkey测试"""
        try:
            # 创建 monkey 日志文件
            monkey_log_file = os.path.join(self.log_dir, f"{self.device_id}_monkey.log")
            
            # 构建 monkey 命令
            cmd = (f"adb -s {self.device_id} shell monkey "
                   f"-p {self.package_name} "
                  "--throttle 500 "
                  "--ignore-crashes --ignore-timeouts --ignore-security-exceptions "
                  "--monitor-native-crashes "
                  "-s 8888 -v "
                  "288000")  # 设置足够大的事件数，由时间控制停止
            
            # 启动 monkey 进程并重定向输出到日志文件
            with open(monkey_log_file, 'w', encoding='utf-8') as f:
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=f,
                    stderr=f,
                    universal_newlines=True
                )
            
            logging.info(f"开始执行Monkey测试 - 包名: {self.package_name}, 时长: {duration_minutes}分钟")
            
            # 监控执行时间
            start_time = time.time()
            while time.time() - start_time < duration_minutes * 60:
                if process.poll() is not None:
                    # monkey 异常退出
                    logging.error("Monkey测试异常退出")
                    break
                    
                # 每分钟输出一次进度
                elapsed_minutes = int((time.time() - start_time) / 60)
                remaining_minutes = duration_minutes - elapsed_minutes
                logging.info(f"Monkey测试进行中... 已执行 {elapsed_minutes} 分钟，剩余 {remaining_minutes} 分钟")
                time.sleep(60)  # 每分钟检查一次
            
            # 停止 monkey 进程
            self._stop_monkey()
            logging.info("Monkey测试完成")
            
        except Exception as e:
            logging.error(f"执行Monkey测试失败: {e}")
            self._stop_monkey()

    def _stop_monkey(self):
        """停止monkey测试"""
        try:
            # 获取 monkey 进程 PID
            cmd = f"adb -s {self.device_id} shell ps | grep monkey"
            output = subprocess.check_output(cmd, shell=True).decode()
            if output:
                pid = output.split()[1]
                # 强制结束进程
                kill_cmd = f"adb -s {self.device_id} shell kill -9 {pid}"
                subprocess.check_output(kill_cmd, shell=True)
                logging.info("已强制结束 Monkey 进程")
        except Exception as e:
            logging.warning(f"结束 Monkey 进程失败: {e}")

    def clear_app_data(self):
        """清除应用数据"""
        try:
            # 清除应用数据
            cmd = f"adb -s {self.device_id} shell pm clear {self.package_name}"
            subprocess.run(cmd, shell=True, check=True)
            
            # 等待应用清除完成
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"清除应用数据失败: {e}")
            raise

    def kill_monkey(self):
        """强制结束设备上的 monkey 进程"""
        try:
            # 获取 monkey 进程 PID
            cmd = f"adb -s {self.device_id} shell ps | grep monkey"
            output = subprocess.check_output(cmd, shell=True).decode()
            if output:
                pid = output.split()[1]
                # 强制结束进程
                kill_cmd = f"adb -s {self.device_id} shell kill -9 {pid}"
                subprocess.check_output(kill_cmd, shell=True)
                logging.info("已强制结束 Monkey 进程")
        except Exception as e:
            logging.warning(f"结束 Monkey 进程失败: {e}")

    def cleanup(self):
        """清理资源"""
        try:
            # 先停止所有监控线程
            self.stop_monitor = True
            
            # 停止日志监控
            if hasattr(self, 'logcat_process') and self.logcat_process:
                try:
                    self.logcat_process.terminate()
                    self.logcat_process.wait(timeout=5)
                except:
                    self.logcat_process.kill()
                self.logcat_process = None
            
            # 停止温度监控线程
            if hasattr(self, 'temp_monitor_thread') and self.temp_monitor_thread:
                try:
                    self.temp_monitor_thread.join(timeout=5)
                except:
                    pass
                self.temp_monitor_thread = None
            
            # 停止录屏
            if hasattr(self, 'recording_thread') and self.recording_thread:
                try:
                    self.stop_recording = True
                    self.recording_thread.join(timeout=5)
                except:
                    pass
                self.recording_thread = None
            
            # 强制停止所有 monkey 进程
            try:
                subprocess.run(f"adb -s {self.device_id} shell pkill -9 monkey", 
                             shell=True, timeout=5)
            except:
                pass
            
            # 强制停止应用
            try:
                subprocess.run(f"adb -s {self.device_id} shell am force-stop {self.package_name}", 
                             shell=True, timeout=5)
            except:
                pass
            
            # 清理存储空间
            try:
                subprocess.run(f"adb -s {self.device_id} shell rm -f /data/local/tmp/fill_*", 
                             shell=True, timeout=5)
            except:
                pass
            
            logging.info("资源清理完成")
            
        except Exception as e:
            logging.error(f"清理资源失败: {e}")
        finally:
            # 确保所有进程都被终止
            if hasattr(self, 'logcat_process') and self.logcat_process:
                try:
                    self.logcat_process.kill()
                except:
                    pass

    def set_memory_usage(self, target_percent):
        """设置内存使用率"""
        try:
            # 获取总内存
            cmd = f"adb -s {self.device_id} shell cat /proc/meminfo"
            output = subprocess.check_output(cmd, shell=True).decode()
            total_memory = int(output.split('\n')[0].split()[1]) * 1024  # 转换为字节
            
            # 启动内存占用进程
            memory_fill_script = """
            while true; do
                array=()
                for i in $(seq 1 100000); do
                    array+=(1)
                done
                sleep 1
            done
            """
            
            cmd = f"adb -s {self.device_id} shell 'echo \"{memory_fill_script}\" > /data/local/tmp/fill_memory.sh'"
            subprocess.check_call(cmd, shell=True)
            
            cmd = f"adb -s {self.device_id} shell 'sh /data/local/tmp/fill_memory.sh &'"
            subprocess.Popen(cmd, shell=True)
            
            # 监控内存使用率
            while True:
                cmd = f"adb -s {self.device_id} shell cat /proc/meminfo"
                output = subprocess.check_output(cmd, shell=True).decode()
                available = int(output.split('\n')[2].split()[1]) * 1024
                usage_percent = (total_memory - available) / total_memory * 100
                
                if usage_percent >= target_percent:
                    break
                    
                time.sleep(5)
                
            logging.info(f"内存使用率已达到目标值: {target_percent}%")
            return True
        except Exception as e:
            logging.error(f"设置内存使用率失败: {e}")
            return False

    def set_install_times(self, times):
        """设置安装次数"""
        self.install_times = times
        
    def set_clear_times(self, times):
        """设置清除缓存次数"""
        self.clear_times = times

    def get_storage_fill_size(self, target_percent):
        """
        计算需要填充的存储大小
        
        Args:
            target_percent: 目标使用率(%)
            
        Returns:
            需要填充的大小(MB)
        """
        try:
            # 获取存储信息
            cmd = f"adb -s {self.device_id} shell df /sdcard"
            output = subprocess.check_output(cmd, shell=True).decode()
            
            # 解析输出
            lines = output.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                total = int(parts[1]) // 1024  # 转换为MB
                used = int(parts[2]) // 1024   # 转换为MB
                
                # 计算需要填充的大小
                target_used = total * target_percent / 100
                fill_size = max(0, target_used - used)
                
                logging.info(f"存储总大小: {total}MB")
                logging.info(f"当前已使用: {used}MB")
                logging.info(f"目标使用量: {target_used}MB")
                logging.info(f"需要填充: {fill_size}MB")
                
                return int(fill_size)
                
        except Exception as e:
            logging.error(f"计算填充大小失败: {e}")
            return 0

    def fill_storage(self, target_size_mb):
        """
        填充设备存储，每5秒填充1GB，直到达到目标大小
        
        Args:
            target_size_mb: 目标填充大小(MB)
        """
        try:
            # 创建1GB的临时文件
            block_size = 1024 * 1024  # 1MB
            gb_size = 1024  # 1GB = 1024MB
            
            filled_size = 0
            while filled_size < target_size_mb and not self.stop_monitor:
                # 计算这次要填充的大小（不超过1GB）
                remaining = target_size_mb - filled_size
                current_fill = min(gb_size, remaining)
                
                # 生成随机文件名
                filename = f"fill_{int(time.time())}.tmp"
                device_path = f"/sdcard/{filename}"
                
                # 创建填充命令
                cmd = (f"adb -s {self.device_id} shell 'dd if=/dev/urandom "
                      f"of={device_path} bs={block_size} count={current_fill}'")
                
                # 执行填充
                logging.info(f"正在填充存储 {filled_size}MB/{target_size_mb}MB...")
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 更新已填充大小
                filled_size += current_fill
                
                # 记录填充文件
                if not hasattr(self, 'filled_files'):
                    self.filled_files = []
                self.filled_files.append(device_path)
                
                # 等待5秒
                time.sleep(5)
                
            logging.info(f"存储填充完成，已填充 {filled_size}MB")
            
        except Exception as e:
            logging.error(f"填充存储失败: {e}")

    def clear_filled_storage(self):
        """清理填充的存储文件"""
        try:
            if hasattr(self, 'filled_files'):
                for file in self.filled_files:
                    cmd = f"adb -s {self.device_id} shell rm -f {file}"
                    subprocess.run(cmd, shell=True)
                logging.info("已清理填充的存储文件")
                self.filled_files = []
        except Exception as e:
            logging.error(f"清理存储文件失败: {e}")

    def get_memory_fill_size(self, target_percent):
        """计算需要填充的内存大小"""
        try:
            # 获取当前内存使用情况
            cmd = f"adb -s {self.device_id} shell cat /proc/meminfo"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # 解析输出获取总内存和可用内存
                total = 0
                available = 0
                for line in result.stdout.split('\n'):
                    if 'MemTotal' in line:
                        total = int(line.split()[1]) * 1024
                    elif 'MemAvailable' in line:
                        available = int(line.split()[1]) * 1024
                
                if total > 0:
                    current_percent = ((total - available) / total) * 100
                    logging.info(f"当前内存使用率: {current_percent:.1f}%")
                    if current_percent < target_percent:
                        return int((target_percent - current_percent) * total / 100)
            return 0
        except Exception as e:
            logging.error(f"计算内存填充大小失败: {e}")
            return 0

    def fill_memory(self, total_size):
        """渐进式填充内存"""
        try:
            if total_size <= 0:
                return
            
            # 创建一个Python程序来占用内存
            memory_fill_script = """
import time
import sys

# 分配指定大小的内存
def allocate_memory(size_mb):
    # 每次分配 100MB
    chunk_size = 100 * 1024 * 1024
    data = []
    total_allocated = 0
    
    while total_allocated < size_mb * 1024 * 1024:
        try:
            chunk = bytearray(min(chunk_size, size_mb * 1024 * 1024 - total_allocated))
            data.append(chunk)
            total_allocated += len(chunk)
            time.sleep(0.5)  # 每次分配后稍作等待
        except MemoryError:
            break
    
    # 保持运行直到被终止
    while True:
        time.sleep(1)

if len(sys.argv) > 1:
    size_mb = int(sys.argv[1])
    allocate_memory(size_mb)
"""
            # 将脚本推送到设备
            script_path = "/data/local/tmp/memory_fill.py"
            with open("memory_fill.py", "w") as f:
                f.write(memory_fill_script)
            
            subprocess.run(f"adb -s {self.device_id} push memory_fill.py {script_path}", shell=True)
            
            # 计算需要填充的内存大小（MB）
            size_mb = total_size // (1024 * 1024)
            
            # 在后台运行Python脚本
            cmd = f"adb -s {self.device_id} shell python {script_path} {size_mb} &"
            self.memory_fill_process = subprocess.Popen(cmd, shell=True)
            
            logging.info(f"开始填充内存 {size_mb}MB...")
            
            # 等待内存使用率达到目标值或超时
            timeout = 60  # 60秒超时
            start_time = time.time()
            while time.time() - start_time < timeout:
                current_percent = self._get_current_memory_percent()
                logging.info(f"当前内存使用率: {current_percent:.1f}%")
                if current_percent >= 80:
                    logging.info("内存使用率已达到80%")
                    break
                time.sleep(2)
            
        except Exception as e:
            logging.error(f"填充内存失败: {e}")
            self.clear_filled_memory()

    def _get_current_memory_percent(self):
        """获取当前内存使用率"""
        try:
            cmd = f"adb -s {self.device_id} shell cat /proc/meminfo"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                total = 0
                available = 0
                for line in result.stdout.split('\n'):
                    if 'MemTotal' in line:
                        total = int(line.split()[1])
                    elif 'MemAvailable' in line:
                        available = int(line.split()[1])
                if total > 0:
                    return ((total - available) / total) * 100
        except Exception:
            pass
        return 0

    def clear_filled_memory(self):
        """清理填充的内存"""
        try:
            # 终止内存填充进程
            if hasattr(self, 'memory_fill_process'):
                cmd = f"adb -s {self.device_id} shell pkill -f memory_fill.py"
                subprocess.run(cmd, shell=True)
                self.memory_fill_process = None
                
            # 删除临时脚本
            cmd = f"adb -s {self.device_id} shell rm -f /data/local/tmp/memory_fill.py"
            subprocess.run(cmd, shell=True)
            
            logging.info("已清理填充的内存")
            
            # 等待内存释放
            time.sleep(2)
            current_percent = self._get_current_memory_percent()
            logging.info(f"当前内存使用率: {current_percent:.1f}%")
            
        except Exception as e:
            logging.error(f"清理内存失败: {e}")

    def launch_app(self):
        """启动应用"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 先尝试获取主 Activity
                cmd = f"adb -s {self.device_id} shell dumpsys package {self.package_name} | grep -A 1 'android.intent.action.MAIN:'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if "android.intent.category.LAUNCHER" in result.stdout:
                    activity_name = result.stdout.split()[1]
                    launch_cmd = f"adb -s {self.device_id} shell am start -n {self.package_name}/{activity_name}"
                    subprocess.run(launch_cmd, shell=True, check=True)
                    logging.info("应用启动成功")
                    return
                
                # 如果找不到主 Activity，使用 monkey 方式启动
                logging.info(f"未找到包 {self.package_name} 的主 Activity")
                logging.info("尝试使用 monkey 方式启动...")
                
                # 重启 ADB 服务
                if retry_count > 0:
                    subprocess.run("adb kill-server", shell=True)
                    time.sleep(2)
                    subprocess.run("adb start-server", shell=True)
                    time.sleep(3)
                
                monkey_cmd = f"adb -s {self.device_id} shell monkey -p {self.package_name} -c android.intent.category.LAUNCHER 1"
                result = subprocess.run(monkey_cmd, shell=True, capture_output=True, text=True)
                
                if "Events injected: 1" in result.stdout:
                    logging.info("使用 monkey 方式启动成功")
                    return
                
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f"启动失败，等待 5 秒后重试 ({retry_count}/{max_retries})")
                    time.sleep(5)
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logging.error(f"启动异常: {e}，等待 5 秒后重试 ({retry_count}/{max_retries})")
                    time.sleep(5)
                else:
                    raise Exception(f"应用启动失败: {e}")
        
        raise Exception("多次尝试后应用启动失败")

# 然后是其他导入
from test_cases import (
    run_test_case_1,
    run_test_case_2,
    run_test_case_3,
    run_test_case_4,
    run_test_case_5
)

# 定义测试用例映射
test_cases = {
    1: run_test_case_1,
    2: run_test_case_2,
    3: run_test_case_3,
    4: run_test_case_4,
    5: run_test_case_5
}

def run_test_case_1(device_id, config):
    """用例1: 关闭wifi环境测试"""
    try:
        # 创建设备控制器并设置配置
        device = DeviceController(device_id)
        device.package_name = config.get('package_name')
        device.apk_path = config.get('apk_path')  # 确保设置 APK 路径

        
        # 打印配置信息以便调试
        logging.info(f"用例1配置信息:")
        logging.info(f"APK路径: {device.apk_path}")
        logging.info(f"包名: {device.package_name}")

        # 启动录屏和监控
        device.start_screen_record()
        device.start_temp_monitor()
        device.start_log_monitor()
        
        logging.info("\n开始执行用例1前的准备工作")
        
        # 执行安装和清除操作，传入当前 device 对象
        device = run_install_and_clear(device_id, config, device)  # 传入已配置的 device 对象
        
        
        
        # 执行 monkey 测试
        duration = config.get('case_durations', {}).get('1', 2)  # 默认2分钟
        device.run_monkey(duration_minutes=duration)
        
    except Exception as e:
        logging.error(f"用例1执行失败: {e}")
        raise
    finally:
        if device:
            device.cleanup()

def run_install_and_clear(device_id, config, device=None):
    """执行安装和清除操作"""
    try:
        # 如果没有传入 device 对象，创建新的并设置配置
        if device is None:
            device = DeviceController(device_id)
            device.package_name = config.get('package_name')
            device.apk_path = config.get('apk_path')
        
        if not device.package_name:
            raise ValueError("未设置包名")
            
        if not device.apk_path:
            raise ValueError("未设置APK路径")
            
        # 验证APK文件
        if not os.path.exists(device.apk_path):
            raise ValueError(f"APK文件不存在: {device.apk_path}")
            
        if not device.apk_path.endswith('.apk'):
            raise ValueError(f"不是有效的APK文件: {device.apk_path}")
        
        # 执行安装
        logging.info(f"开始执行安装 ({config.get('install_times', 2)} 次)")
        for i in range(config.get('install_times', 2)):
            try:
                success = device.install_app()
                if not success:
                    raise Exception("安装失败")
                logging.info(f"第 {i+1} 次安装成功")
            except Exception as e:
                logging.error(f"第 {i+1} 次安装失败: {e}")
                raise
                
        # 执行清除缓存
        logging.info(f"开始执行清除缓存 ({config.get('clear_times', 2)} 次)")
        for i in range(config.get('clear_times', 2)):
            try:
                device.clear_app_data()
                time.sleep(5)  # 等待5秒
                device.launch_app()
                time.sleep(3)  # 等待应用启动
                logging.info(f"第 {i+1} 次清除缓存成功")
            except Exception as e:
                logging.error(f"第 {i+1} 次清除缓存失败: {e}")
                raise
        
        return device
        
    except Exception as e:
        logging.error(f"安装和清除操作失败: {e}")
        raise

def run_test_case_2(device_id, config):
    """用例2: 2G网络环境测试"""
    try:
        # 创建设备控制器并设置配置
        device = DeviceController(device_id)
        device.package_name = config.get('package_name')
        device.apk_path = config.get('apk_path')  # 确保设置 APK 路径
        
        # 打印配置信息以便调试
        logging.info(f"用例2配置信息:")
        logging.info(f"APK路径: {device.apk_path}")
        logging.info(f"包名: {device.package_name}")

        # 启动录屏和监控
        device.start_screen_record()
        device.start_temp_monitor()
        device.start_log_monitor()
        
        # 设置2G网络环境
        logging.info("\n开始设置用例2网络环境...")
        logging.info("=" * 40)
        
        # 获取当前 WIFI 状态
        wifi_cmd = f"adb -s {device_id} shell settings get global wifi_on"
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"当前WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 启用 WIFI
        device.set_wifi_state(True)
        time.sleep(2)  # 等待 WIFI 状态变化
        
        # 检查 WIFI 是否已开启
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"开启后WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 设置为 2G 网络
        logging.info("设置移动网络为2G...")
        device.set_network_state('2g')
        time.sleep(2)  # 等待网络切换完成
        
        logging.info("=" * 40)
        
        logging.info("\n开始执行用例2前的准备工作")
        
        # 执行安装和清除操作，传入当前 device 对象
        device = run_install_and_clear(device_id, config, device)  # 传入已配置的 device 对象
        
        
        
        # 执行 monkey 测试
        duration = config.get('case_durations', {}).get('2', 2)  # 默认2分钟
        device.run_monkey(duration_minutes=duration)
        
    except Exception as e:
        logging.error(f"用例2执行失败: {e}")
        raise
    finally:
        if device:
            device.cleanup()

def run_test_case_3(device_id, config):
    """用例3: 正常WIFI环境测试"""
    try:
        # 创建设备控制器并设置配置
        device = DeviceController(device_id)
        device.package_name = config.get('package_name')
        device.apk_path = config.get('apk_path')  # 确保设置 APK 路径
        
        # 打印配置信息以便调试
        logging.info(f"用例3配置信息:")
        logging.info(f"APK路径: {device.apk_path}")
        logging.info(f"包名: {device.package_name}")

        # 启动录屏和监控
        device.start_screen_record()
        device.start_temp_monitor()
        device.start_log_monitor()
        
        # 设置正常WIFI环境
        logging.info("\n开始设置用例3网络环境...")
        logging.info("=" * 40)
        
        # 获取当前 WIFI 状态
        wifi_cmd = f"adb -s {device_id} shell settings get global wifi_on"
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"当前WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 启用 WIFI
        device.set_wifi_state(True)
        time.sleep(2)  # 等待 WIFI 状态变化
        
        # 检查 WIFI 是否已开启
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"开启后WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 设置为 4G 网络
        logging.info("设置移动网络为4G...")
        device.set_network_state('4g')
        time.sleep(2)  # 等待网络切换完成
        
        logging.info("=" * 40)
        
        logging.info("\n开始执行用例3前的准备工作")
        
        # 执行安装和清除操作，传入当前 device 对象
        device = run_install_and_clear(device_id, config, device)  # 传入已配置的 device 对象
        
        
        
        # 执行 monkey 测试
        duration = config.get('case_durations', {}).get('3', 2)  # 默认2分钟
        device.run_monkey(duration_minutes=duration)
        
    except Exception as e:
        logging.error(f"用例3执行失败: {e}")
        raise
    finally:
        if device:
            device.cleanup()

def run_test_case_4(device_id, config):
    """用例4: 2G网络+存储填充测试"""
    try:
        # 创建设备控制器并设置配置
        device = DeviceController(device_id)
        device.package_name = config.get('package_name')
        device.apk_path = config.get('apk_path')  # 确保设置 APK 路径
        
        # 打印配置信息以便调试
        logging.info(f"用例4配置信息:")
        logging.info(f"APK路径: {device.apk_path}")
        logging.info(f"包名: {device.package_name}")
        
        # 启动录屏和监控 - 移到执行用例前
        device.start_screen_record()
        device.start_temp_monitor()
        device.start_log_monitor()
        
        # 设置2G网络环境
        logging.info("\n开始设置用例4网络环境...")
        logging.info("=" * 40)
        
        # 获取当前 WIFI 状态
        wifi_cmd = f"adb -s {device_id} shell settings get global wifi_on"
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"当前WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 启用 WIFI
        device.set_wifi_state(True)
        time.sleep(2)  # 等待 WIFI 状态变化
        
        # 检查 WIFI 是否已开启
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"开启后WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 设置为 2G 网络
        logging.info("设置移动网络为2G...")
        device.set_network_state('2g')
        time.sleep(2)  # 等待网络切换完成
        
        logging.info("=" * 40)
        
        logging.info("\n开始执行用例4前的准备工作")
        
        # 执行安装和清除操作，传入当前 device 对象
        device = run_install_and_clear(device_id, config, device)
        
        # 填充存储到90%
        logging.info("开始填充存储空间...")
        try:
            while True:
                # 获取当前存储空间
                cmd = f"adb -s {device_id} shell df /data"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # 解析存储信息
                    info = lines[1].split()
                    total = int(info[1])  # 总空间 (KB)
                    used = int(info[2])   # 已用空间 (KB)
                    
                    # 计算当前使用率
                    current_usage = (used / total) * 100
                    logging.info(f"当前存储使用率: {current_usage:.1f}%")
                    
                    if current_usage >= 90:
                        logging.info("存储空间已达到90%，停止填充")
                        break
                    
                    # 创建2GB的填充文件
                    fill_size_mb = 2048  # 2GB = 2048MB
                    logging.info(f"正在填充 {fill_size_mb}MB 存储空间...")
                    
                    fill_file = f"/data/local/tmp/fill_{int(time.time())}"
                    cmd = f"adb -s {device_id} shell 'dd if=/dev/zero of={fill_file} bs=1048576 count={fill_size_mb}'"
                    subprocess.run(cmd, shell=True, check=True)
                    
                    # 等待3秒后继续填充
                    time.sleep(3)
                    
        except Exception as e:
            logging.error(f"填充存储空间失败: {e}")
            # 继续执行测试，不中断
        
        # 执行 monkey 测试
        duration = config.get('case_durations', {}).get('4', 2)  # 默认2分钟
        device.run_monkey(duration_minutes=duration)
        
    except Exception as e:
        logging.error(f"用例4执行失败: {e}")
        raise
    finally:
        if device:
            # 清理所有填充的存储空间
            try:
                cmd = f"adb -s {device_id} shell rm -f /data/local/tmp/fill_*"
                subprocess.run(cmd, shell=True)
                logging.info("已清理填充的存储空间")
            except Exception as e:
                logging.error(f"清理存储空间失败: {e}")
            
        device.cleanup()

def run_test_case_5(device_id, config):
    """用例5: 正常网络+多次Monkey测试"""
    try:
        # 创建设备控制器并设置配置
        device = DeviceController(device_id)
        device.package_name = config.get('package_name')
        device.apk_path = config.get('apk_path')  # 确保设置 APK 路径
        
        # 打印配置信息以便调试
        logging.info(f"用例5配置信息:")
        logging.info(f"APK路径: {device.apk_path}")
        logging.info(f"包名: {device.package_name}")

        # 启动录屏和监控
        device.start_screen_record()
        device.start_temp_monitor()
        device.start_log_monitor()
        
        # 设置正常网络环境
        logging.info("\n开始设置用例5网络环境...")
        logging.info("=" * 40)
        
        # 获取当前 WIFI 状态
        wifi_cmd = f"adb -s {device_id} shell settings get global wifi_on"
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"当前WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 启用 WIFI
        device.set_wifi_state(True)
        time.sleep(2)  # 等待 WIFI 状态变化
        
        # 检查 WIFI 是否已开启
        wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
        logging.info(f"开启后WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
        
        # 设置为 4G 网络
        logging.info("设置移动网络为4G...")
        device.set_network_state('4g')
        time.sleep(2)  # 等待网络切换完成
        
        logging.info("=" * 40)
        
        logging.info("\n开始执行用例5前的准备工作")
        
        # 执行安装和清除操作，传入当前 device 对象
        device = run_install_and_clear(device_id, config, device)  # 传入已配置的 device 对象
        
        
        
        # 循环执行10次 monkey 测试
        monkey_times = 10
        duration = config.get('case_durations', {}).get('5', 2)  # 默认2分钟
        
        logging.info(f"开始执行 {monkey_times} 次 Monkey 测试，每次 {duration} 分钟")
        
        for i in range(monkey_times):
            try:
                logging.info(f"\n开始第 {i+1}/{monkey_times} 次 Monkey 测试")
                device.run_monkey(duration_minutes=duration)
                logging.info(f"第 {i+1}/{monkey_times} 次 Monkey 测试完成")
                
                # 检查应用是否仍在运行
                try:
                    cmd = f"adb -s {device_id} shell ps | grep {device.package_name}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        logging.info("应用仍在运行")
                    else:
                        logging.warning("应用已停止，尝试重新启动")
                        device.launch_app()
                except Exception as e:
                    logging.warning(f"检查应用状态失败: {e}")
                    device.launch_app()  # 如果检查失败，尝试重启应用
                
                # 每次测试后等待5秒
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"第 {i+1}/{monkey_times} 次 Monkey 测试失败: {e}")
                # 继续执行下一次测试
                continue
        
        logging.info(f"\n{monkey_times} 次 Monkey 测试全部完成")
        
    except Exception as e:
        logging.error(f"用例5执行失败: {e}")
        raise
    finally:
        if device:
            device.cleanup()

def run_test_thread(self, device_id, config, selected_cases):
    """在新线程中运行测试"""
    try:
        logging.info(f"设备 {device_id} 开始测试")
        start_time = time.time()
        
        # 执行选中的测试用例
        test_cases = {
            "1": run_test_case_1,
            "2": run_test_case_2,
            "3": run_test_case_3,
            "4": run_test_case_4,
            "5": run_test_case_5
        }
        
        total_cases = len(selected_cases)
        successful_cases = 0
        failed_cases = []
        
        for i, case_num in enumerate(selected_cases, 1):
            try:
                logging.info(f"\n设备 {device_id} 开始执行用例 {case_num} ({i}/{total_cases})")
                test_cases[case_num](device_id, config)
                successful_cases += 1
                logging.info(f"设备 {device_id} 用例 {case_num} 执行完成")
            except Exception as e:
                logging.error(f"设备 {device_id} 用例 {case_num} 执行失败: {e}")
                failed_cases.append(case_num)
                continue
        
        # 计算总耗时
        total_time = int(time.time() - start_time)
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        seconds = total_time % 60
        
        # 打印测试总结
        logging.info("\n" + "="*50)
        logging.info("测试执行完成")
        logging.info(f"总用例数: {total_cases}")
        logging.info(f"成功用例: {successful_cases}")
        logging.info(f"失败用例: {len(failed_cases)}")
        if failed_cases:
            logging.info(f"失败用例列表: {', '.join(failed_cases)}")
        logging.info(f"总耗时: {hours}小时{minutes}分钟{seconds}秒")
        logging.info("="*50)
        logging.info("\n测试已完成！\n")
                
    except Exception as e:
        logging.error(f"设备 {device_id} 测试执行失败: {e}")
    finally:
        # 停止录屏
        if config.get('screen_process'):
            config['screen_process'].terminate()
            try:
                config['screen_process'].wait(timeout=5)
            except subprocess.TimeoutExpired:
                config['screen_process'].kill()

def main():
    # 获取设备ID
    try:
        cmd = "adb devices"
        output = subprocess.check_output(cmd, shell=True).decode()
        devices = [
            line.split()[0] for line in output.splitlines()[1:]
            if line.strip() and not line.strip().startswith('*')
        ]
        
        if not devices:
            logging.error("未找到已连接的设备")
            return
            
        device_id = devices[0]  # 使用第一个设备
        
        # 创建默认配置
        config = {
            'apk_path': None,  # 需要在运行前设置
            'package_name': None,  # 需要在运行前设置
            'install_times': 10,  # 默认值
            'clear_times': 10  # 默认值
        }
        
        # 运行测试用例
        run_test_thread(device_id, config, [1, 2, 3, 4, 5])
            
    except Exception as e:
        logging.error(f"测试执行失败: {e}")

if __name__ == "__main__":
    main()

# 确保这些函数在文件末尾被导出
__all__ = [
    'DeviceController',
    'run_install_and_clear',
    'run_test_thread',
    'run_test_case_1',
    'run_test_case_2',
    'run_test_case_3',
    'run_test_case_4',
    'run_test_case_5'
]
