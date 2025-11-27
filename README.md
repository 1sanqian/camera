# 4路摄像头监控系统

基于 PyQt6 的桌面应用程序，用于在 Ubuntu 系统上显示 4 路 USB 摄像头监控画面。

## 功能特点

- 主摄像头显示（640x480）- 显示在顶部
- 3 个副摄像头显示（320x240）- 横向排列在底部
- 使用 ffmpeg 通过 v4l2 捕获视频流
- 现代化的深色主题 UI
- 适合 Ubuntu 系统，可打包分发

## 系统要求

- Ubuntu 18.04 或更高版本
- Python 3.8 或更高版本
- ffmpeg（用于视频捕获）
- 4 个 USB 摄像头设备（/dev/video0, /dev/video1, /dev/video2, /dev/video3）

## 安装

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3-pip python3-dev
```

### 2. 安装 Python 依赖

```bash
pip3 install -r requirements.txt
```

或者sudo下载：

```bash
sudo apt install python3-pyqt6 python3-opencv python3-numpy
```

或者使用虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使用方法

### 直接运行

```bash
python3 main.py
```

### 安装为系统命令

```bash
pip3 install -e .
camera-monitor
```

## 打包

### 使用 PyInstaller 打包

```bash
pip3 install pyinstaller
pyinstaller --onefile --windowed --name camera-monitor main.py
```

打包后的可执行文件在 `dist/` 目录中。

### 使用 cx_Freeze 打包

```bash
pip3 install cx_Freeze
python3 setup_cx.py build
```

## 摄像头设备配置

确保您的摄像头设备已正确连接并被系统识别：

```bash
ls -l /dev/video*
```

如果设备不存在，可能需要：
1. 检查 USB 连接
2. 安装 v4l2 驱动
3. 检查用户权限（可能需要将用户添加到 video 组）

```bash
sudo usermod -a -G video $USER
```

然后重新登录。

## 故障排除

### 摄像头无法打开

- 检查设备路径是否正确
- 确认用户有访问 /dev/video* 的权限
- 检查 ffmpeg 是否支持 v4l2

### 视频流延迟

- 可以调整 framerate 参数（在 main.py 中）
- 检查 USB 带宽是否足够支持 4 路摄像头

## 许可证

MIT License

