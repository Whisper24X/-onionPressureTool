# Perf

环境搭建：
Windows系统
Python 3+
代码编辑器：PyCharm，VScode


1. 使用Git clone下来，这个项目 https://github.com/Whisper24X/Perf
2. 使用Windows电脑，代码编辑器打开项目
3. 连接devices【支持多台】
连接方式 1

- 直连方式
使用USB连接电脑即可
连接方式 2
- tcpip连接
与系统环境保持同一个网络，使用tcpip方式连接
```
adb -s snid shell ifconfig
  
adb -s snid tcpip 5555
  
adb connect snid-ip:5555
```

3. 运行前，可检测配置文件是否正确：
config.conf配置文件
``` shell

config.conf配置文件
[Common]
#填写包名，必填
package=com.yangcong345.android.phone
#采集频率
frequency=5
#collect timeout ,int type ,unit:minute, for example:72 hours 4320
timeout=4320
#dumpheap frequency, int type,unit: minute
dumpheap_freq=60
#adb serialnum,adb devices result example WSKFSKBQLFA695D6
serialnum=192.168.10.38:7777
#except log tag,tools will check in logcat,save exception log in exception.log,multi tags separate use ;
exceptionlog=fatal exception;has died
#monkey命令，可指定包或者不指定包进行跑
monkey=adb shell monkey -v -v --throttle 500 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -s 8888 -v 2880000
#test results save path,forbidden space, default None,will save in mobileperf/results
#example  save_path=/Users/look/Desktop/project/mobileperf_output
save_path=
#device pull path,test end,tool pull path to PC,multi path separate use;
phone_log_path=/data/anr
#mailbox Reserved, no use
mailbox=390125133@qq.com
4. 打开项目，打开Perf/adbconnect.py，点击run，运行后，会自动生成该设备性能数据采集文件夹
数据文件夹在目录：
Perf/R/设备id/results

```

5. 可采集的数据范围，验证过的有
``` python
logs：开发看是否存在crash/anr
logcat-log：开发看是否存在crash/anr
cpuinfo.csv
device_cpu_rate%
user%
pid_cpu%
meminfo.csv
free_ram(MB)
pid_pss(MB)
fps
jank
```

6. Android系统兼容性
``` python
Android 5-11执行方式：
使用 adbconnect.py 执行文件进行执行

Android 13 执行方式：
使用 adbconnect_Android13.py 执行文件进行执行

```
7. 支持部署的系统
``` python
支持Windows
支持Mac
```

可采集的数据范围，验证过的有logs：开发看是否存在crash/anr
logcat-log：开发看是否存在crash/anr
cpuinfo.csv
 device_cpu_rate%
 user%
 pid_cpu%
meminfo.csv
 free_ram(MB)
 pid_pss(MB)





