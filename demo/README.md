# Android 应用自动化测试工具

这是一个用于 Android 应用自动化测试的工具，支持多种测试场景，包括网络环境测试、存储测试和 Monkey 测试等。

## 功能特点

1. 多设备支持
   - 支持同时连接多个设备
   - 可远程连接设备
   - 自动检测设备连接状态

2. 测试用例
   - 用例1：关闭 wifi 环境测试
   - 用例2：2G 网络环境测试
   - 用例3：正常 WIFI 环境测试
   - 用例4：极端环境测试（2G网络 + 存储填充）
   - 用例5：循环 Monkey 测试（10次）

3. 实时监控
   - 设备温度监控
   - 应用状态监控
   - 屏幕录制
   - 日志记录

4. 辅助功能
   - MTKlog 工具快速启动
   - 洋葱工具箱快速访问
   - 一键远程连接设备

## 环境要求

1. Python 环境
   - Python 3.x（推荐 3.8 或更高版本）
   - tkinter 支持（通常随 Python 安装）

2. Android 开发工具
   - Android SDK Platform Tools（用于 adb）
   - Android SDK Build Tools（用于 aapt/aapt2）

3. 系统要求
   - Windows/macOS/Linux 均可
   - 需要 USB 调试权限
   - 需要网络访问权限

## 安装步骤

1. Python 环境配置
   ```bash
   # 检查 Python 版本
   python --version  # 应显示 3.x 版本
   ```

2. Android 工具安装
   - 下载 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
   - 下载 [Android SDK Build Tools](https://developer.android.com/studio/releases/build-tools)

3. 环境变量配置
   ```bash
   # Windows (添加到系统环境变量 Path):
   C:\Users\<用户名>\AppData\Local\Android\sdk\platform-tools
   C:\Users\<用户名>\AppData\Local\Android\sdk\build-tools\<版本号>

   # macOS/Linux (添加到 ~/.bashrc 或 ~/.zshrc):
   export PATH=$PATH:~/Library/Android/sdk/platform-tools
   export PATH=$PATH:~/Library/Android/sdk/build-tools/<版本号>
   ```

4. 验证安装
   ```bash
   # 验证 adb
   adb version

   # 验证 aapt
   aapt version

   # 验证 aapt2
   aapt2 version
   ```

## 使用说明

1. 启动程序
   ```bash
   python gui.py
   ```

2. 基本操作流程
   - 连接 Android 设备（确保开启 USB 调试）
   - 点击"刷新设备"检查设备连接状态
   - 选择要测试的设备
   - 配置 APK 路径和包名
   - 设置安装次数和清除缓存次数
   - 选择要执行的测试用例
   - 设置每个用例的 Monkey 测试时长
   - 点击"开始测试"执行测试

3. 远程连接设备
   - 确保设备和电脑在同一网络
   - 选择设备
   - 点击"一键远程连接设备"
   - 等待连接成功提示

4. 查看测试结果
   - 测试日志保存在 logs 目录
   - 每次测试会创建独立的时间戳目录
   - 包含完整日志、温度记录、屏幕录制等

## 注意事项

1. 设备连接
   - 确保 USB 调试已启用
   - 首次连接需要在设备上确认授权
   - 远程连接需要设备和电脑在同一网络

2. APK 安装
   - 确保 APK 文件路径正确
   - 包名需要与 APK 匹配
   - 某些应用可能需要特殊权限

3. 测试执行
   - 建议先进行单个用例测试
   - 长时间测试建议连接充电器
   - 注意监控设备温度

4. 特殊说明
   - 葱管家清除缓存或覆盖安装后可能导致设备断开连接
   - 建议将相关用例的执行次数设为 0
   - 确保设备存储空间充足

## 常见问题

1. 设备无法连接
   - 检查 USB 线缆
   - 确认 USB 调试是否启用
   - 检查设备驱动是否正确安装

2. APK 安装失败
   - 确认 APK 文件完整性
   - 检查设备存储空间
   - 查看是否有安装权限

3. 测试中断
   - 检查设备连接状态
   - 查看日志确认具体原因
   - 确保网络环境稳定

## 日志说明

- test.log: 主测试日志
- temperature.log: 温度监控日志
- logcat.txt: 应用日志
- screen_record.mp4: 屏幕录制文件

## 联系支持

如有问题或建议，请联系：[your-email@example.com] 