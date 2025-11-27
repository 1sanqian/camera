#!/usr/bin/env python3
"""
4-Camera Monitoring System
Main application for displaying 4 USB camera feeds
"""

import sys
import subprocess
import threading
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np


class VideoStreamThread(QThread):
    """Thread for capturing video stream from ffmpeg"""
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, device_path, width, height, max_fps=15, input_format='mjpeg', retry_count=3):
        super().__init__()
        self.device_path = device_path
        self.width = width
        self.height = height
        self.running = False
        self.process = None
        self.max_fps = max_fps
        self.frame_interval = 1.0 / max_fps if max_fps > 0 else 0
        self.last_frame_time = 0
        self.input_format = input_format
        self.retry_count = retry_count
        self.error_count = 0
        
    def run(self):
        self.running = True
        frame_size = self.width * self.height * 3
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running and self.error_count < self.retry_count * 10:
            try:
                # Use ffmpeg to capture video stream
                # 添加线程优先级和缓冲区优化
                cmd = [
                    'ffmpeg',
                    '-f', 'v4l2',
                    '-framerate', str(self.max_fps),
                    '-video_size', f'{self.width}x{self.height}',
                    '-input_format', self.input_format,
                    '-thread_queue_size', '512',  # 增加线程队列大小
                    '-i', self.device_path,
                    '-f', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-loglevel', 'error',  # 只显示错误
                    '-'
                ]
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=frame_size * 2  # 增加缓冲区大小
                )
                
                consecutive_errors = 0
                
                while self.running:
                    # 确保读取完整的帧数据
                    raw_frame = b''
                    timeout_count = 0
                    while len(raw_frame) < frame_size:
                        chunk = self.process.stdout.read(frame_size - len(raw_frame))
                        if not chunk:
                            timeout_count += 1
                            if timeout_count > 10:  # 超时重试
                                break
                            time.sleep(0.01)
                            continue
                        raw_frame += chunk
                        timeout_count = 0
                    
                    if len(raw_frame) != frame_size:
                        consecutive_errors += 1
                        if consecutive_errors > max_consecutive_errors:
                            break
                        # 短暂延迟后重试
                        time.sleep(0.1)
                        continue
                    
                    consecutive_errors = 0
                    
                    # 帧率控制：限制发送帧的频率
                    current_time = time.time()
                    if current_time - self.last_frame_time >= self.frame_interval:
                        try:
                            # 创建副本以避免内存共享问题
                            frame = np.frombuffer(raw_frame, dtype=np.uint8).copy()
                            frame = frame.reshape((self.height, self.width, 3))
                            # 确保数据是连续的
                            frame = np.ascontiguousarray(frame)
                            # 验证帧数据有效性
                            if frame.size == frame_size and frame.max() > 0:
                                self.frame_ready.emit(frame)
                                self.last_frame_time = current_time
                        except Exception as e:
                            # 帧处理错误，跳过这一帧
                            pass
                
            except Exception as e:
                self.error_count += 1
                consecutive_errors += 1
                print(f"Error in video stream {self.device_path}: {e}")
                if self.process:
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=1)
                    except:
                        try:
                            self.process.kill()
                        except:
                            pass
                
                # 如果错误太多，等待更长时间再重试
                if consecutive_errors > 5:
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)
            
            finally:
                if self.process:
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=1)
                    except:
                        try:
                            self.process.kill()
                        except:
                            pass
                    self.process = None
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()


class VideoLabel(QLabel):
    """Custom QLabel for displaying video frames"""
    
    def __init__(self, width, height, label_text=""):
        super().__init__()
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 4px;
            }
        """)
        if label_text:
            self.setText(label_text)
            self.setStyleSheet(self.styleSheet() + """
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                }
            """)
    
    def set_frame(self, frame):
        """Update the label with a new frame"""
        if frame is not None and frame.size > 0:
            try:
                # 确保帧数据是连续的副本，避免线程安全问题
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)
                
                height, width, channel = frame.shape
                if channel != 3:
                    return
                    
                bytes_per_line = 3 * width
                # 使用 frame.copy() 确保数据安全
                frame_copy = frame.copy()
                q_image = QImage(frame_copy.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
                pixmap = QPixmap.fromImage(q_image)
                self.setPixmap(pixmap.scaled(
                    self.width(), 
                    self.height(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            except Exception as e:
                # 静默处理错误，避免崩溃
                pass


class CameraMonitorApp(QMainWindow):
    """Main application window for 4-camera monitoring"""
    
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("4路摄像头监控")
        self.setGeometry(100, 100, 1000, 700)
        
        # Camera devices
        self.devices = ['/dev/video2', '/dev/video0', '/dev/video1', '/dev/video3']
         
        # Video threads
        self.video_threads = []
        
        # Setup UI
        self.setup_ui()
        
        # Start video streams
        self.start_streams()
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 5, 10, 0)
        
        # Main camera view (640x480)
        self.main_view = VideoLabel(640, 480, "Front")
        main_layout.addWidget(self.main_view, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Thumbnail views (320x240 each)
        thumbnails_layout = QHBoxLayout()
        thumbnails_layout.setSpacing(5)
        
        self.thumbnails = []
        labels = ["Left", "Back", "Right"]
        for label in labels:
            thumb = VideoLabel(320, 240, label)
            self.thumbnails.append(thumb)
            thumbnails_layout.addWidget(thumb)
        
        main_layout.addLayout(thumbnails_layout)
        
        # Set window background
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
        """)
    
    def start_streams(self):
        """Start all video streams with staggered startup to avoid resource contention"""
        # Main camera (video0) - 640x480
        main_thread = VideoStreamThread(self.devices[0], 640, 480, max_fps=15)
        main_thread.frame_ready.connect(self.update_main_view)
        main_thread.start()
        self.video_threads.append(main_thread)
        time.sleep(0.2)  # 延迟启动，避免资源竞争
        
        # Thumbnail cameras (video1, video2, video3) - 320x240
        # 为不同的摄像头设置不同的参数，特别是中间的 Back 摄像头
        camera_configs = [
            {'device': 1, 'fps': 15, 'format': 'mjpeg'},  # Left
            {'device': 2, 'fps': 10, 'format': 'mjpeg'},  # Back - 降低帧率减少资源竞争
            {'device': 3, 'fps': 15, 'format': 'mjpeg'},  # Right
        ]
        
        for i, config in enumerate(camera_configs):
            # 为 Back 摄像头（中间那个）使用更保守的设置
            if i == 1:  # Back camera
                thread = VideoStreamThread(
                    self.devices[config['device']], 
                    320, 240, 
                    max_fps=config['fps'],
                    input_format=config['format'],
                    retry_count=5  # 增加重试次数
                )
            else:
                thread = VideoStreamThread(
                    self.devices[config['device']], 
                    320, 240, 
                    max_fps=config['fps'],
                    input_format=config['format']
                )
            
            thread.frame_ready.connect(self.thumbnails[i].set_frame)
            thread.start()
            self.video_threads.append(thread)
            time.sleep(0.2)  # 每个摄像头延迟启动，避免同时竞争资源
    
    def update_main_view(self, frame):
        """Update the main camera view"""
        self.main_view.set_frame(frame)
    
    def closeEvent(self, event):
        """Clean up when closing the application"""
        for thread in self.video_threads:
            thread.stop()
            thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CameraMonitorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

