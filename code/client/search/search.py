import glob
import json
import os
from log import log
logger = log.get_log(__name__)
import win32api
from PyQt5.QtCore import QBasicTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QProgressBar


class ProgressDialog(QDialog):
    def __init__(self, maximum, parent=None):
        super().__init__(parent)
        try:
            self.setWindowTitle("guka")
            self.setWindowIcon(QIcon('./pet/icon/icon.png'))
            self.setModal(True)
            self.progress = QProgressBar(self)
            self.progress.setMinimum(0)
            self.progress.setMaximum(maximum)
            self.layout = QVBoxLayout()
            self.layout.addWidget(self.progress)
            self.setLayout(self.layout)
            self.timer = QBasicTimer()
            self.step = 0
        except Exception as e:
            logger.error(e)

    def start(self):
        try:
            self.show()
            self.timer.start(100, self)  # 每100毫秒更新一次进度条
        except Exception as e:
            logger.error(e)

    def timerEvent(self, event):
        try:
            if self.step >= self.progress.maximum():
                self.timer.stop()
                self.accept()  # 关闭对话框
            else:
                self.step += 1
                self.progress.setValue(self.step)
        except Exception as e:
            logger.error(e)


def find_file_path(filename, drives, progress_callback):
    try:
        for i, drive in enumerate(drives):
            for path in glob.iglob(os.path.join(drive, '**', filename), recursive=True):
                return path
            progress_callback(i + 1)  # 更新进度条
            QApplication.processEvents()
        return None
    except Exception as e:
        logger.error(e)


def json_file_paths(input_json_path, output_json_path):
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
        total_programs = len(data['programs'])
        progress = ProgressDialog(total_programs)
        progress.start()  # 显示进度条弹窗并开始计时器

        def update_progress(current):
            progress.progress.setValue(current * len(drives))  # 因为每个程序可能在多个驱动器上搜索，所以乘以驱动器数量来估算进度
        for i, program in enumerate(data['programs']):
            exe_file = program['exe_file']
            file_path = find_file_path(exe_file, drives, update_progress)  # 传递更新进度的回调函数
            if file_path:
                program['exe_file'] = file_path
            else:
                program['exe_file'] = ''
            QApplication.processEvents()  # 处理事件队列中的事件，包括更新GUI
        data['programs'] = [program for program in data['programs'] if program['exe_file'] != '']

        progress.timer.stop()  # 确保进度条停止更新
        progress.accept()  # 关闭进度条弹窗

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"已更新的程序信息已保存为 {output_json_path}")
    except Exception as e:
        logger.error(e)
