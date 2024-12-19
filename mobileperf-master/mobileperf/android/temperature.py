import subprocess
import time
import datetime
# 导入 DB_utils.py 中的某个函数
from mobileperf.android.DB_utils import DatabaseOperations

def get_device_temperature(device):
    # 执行 ADB 命令获取设备温度，假设设备路径是 /sys/class/thermal/thermal_zone0/temp
    result = subprocess.run(
        ["adb", "shell", "cat", "/sys/class/thermal/thermal_zone0/temp"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # 如果命令成功执行，输出温度信息
    if result.returncode == 0:
        temperature = int(result.stdout.strip()) / 1000  # 转换为摄氏度
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} - 设备当前温度：{temperature} °C")
        # 插入设备温度数据
        db_operations = DatabaseOperations()

        try:

            # 查询新ids，用于区分新老数据
            latest_ids = db_operations.get_latest_ids(device)
            # Prepare fps_data for insertion into database
            temperature_data = {
                'device_id': device,
                'temperature': temperature,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'device_ids': latest_ids

            }
            db_operations.insert_temperature(temperature_data)


        except Exception as db_e:
            print(db_e)
            print("devices_info插入数据库失败！！")

    else:
        print("无法获取温度信息:", result.stderr)

def monitor_temperature():
    while True:
        get_device_temperature()  # 获取温度
        time.sleep(15)  # 每 15 秒获取一次

if __name__ == "__main__":
    monitor_temperature()
