# #!/bin/bash
#
# # 启动 ADB 服务器
# adb start-server
#
# # 等待几秒钟确保 ADB 服务已经启动
# sleep 5
#
# # 列出已连接的设备
# devices=$(adb devices | grep 'device$' | cut -f1)
#
# for device in $devices
# do
#   echo "正在切换设备 $device 到 TCP/IP 模式..."
#
#   # 设置设备为 TCP/IP 模式，端口为 5555
#   adb -s $device tcpip 5555
#
#   # 再次等待几秒钟
#   sleep 5
#
#   # 获取设备的 IP 地址
#   device_ip=$(adb -s $device shell ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | head -n 1)
#
#   # 通过 IP 连接设备
#   if [[ -n "$device_ip" ]]; then
#     adb connect $device_ip:5555
#     echo "已连接设备: $device_ip"
#   else
#     echo "无法获取设备 IP"
#   fi
# done
#
# # 保持容器运行
# tail -f /dev/null

#---

#!/bin/bash

#!/bin/bash

# 启动 ADB 服务器
adb start-server

# 等待几秒钟确保 ADB 服务已经启动
sleep 5

# 获取设备的 IP 地址
device_ip=$(adb shell ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | head -n 1)

# 通过 IP 连接设备
if [[ -n "$device_ip" ]]; then
  adb connect $device_ip:5555
  echo "已连接设备: $device_ip"
else
  echo "无法获取设备 IP"
fi
# #!/bin/bash
#
# # 启动 ADB 服务器
# adb start-server
#
# # 等待几秒钟确保 ADB 服务已经启动
# sleep 5
#
# # 列出已连接的设备
# devices=$(adb devices | grep 'device$' | cut -f1)
#
# for device in $devices
# do
#   echo "正在切换设备 $device 到 TCP/IP 模式..."
#
#   # 设置设备为 TCP/IP 模式，端口为 5555
#   adb -s $device tcpip 5555
#
#   # 再次等待几秒钟
#   sleep 5
#
#   # 获取设备的 IP 地址
#   device_ip=$(adb -s $device shell ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | head -n 1)
#
#   # 通过 IP 连接设备
#   if [[ -n "$device_ip" ]]; then
#     adb connect $device_ip:5555
#     echo "已连接设备: $device_ip"
#   else
#     echo "无法获取设备 IP"
#   fi
# done
#
# # 保持容器运行
# tail -f /dev/null

#---

#!/bin/bash

#!/bin/bash

#!/bin/bash

# 启动 ADB 服务器
adb start-server

# 等待几秒钟确保 ADB 服务已经启动
sleep 5

# 列出已连接的设备
devices=$(adb devices | grep 'device$' | cut -f1)

if [[ -z "$devices" ]]; then
  echo "未找到设备，尝试通过 TCP/IP 连接"
  # 这里可以硬编码设备的 IP，或者根据需要获取
  device_ip="<your_device_ip>"
  adb connect $device_ip:5555
else
  for device in $devices; do
    echo "找到设备: $device"
  done
fi

# 保持容器运行
tail -f /dev/null

