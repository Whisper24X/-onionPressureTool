#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
import os
from datetime import datetime
import subprocess
import sys
import time
import random
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_controller import (
    DeviceController,
    run_install_and_clear,
    run_test_case_1,
    run_test_case_2,
    run_test_case_3,
    run_test_case_4,
    run_test_case_5
)

class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化测试工具")
        self.root.geometry("1200x600")
        
        # 添加窗口关闭处理

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            # 创建主框架
            self.create_main_frames()
            
            # 创建基本控件
            self.create_basic_widgets()
            
            # 配置日志
            self.setup_logging()
            
            # 启动设备监控
            self.root.after(2000, self.auto_refresh_devices)
            
            logging.info("应用程序启动完成")
            
        except Exception as e:
            print(f"初始化失败: {e}")
            raise
        
    def create_main_frames(self):
        """创建主框架"""
        # 左侧控制区域
        self.left_frame = ttk.Frame(self.root, padding="5")
        self.left_frame.pack(side='left', fill='y')
        
        # 右侧日志区域
        self.right_frame = ttk.Frame(self.root, padding="5")
        self.right_frame.pack(side='left', fill='both', expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
        
    def create_basic_widgets(self):
        """创建基本控件"""
        # 左侧：设备选择区域
        self.create_device_frame()
        
        # APK配置区域
        self.create_apk_frame()
        
        # 用例选择和配置
        cases_frame = ttk.LabelFrame(self.left_frame, text="测试用例", padding=5)
        cases_frame.pack(fill='x', pady=5)
        
        # 初始化用例选择变量
        self.case_vars = {}
        
        # 用例1：关闭wifi环境测试
        case1_frame = ttk.Frame(cases_frame)
        case1_frame.pack(fill='x', pady=2)
        self.case_vars["1"] = tk.BooleanVar()
        ttk.Checkbutton(case1_frame, text="1. 关闭wifi环境测试", 
                        variable=self.case_vars["1"]).pack(side='left')
        ttk.Label(case1_frame, text="Monkey时长:").pack(side='left', padx=(10,0))
        self.case1_duration = ttk.Entry(case1_frame, width=5)
        self.case1_duration.insert(0, "2")  # 改为2分钟
        self.case1_duration.pack(side='left', padx=2)
        ttk.Label(case1_frame, text="min").pack(side='left')
        
        # 用例2：2G网络环境测试
        case2_frame = ttk.Frame(cases_frame)
        case2_frame.pack(fill='x', pady=2)
        self.case_vars["2"] = tk.BooleanVar()
        ttk.Checkbutton(case2_frame, text="2. 2G网络环境测试", 
                        variable=self.case_vars["2"]).pack(side='left')
        ttk.Label(case2_frame, text="Monkey时长:").pack(side='left', padx=(10,0))
        self.case2_duration = ttk.Entry(case2_frame, width=5)
        self.case2_duration.insert(0, "2")  # 改为2分钟
        self.case2_duration.pack(side='left', padx=2)
        ttk.Label(case2_frame, text="min").pack(side='left')
        
        # 用例3：正常WIFI环境测试
        case3_frame = ttk.Frame(cases_frame)
        case3_frame.pack(fill='x', pady=2)
        self.case_vars["3"] = tk.BooleanVar()
        ttk.Checkbutton(case3_frame, text="3. 正常WIFI环境测试", 
                        variable=self.case_vars["3"]).pack(side='left')
        ttk.Label(case3_frame, text="Monkey时长:").pack(side='left', padx=(10,0))
        self.case3_duration = ttk.Entry(case3_frame, width=5)
        self.case3_duration.insert(0, "2")  # 改为2分钟
        self.case3_duration.pack(side='left', padx=2)
        ttk.Label(case3_frame, text="min").pack(side='left')
        
        # 用例4：极端环境测试
        case4_frame = ttk.Frame(cases_frame)
        case4_frame.pack(fill='x', pady=2)
        self.case_vars["4"] = tk.BooleanVar()
        ttk.Checkbutton(case4_frame, text="4. 极端环境测试（只包含2G网, 填充存储至90%）", 
                        variable=self.case_vars["4"]).pack(side='left')
        ttk.Label(case4_frame, text="Monkey时长:").pack(side='left', padx=(10,0))
        self.case4_duration = ttk.Entry(case4_frame, width=5)
        self.case4_duration.insert(0, "2")
        self.case4_duration.pack(side='left', padx=2)
        ttk.Label(case4_frame, text="min").pack(side='left')
        
        # 用例5：循环测试
        case5_frame = ttk.Frame(cases_frame)
        case5_frame.pack(fill='x', pady=2)
        self.case_vars["5"] = tk.BooleanVar()
        ttk.Checkbutton(case5_frame, text="5. 循环测试(循环执行Monkey次数10次)", 
                        variable=self.case_vars["5"]).pack(side='left')
        ttk.Label(case5_frame, text="Monkey时长:").pack(side='left', padx=(10,0))
        self.case5_duration = ttk.Entry(case5_frame, width=5)
        self.case5_duration.insert(0, "2")
        self.case5_duration.pack(side='left', padx=2)
        ttk.Label(case5_frame, text="min").pack(side='left')
        
        # 启动测试按钮
        start_btn = ttk.Button(self.left_frame, text="开始测试", command=self.run_test)
        start_btn.pack(pady=10)
        
        # 右侧：日志显示
        ttk.Label(self.right_frame, text="执行日志:").pack(anchor='w')
        self.log_text = scrolledtext.ScrolledText(self.right_frame, height=30)
        self.log_text.pack(fill='both', expand=True)
        
        # 初始化设备列表
        self.device_vars = {}
        self.refresh_devices()
        
    def create_device_frame(self):
        """创建设备选择区域"""
        # 设备选择区域
        device_frame = ttk.LabelFrame(self.left_frame, text="设备选择", padding=5)
        device_frame.pack(fill='x', pady=5)
        
        # 设备列表框架
        self.devices_list_frame = ttk.Frame(device_frame)
        self.devices_list_frame.pack(fill='x', expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(device_frame)
        button_frame.pack(fill='x', pady=2)
        
        # 刷新设备按钮
        ttk.Button(button_frame, text="刷新设备", command=self.refresh_devices).pack(side='left', padx=2)
        
        # 打开 Logger UI 按钮
        ttk.Button(button_frame, text="打开MTKlog（请打开后，点击平板上的开始按钮）", command=self.open_logger_ui).pack(side='left', padx=2)

        # 打开洋葱工具箱 - 禁用通知栏
        ttk.Button(button_frame, text="打开洋葱工具箱 - 禁用通知栏", command=self.disable_notice).pack(side='left', padx=2)

        # 远程连接设备
        ttk.Button(button_frame, text="一键远程连接设备", command=self.remote_connect_devices).pack(side='left', padx=2)



    def create_apk_frame(self):
        """创建APK配置区域"""
        # APK配置区域
        apk_frame = ttk.LabelFrame(self.left_frame, text="APK配置", padding=5)
        apk_frame.pack(fill='x', pady=5)
        
        # APK路径配置
        path_frame = ttk.Frame(apk_frame)
        path_frame.pack(fill='x', pady=2)
        ttk.Label(path_frame, text="APK路径:").pack(side='left')
        self.apk_path = ttk.Entry(path_frame)
        self.apk_path.pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(path_frame, text="浏览", command=self.browse_apk).pack(side='right')
        
        # 包名选择
        package_frame = ttk.Frame(apk_frame)
        package_frame.pack(fill='x', pady=2)
        ttk.Label(package_frame, text="包名:").pack(side='left')
        self.package_name = ttk.Combobox(package_frame, values=[
            'com.yangcong345.cloud.ui.launcher',    # 启动器UI
            'com.yangcong345.android.phone',        # 手机端
            'com.yangcong345.cloud.launcher',       # 启动器
            'com.yangcong345.pad.systemsetting',    # 系统设置
            'com.yangcong345.cloud.plan',           # 规划
            'com.yangcong345.cloud.toolbox',        # 工具箱
            'com.yangcong345.pad.market',           # 应用市场
            'com.yangcong345.eye.protection'        # 护眼
        ])
        self.package_name.pack(side='left', fill='x', expand=True, padx=2)
        # self.package_name.set('com.yangcong345.cloud.toolbox')  # 设置默认值已注释
        
        # 安装次数配置
        install_frame = ttk.Frame(apk_frame)
        #root = tk.Tk()
        install_frame.pack(fill='x', pady=2)
        ttk.Label(install_frame, text="安装次数:").pack(side='left')
        self.install_times = ttk.Entry(install_frame, width=10)
        self.install_times.pack(side='left', padx=2)
        self.install_times.insert(0, "2")

        label1 = ttk.Frame(apk_frame)
        label1.pack(fill='x', pady=2)
        ttk.Label(label1, text="注：【葱管家】清除缓存或覆盖安装后，可能导致设备失去连接，建议把这2个case的值设置为0，以免影响测试进程！", foreground="red").pack(side='left')
        
        
        # 清除缓存次数配置
        clear_frame = ttk.Frame(apk_frame)
        clear_frame.pack(fill='x', pady=2)
        ttk.Label(clear_frame, text="清除缓存次数:").pack(side='left')
        self.clear_times = ttk.Entry(clear_frame, width=10)
        self.clear_times.pack(side='left', padx=2)
        self.clear_times.insert(0, "2")

        label2 = ttk.Frame(apk_frame)
        label2.pack(fill='x', pady=2)
        ttk.Label(label2, text="注：【葱管家】清除缓存或覆盖安装后，可能导致设备失去连接，建议把这2个case的值设置为0，以免影响测试进程！", foreground="red").pack(side='left')

    def setup_logging(self):
        """设置日志"""
        # 创建日志目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join("logs", timestamp)
        os.makedirs(log_dir, exist_ok=True)
        
        # 移除所有现有的处理器
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 设置日志级别
        logger.setLevel(logging.INFO)
        
        # 创建自定义处理器，将日志输出到GUI
        class GUIHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                self.formatter = logging.Formatter('%(asctime)s - %(message)s', 
                                                datefmt='%Y-%m-%d %H:%M:%S')
        
            def emit(self, record):
                msg = self.formatter.format(record)
                self.text_widget.insert('end', msg + '\n')
                self.text_widget.see('end')  # 自动滚动到最新日志
                self.text_widget.update()  # 立即更新界面
        
        # 添加GUI处理器
        gui_handler = GUIHandler(self.log_text)
        logger.addHandler(gui_handler)
        
        # 添加文件处理器
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "test.log"),
            encoding='utf-8'
        )
        file_handler.setFormatter(gui_handler.formatter)
        logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(gui_handler.formatter)
        logger.addHandler(console_handler)
        
    def refresh_devices(self):
        """刷新设备列表"""
        try:
            # 清除现有设备列表
            for widget in self.devices_list_frame.winfo_children():
                widget.destroy()
            self.device_vars.clear()
            
            # 获取已连接设备
            devices = self.get_connected_devices()
            
            if not devices:
                ttk.Label(self.devices_list_frame, text="未发现设备").pack()
                return
                
            # 添加新设备到列表
            for device_id in devices:
                var = tk.BooleanVar()
                self.device_vars[device_id] = var
                ttk.Checkbutton(
                    self.devices_list_frame,
                    text=device_id,
                    variable=var
                ).pack(anchor='w')
                
            logging.info(f"已刷新设备列表，发现 {len(devices)} 个设备")
            
        except Exception as e:
            logging.error(f"刷新设备列表失败: {e}")

    def browse_apk(self):
        """选择APK文件"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择APK文件",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")]
        )
        if filename:
            self.apk_path.insert(0, filename)

    def validate_configs(self):
        """验证所有配置"""
        try:
            # 验证是否选择了测试用例
            selected_cases = [num for num, var in self.case_vars.items() if var.get()]
            if not selected_cases:
                raise ValueError("请至少选择一个测试用例")
            
            # 验证是否选择了设备
            selected_devices = [
                device_id for device_id, var in self.device_vars.items() 
                if var.get()
            ]
            if not selected_devices:
                raise ValueError("请选择至少一个设备")
            
            # 验证APK路径
            apk_path = self.apk_path.get().strip()
            if not apk_path:
                raise ValueError("请选择APK文件")
            if not os.path.exists(apk_path):
                raise ValueError("APK文件不存在")
            if not apk_path.endswith('.apk'):
                raise ValueError("不是有效的APK文件")
            
            # 验证包名选择
            package_name = self.package_name.get().strip()
            if not package_name:
                raise ValueError("请选择测试包名")
            
            # 验证安装次数
            install_times = self.install_times.get().strip()
            if not install_times:
                raise ValueError("请输入安装次数")
            install_times = int(install_times)
            if install_times <= 0:
                raise ValueError("安装次数必须大于0")
            
            # 验证清除缓存次数
            clear_times = self.clear_times.get().strip()
            if not clear_times:
                raise ValueError("请输入清除缓存次数")
            clear_times = int(clear_times)
            if clear_times < 0:
                raise ValueError("清除缓存次数不能小于0")
            
            # 验证所有选中用例的配置
            for case_num in selected_cases:
                config = self.case_vars[case_num]
                
                # 验证时长
                duration = self.case1_duration.get().strip()
                if not duration:
                    raise ValueError(f"请为用例 {case_num} 输入Monkey执行时长")
                duration = float(duration)
                if duration <= 0:
                    raise ValueError(f"用例 {case_num} 的执行时长必须大于0")
                
                # 验证间隔
                interval = self.case1_duration.get().strip()
                if not interval:
                    raise ValueError(f"请为用例 {case_num} 输入事件间隔")
                interval = int(interval)
                if interval < 100:
                    raise ValueError(f"用例 {case_num} 的事件间隔不能小于100ms")
                
            return True
            
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return False

    def run_test_with_config(self, test_func, device_id):
        """使用自定义配置运行测试"""
        from test_controller import (
            DeviceController, 
            run_test_case_1, 
            run_test_case_2, 
            run_test_case_3, 
            run_test_case_4, 
            run_test_case_5
        )
        
        # 保存原始方法
        original_run_monkey = DeviceController.run_monkey
        original_init = DeviceController.__init__
        original_install_app = DeviceController.install_app
        original_clear_cache = DeviceController.clear_app_cache
        
        # 测试用例映射
        test_cases_map = {
            run_test_case_1: "1",
            run_test_case_2: "2",
            run_test_case_3: "3",
            run_test_case_4: "4",
            run_test_case_5: "5"
        }
        
        try:
            # 修改初始化方法以使用选择的包名
            def modified_init(self, device_id):
                original_init(self, device_id)
                self.apk_path = self.root.apk_path.get()
                self.package_name = self.root.package_name.get()
                # 保存原始安装次数和清除缓存次数
                self._original_install_times = int(self.root.install_times.get())
                self._original_clear_times = int(self.root.clear_times.get())
                self._install_count = 0  # 添加安装计数器
                logging.info(f"将对包 {self.package_name} 执行测试")
            
            # 修改安装方法以使用自定义次数
            def modified_install_app(self, times=None):
                if times is None and hasattr(self, '_original_install_times'):
                    # 检查是否已经执行过完整的安装测试
                    if self._install_count >= 1:
                        times = 1  # 后续的安装只执行一次
                    else:
                        times = self._original_install_times
                        self._install_count += 1
                return original_install_app(self, times)
            
            # 修改清除缓存方法以使用自定义次数
            def modified_clear_cache(self):
                if hasattr(self, '_original_clear_times'):
                    times = self._original_clear_times
                    for i in range(times):
                        try:
                            logging.info(f"开始第 {i+1}/{times} 次清除缓存")
                            cmd = f"adb -s {self.device_id} shell pm clear {self.package_name}"
                            subprocess.check_call(cmd, shell=True)
                            logging.info(f"第 {i+1}/{times} 次清除缓存完成")
                        except Exception as e:
                            logging.error(f"第 {i+1}/{times} 次清除缓存失败: {e}")
                            raise
                else:
                    return original_clear_cache(self)
            
            # 修改Monkey方法
            def modified_run_monkey(self, duration_minutes=None, interval=None):
                # 获取当前正在执行的用例编号
                current_case = test_cases_map.get(test_func)
                
                if current_case and current_case in self.root.case_vars:
                    config = self.root.case_vars[current_case]
                    if duration_minutes is None:
                        duration = float(self.case1_duration.get())
                        if config['unit'] == 'hour':
                            duration *= 60
                        duration_minutes = int(duration)
                    
                    if interval is None:
                        interval = int(self.case1_duration.get())
                    
                    logging.info(f"开始执行Monkey测试 - 时长: {duration_minutes}分钟, 间隔: {interval}ms")
                    return original_run_monkey(self, duration_minutes, interval)
                else:
                    logging.error(f"未找到用例配置")
                    raise ValueError("未找到用例配置")
            
            # 应用修改后的方法
            DeviceController.__init__ = modified_init
            DeviceController.install_app = modified_install_app
            DeviceController.run_monkey = modified_run_monkey
            DeviceController.clear_app_cache = modified_clear_cache
            DeviceController.root = self
            
            # 运行测试
            test_func(device_id)
            
        finally:
            # 恢复原始方法
            DeviceController.__init__ = original_init
            DeviceController.install_app = original_install_app
            DeviceController.run_monkey = original_run_monkey
            DeviceController.clear_app_cache = original_clear_cache
            if hasattr(DeviceController, 'root'):
                delattr(DeviceController, 'root')

    def start_test(self):
        """开始测试"""
        # 导入测试用例
        from test_controller import (
            DeviceController, 
            run_test_case_1, 
            run_test_case_2, 
            run_test_case_3, 
            run_test_case_4, 
            run_test_case_5
        )
        
        if hasattr(self, 'test_threads') and any(t.is_alive() for t in self.test_threads):
            messagebox.showwarning("警告", "测试正在进行中")
            return
        
        # 验证所有配置
        if not self.validate_configs():
            return
        
        # 获取选中的设备
        selected_devices = [
            device_id for device_id, var in self.device_vars.items() 
            if var.get()
        ]
        
        # 清空日志
        self.log_text.delete('1.0', 'end')
        
        # 禁用开始按钮
        self.start_btn.state(['disabled'])
        self.status_var.set("测试进行中...")
        
        # 测试用例映射
        test_cases = {
            "1": run_test_case_1,
            "2": run_test_case_2,
            "3": run_test_case_3,
            "4": run_test_case_4,
            "5": run_test_case_5
        }
        
        # 获取选中的用例编号，按顺序排序
        selected_cases = sorted([num for num, var in self.case_vars.items() if var.get()])
        
        def run_test_on_device(device_id):
            try:
                logging.info(f"设备 {device_id} 开始测试")
                
                # 按顺序执行选中的测试用例
                total_cases = len(selected_cases)
                for index, case_num in enumerate(selected_cases, 1):
                    try:
                        logging.info(f"\n设备 {device_id} 开始执行用例 {case_num} ({index}/{total_cases})")
                        test_func = test_cases[case_num]
                        self.run_test_with_config(test_func, device_id)
                        logging.info(f"设备 {device_id} 用例 {case_num} 执行完成")
                    except Exception as e:
                        logging.error(f"设备 {device_id} 用例 {case_num} 执行失败: {str(e)}")
                        raise
                
                logging.info(f"设备 {device_id} 测试完成")
                
            except Exception as e:
                logging.error(f"设备 {device_id} 测试执行失败: {str(e)}")
        
        # 为每个设备创建测试线程
        self.test_threads = []
        for device_id in selected_devices:
            thread = threading.Thread(target=run_test_on_device, args=(device_id,))
            thread.daemon = True
            self.test_threads.append(thread)
            thread.start()
        
        # 启动监控线程
        def monitor_threads():
            if all(not t.is_alive() for t in self.test_threads):
                self.status_var.set("测试完成")
                self.start_btn.state(['!disabled'])
                messagebox.showinfo("完成", "所有设备测试完成")
            else:
                self.root.after(1000, monitor_threads)
        
        self.root.after(1000, monitor_threads)

    def auto_refresh_devices(self):
        """自动刷新设备列表"""
        try:
            # 获取当前和新的设备列表
            current_devices = set(self.device_vars.keys())
            new_devices = set(self.get_connected_devices())
            
            # 如果设备列表有变化，刷新界面
            if current_devices != new_devices:
                self.refresh_devices()
                
                # 如果有新增设备，显示通知
                added_devices = new_devices - current_devices
                if added_devices:
                    for device in added_devices:
                        logging.info(f"新设备已连接: {device}")
                
                # 如果有设备断开，显示通知
                removed_devices = current_devices - new_devices
                if removed_devices:
                    for device in removed_devices:
                        logging.warning(f"设备已断开: {device}")
        except Exception as e:
            logging.error(f"刷新设备列表失败: {e}")
        finally:
            # 继续定时刷新
            self.root.after(2000, self.auto_refresh_devices)

    def get_connected_devices(self):
        """获取已连接的设备列表"""
        try:
            cmd = "adb devices"
            output = subprocess.check_output(cmd, shell=True).decode()
            devices = [
                line.split()[0] for line in output.splitlines()[1:]
                if line.strip() and not line.strip().startswith('*')
            ]
            return devices
        except:
            return []

    def run_test(self):
        try:
            # 获取选中的设备
            device_id = self.get_selected_device()
            if not device_id:
                logging.error("未选择设备")
                return
                
            # 创建录屏目录
            screen_dir = os.path.join("demo", "screen", device_id)
            os.makedirs(screen_dir, exist_ok=True)
            
            # 启动录屏
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screen_file = os.path.join(screen_dir, f"screen_{timestamp}.mp4")
            temp_screen_file = f"/sdcard/screen_{timestamp}.mp4"
            
            # 构建录屏命令
            cmd = f"adb -s {device_id} shell screenrecord {temp_screen_file}"
            screen_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 收集配置
            config = {
                'package_name': self.package_name.get(),
                'apk_path': self.apk_path.get().strip(),  # 确保添加APK路径
                'install_times': int(self.install_times.get()),
                'clear_times': int(self.clear_times.get()),
                'case_durations': {
                    '1': int(self.case1_duration.get()),
                    '2': int(self.case2_duration.get()),
                    '3': int(self.case3_duration.get()),
                    '4': int(self.case4_duration.get()),
                    '5': int(self.case5_duration.get())
                },
                'screen_file': screen_file,
                'temp_screen_file': temp_screen_file,
                'screen_process': screen_process
            }
            
            # 获取选中的用例
            selected_cases = []
            for case_num, var in self.case_vars.items():
                if var.get():
                    selected_cases.append(case_num)
            
            if not selected_cases:
                logging.error("未选择测试用例")
                return
                
            # 启动测试线程
            test_thread = threading.Thread(
                target=self.run_test_thread,
                args=(device_id, config, selected_cases)
            )
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            logging.error(f"执行测试失败: {e}")
            # 如果出错，确保停止录屏
            if 'screen_process' in locals():
                screen_process.terminate()

    def run_test_thread(self, device_id, config, selected_cases):
        """在新线程中运行测试"""
        try:
            logging.info(f"设备 {device_id} 开始测试")
            
            # 创建设备控制器
            device = DeviceController(device_id)
            
            # 直接使用传入的 config 中的 APK 路径和包名
            device.package_name = config.get('package_name')
            device.apk_path = config.get('apk_path')
            
            # 打印配置信息以便调试
            logging.info(f"配置信息:")
            logging.info(f"APK路径: {device.apk_path}")
            logging.info(f"包名: {device.package_name}")
            
            # 如果选择了用例1，先禁用 WIFI
            if "1" in selected_cases:
                logging.info("\n开始设置用例1网络环境...")
                logging.info("=" * 40)
                
                # 获取当前 WIFI 状态
                wifi_cmd = f"adb -s {device_id} shell settings get global wifi_on"
                wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
                logging.info(f"当前WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
                
                # 禁用 WIFI
                device.set_wifi_state(False)
                time.sleep(2)  # 等待 WIFI 状态变化
                
                # 检查 WIFI 是否已关闭
                wifi_result = subprocess.run(wifi_cmd, shell=True, capture_output=True, text=True)
                logging.info(f"关闭后WIFI状态: {'开启' if wifi_result.stdout.strip() == '1' else '关闭'}")
                logging.info("=" * 40)
            
            # 执行选中的测试用例
            test_cases = {
                "1": run_test_case_1,
                "2": run_test_case_2,
                "3": run_test_case_3,
                "4": run_test_case_4,
                "5": run_test_case_5
            }
            
            total_cases = len(selected_cases)
            for i, case_num in enumerate(selected_cases, 1):
                try:
                    logging.info(f"\n设备 {device_id} 开始执行用例 {case_num} ({i}/{total_cases})")
                    test_cases[case_num](device_id, config)
                except Exception as e:
                    logging.error(f"设备 {device_id} 用例 {case_num} 执行失败: {e}")
                    continue
            
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
                logging.info(f"录屏已保存至: {config.get('screen_file')}")

    def get_selected_device(self):
        """获取选中的设备"""
        try:
            # 遍历设备变量字典，找到选中的设备
            for device_id, var in self.device_vars.items():
                if var.get():
                    return device_id
            return None
        except Exception as e:
            logging.error(f"获取选中设备失败: {e}")
            return None

    def open_logger_ui(self):
        """打开 Logger UI 工具"""
        try:
            device_id = self.get_selected_device()
            if not device_id:
                messagebox.showwarning("警告", "请先选择设备")
                return
            
            # 检查设备是否仍然连接
            if device_id not in self.get_connected_devices():
                messagebox.showerror("错误", "设备已断开连接")
                return
            
            # 检查 Logger UI 应用是否已安装
            check_cmd = f"adb -s {device_id} shell pm list packages | grep com.debug.loggerui"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if not result.stdout.strip():
                messagebox.showerror("错误", "Logger UI 应用未安装")
                return
            
            # 启动 Logger UI
            cmd = f"adb -s {device_id} shell am start -n com.debug.loggerui/.MainActivity"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if "Error" in result.stderr:
                raise Exception(result.stderr)
            
            logging.info(f"已在设备 {device_id} 上打开日志工具")
            
        except Exception as e:
            error_msg = f"打开日志工具失败: {str(e)}"
            logging.error(error_msg)
            messagebox.showerror("错误", error_msg)

    def disable_notice(self):
        # 禁用通知栏
        try:
            device_id = self.get_selected_device()
            if not device_id:
                messagebox.showwarning("警告", "请先选择设备")
                return
            # 检查设备是否仍然连接
            if device_id not in self.get_connected_devices():
                messagebox.showerror("错误", "设备已断开连接")
                return
            check_cmd = f"adb -s {device_id} shell am start -n com.yangcong345.cloud.toolbox/com.yangcong345.cloud.lib_debugtool.debug.DebugToolActivity"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

            if "Error" in result.stderr:
                raise Exception(result.stderr)
            
            logging.info(f"已在设备 {device_id} 上打开洋葱工具箱")

        except Exception as e:
            error_msg = f"打开洋葱工具箱失败：{str(e)}"
            logging.error(error_msg)
            messagebox.showerror("错误", error_msg)

    def remote_connect_devices(self):
        """远程连接设备"""
        try:
            device_id = self.get_selected_device()
            if not device_id:
                messagebox.showwarning("警告", "请先选择设备")
                return
            
            # 检查设备是否仍然连接
            if device_id not in self.get_connected_devices():
                messagebox.showerror("错误", "设备已断开连接")
                return
            
            # 生成随机端口号
            random_port = random.randint(1000, 9999)
            
            # 设置设备为 TCP/IP 模式
            cmd_tcpip = f"adb -s {device_id} tcpip {random_port}"
            result = subprocess.run(cmd_tcpip, shell=True, capture_output=True, text=True)
            
            if "error" in result.stderr.lower():
                raise Exception(result.stderr)
            logging.info(f"已设置设备 {device_id} 为 TCP/IP 模式，端口: {random_port}")
            
            time.sleep(2)  # 等待 TCP/IP 模式生效
            
            # 获取设备 IP 地址
            cmd = f"adb -s {device_id} shell ip addr show wlan0"
            try:
                output = subprocess.check_output(cmd, shell=True, text=True)
                # 使用正则表达式匹配 IP 地址
                import re
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/', output)
                if not ip_match:
                    raise Exception("未找到设备 IP 地址")
                device_ip = ip_match.group(1)
                logging.info(f"获取到设备 IP 地址: {device_ip}")
                
            except Exception as e:
                error_msg = f"获取设备 IP 地址失败: {str(e)}"
                logging.error(error_msg)
                messagebox.showerror("错误", error_msg)
                return
            
            time.sleep(2)  # 等待连接准备就绪
            
            # 执行远程连接
            connect_cmd = f"adb connect {device_ip}:{random_port}"
            result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
            
            if "connected" in result.stdout.lower():
                logging.info(f"已成功连接到设备 {device_ip}:{random_port}")
                messagebox.showinfo("成功", f"已连接到设备 {device_ip}:{random_port}")
            else:
                raise Exception(f"连接失败: {result.stderr}")
            
        except Exception as e:
            error_msg = f"远程连接设备失败: {str(e)}"
            logging.error(error_msg)
            messagebox.showerror("错误", error_msg)
    
    

    def on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 获取所有已连接的设备
            devices = self.get_connected_devices()
            for device_id in devices:
                try:
                    # 对每个设备执行清理
                    device = DeviceController(device_id)
                    device.cleanup()
                except Exception as e:
                    logging.error(f"清理设备 {device_id} 失败: {e}")
        except Exception as e:
            logging.error(f"关闭窗口时清理失败: {e}")
        finally:
            # 确保窗口关闭
            self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = TestApp(root)
        
        # 添加异常处理
        def handle_exception(exc_type, exc_value, exc_traceback):
            logging.error("程序异常退出", exc_info=(exc_type, exc_value, exc_traceback))
            # 清理所有设备
            try:
                devices = app.get_connected_devices()
                for device_id in devices:
                    try:
                        device = DeviceController(device_id)
                        device.cleanup()
                    except:
                        pass
            except:
                pass
            # 确保程序退出
            root.quit()
        
        # 设置异常处理器
        sys.excepthook = handle_exception
        
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 