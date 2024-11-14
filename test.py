from uiautomator import Device
import subprocess
import time

# 连接设备
d = Device()
subprocess.run(["adb", "shell", "am", "start", "-n", "com.debug.loggerui/.MainActivity"])
time.sleep(2)  # 增加一些延迟等待界面加载完成
# 点击指定元素
d(resourceId='com.debug.loggerui:id/startStopToggleButton').click()
time.sleep(4)  # 增加一些延迟等待界面加载完成
# 回到主屏幕
subprocess.run(['adb', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])
