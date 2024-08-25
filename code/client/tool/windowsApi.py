from log import log

logger = log.get_log(__name__)
import datetime
import logging
import math
import os
import time
import webbrowser
import cv2
import subprocess
import win32api
import win32con
import ctypes
import win32file
import psutil
import pyaudio
import wave
import keyboard
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ffpyplayer.player import MediaPlayer


class WindowsAPI:

    # 判断是否有管理员权限
    def is_admin(self):
        try:
            # 获取当前用户的是否为管理员
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logging.error(e)
            return False

    # 弹出确认框
    def confirm_action(self, message):
        return win32api.MessageBox(0, message, "确认", win32con.MB_YESNO | win32con.MB_ICONQUESTION)

    # 重启计算机(立即重启)
    def restart_computer(self):
        try:
            # 弹出确认框
            confirmed = self.confirm_action("确定要重启计算机吗？确认前请保证所需文件已保存！")

            # 判断是和否
            if confirmed == win32con.IDYES:
                # if is_admin():
                # 立即重启
                # win32api.ExitWindowsEx(win32con.EWX_REBOOT, 0)
                subprocess.call(["shutdown", "-r", "-t", "0"])
                # else:
                #     # 重新运行这个程序使用管理员权限
                #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            else:
                logger.info("取消重启操作")
        except Exception as e:
            logger.error(e)

    # 关闭计算机(一分钟后关机)
    def close_computer(self):
        try:
            confirmed = self.confirm_action("确定要关闭计算机吗？确认前请保证所需文件已保存！")

            if confirmed == win32con.IDYES:
                # if is_admin():
                subprocess.call(["shutdown", "/s"])
                # else:
                #     # 重新运行这个程序使用管理员权限
                #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            else:
                logger.info("取消关闭操作")
        except Exception as e:
            logger.error(e)

    def unclose_computer(self):
        subprocess.call(["shutdown.exe", "-a"])


    def close_time_computer(self, time_str):
        current_time = datetime.datetime.now()
        if '时' in time_str:
            target_time_parts = time_str.split("时")
        elif '点' in time_str:
            target_time_parts = time_str.split("点")
        elif '.' in time_str:
            target_time_parts = time_str.split(".")
        target_hour = int(target_time_parts[0])
        target_minute = int(target_time_parts[1].split("分")[0])
        target_time = datetime.datetime(current_time.year, current_time.month, current_time.day, target_hour,
                                        target_minute)

        # 如果目标时间已经过去，则设置为明天的同一时间
        if target_time < current_time:
            target_time += datetime.timedelta(days=1)

        remaining_time = (target_time - current_time).total_seconds()
        remaining_time_int = int(remaining_time)
        # 将整数转换为字符串
        remaining_time_str = str(remaining_time_int)
        subprocess.call(["shutdown.exe", "-s", "-f", "-t", remaining_time_str])
    # # 注销用户
    # def logoff_user():
    #     confirmed = confirm_action("确定要注销用户吗？确认前请保证所需文件已保存！")
    #
    #     if confirmed == win32con.IDYES:
    #         # if is_admin():shutdown -l -t 60
    #           os.system('shutdown -l -t 60')
    #         # else:
    #         #     # 重新运行这个程序使用管理员权限
    #         #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    #     else:
    #         print("取消注销操作")

    # 锁定计算机
    def lock_computer(self):
        try:
            confirmed = self.confirm_action("确定要锁定计算机吗？")

            if confirmed == win32con.IDYES:
                dll = ctypes.WinDLL('user32.dll')

                dll.LockWorkStation()
            else:
                logger.info("取消锁定操作")
        except Exception as e:
            logger.error(e)

    # 发出一次短促的蜂鸣声
    def make_beep(self):
        win32api.Beep(440, 1000)

    # 发出预定义的声音
    def message_beep(self):
        win32api.MessageBeep(1)

    # 复制文件  源文件路径src_file  目标文件路径dst_file
    def copy_file(self, src_file, dst_file):
        try:
            win32api.CopyFile(src_file, dst_file)
        except Exception as e:
            logger.error(e)

    # 删除文件
    def delete_file(self, fileName):
        try:
            win32api.DeleteFile(fileName)
        except Exception as e:
            logger.error(e)

    # 获取计算机名
    def get_computer_name(self):
        print(win32api.GetComputerName())
        return win32api.GetComputerName()

    # 返回鼠标位置
    def get_cursor_pos(self):
        x, y = win32api.GetCursorPos()
        print(x, y)
        return x, y

    # 获取当前时间
    def get_local_time(self):
        try:
            # 获取当前时间
            current_time = datetime.datetime.now()
            # 格式化当前时间
            formatted_time_without_weekday = current_time.strftime("%Y-%m-%d %H:%M:%S")  # 包括年、月、日、时、分、秒
            # 获取星期几的英文缩写（例如：Mon）
            weekday_abbr = current_time.strftime("%a")
            # 定义英文星期缩写到中文的映射
            weekday_abbr_to_chinese = {
                "Mon": "星期一",
                "Tue": "星期二",
                "Wed": "星期三",
                "Thu": "星期四",
                "Fri": "星期五",
                "Sat": "星期六",
                "Sun": "星期日"
            }
            # 获取对应的中文星期几
            chinese_weekday = weekday_abbr_to_chinese[weekday_abbr]
            # 拼接完整的格式化时间字符串，包括中文星期几
            formatted_time = f"{formatted_time_without_weekday} {chinese_weekday}"
            # 打印格式化后的当前时间
            logger.info(formatted_time)
            return formatted_time
        except Exception as e:
            logger.error(e)

    # 根据进程ID终止进程
    def kill_process_by_pid(self, pid):
        try:
            # 打开进程句柄
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
            if handle:
                # 终止进程
                win32api.TerminateProcess(handle, 0)
                # 关闭进程句柄
                win32api.CloseHandle(handle)
        except Exception as e:
            logger.error(e)

    # 根据进程名称终止进程
    def kill_process_by_name(self, name):
        try:
            # 用psutil模块来获取正在运行的进程列表
            for process in psutil.process_iter(['name', 'pid']):

                # 根据进程名称匹配要终止的进程
                if process.info['name'] == name:
                    pid = process.info['pid']

                    # 根据进程ID终止进程
                    self.kill_process_by_pid(pid)
        except Exception as e:
            logger.error(e)

    # 读取文件内容
    def read_file(self, filename):
        try:
            # 打开文件
            handle = win32file.CreateFile(filename, win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING, 0, 0)

            # 获取文件大小
            file_size = win32file.GetFileSize(handle)

            # 读取文件内容
            buffer = win32file.ReadFile(handle, file_size)

            # 关闭文件句柄
            win32file.CloseHandle(handle)

            return buffer
        except Exception as e:
            logger.error(e)

    def set_auidio_volume(self, value):
        try:
            # 使用 AudioUtilities 模块中的 GetSpeakers 方法来获取默认的音频渲染设备
            devices = AudioUtilities.GetSpeakers()
            # 使用获取到的音频渲染设备对象的 Activate 方法来激活 IAudioEndpointVolume 接口
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            # 使用 cast 函数将 interface 转换为 IAudioEndpointVolume 对象
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            # 获取音量值，0.0代表最大，-65.25代表最小
            volume.SetMasterVolumeLevelScalar(value/100.0, None)
            # 获取音量值，0.0代表最大，-65.25代表最小
            vl = volume.GetMasterVolumeLevelScalar()
            logger.info('当前音量='+vl)
        except Exception as e:
            logger.error(e)

    # 获取默认音频设备的音量对象
    def get_default_audio_volume(self, command):
        try:
            # 使用 AudioUtilities 模块中的 GetSpeakers 方法来获取默认的音频渲染设备
            devices = AudioUtilities.GetSpeakers()
            # 使用获取到的音频渲染设备对象的 Activate 方法来激活 IAudioEndpointVolume 接口
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            # 使用 cast 函数将 interface 转换为 IAudioEndpointVolume 对象
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            # 获取音量值，0.0代表最大，-65.25代表最小
            vl = volume.GetMasterVolumeLevel()
            if '放大' in command:
                volume.SetMasterVolumeLevel(vl + 3.2625, None)
            elif '减小' in command:
                volume.SetMasterVolumeLevel(vl - 3.2625, None)
            elif '静音' in command:
                volume.SetMute(1, None)
            elif '最大' in command:
                volume.SetMasterVolumeLevel(0.0, None)
            # 获取音量值，0.0代表最大，-65.25代表最小
            vl = volume.GetMasterVolumeLevel()
            logger.info('当前音量='+vl)
        except Exception as e:
            logger.error(e)

    # 获取视频时长
    def get_video_time(self, video_path):
        try:
            cap = cv2.VideoCapture(video_path)

            # 获取视频的帧率和总帧数
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

            # 计算视频的总时长
            duration_in_seconds = total_frames / fps

            print("视频时长（秒）：", duration_in_seconds)

            cap.release()

            return duration_in_seconds
        except Exception as e:
            logger.error(e)

    # 打开视频并全屏
    def open_video(self, video_path):
        # 调用系统默认的视频播放软件打开视频
        os.system(f"start {video_path}")
        # 将视频全屏显示
        pyautogui.hotkey('alt', 'enter')

    # 打开视频并全屏
    def play_video_fullscreen(self, video_path, audio_play=True):
        try:
            cap = cv2.VideoCapture(video_path)

            total_time = self.get_video_time(video_path)
            if audio_play:
                player = MediaPlayer(video_path, loop=False, stop_time=total_time)

            # 打开文件状态
            isopen = cap.isOpened()
            if not isopen:
                logger.error("Err: Video is failure. Exiting ...")
            # 视频时长总帧数
            total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            # 获取视频宽度
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            # 获取视频高度
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # 创建全屏窗口
            cv2.namedWindow('image', cv2.WINDOW_NORMAL)
            cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            # 视频帧率
            fps = cap.get(cv2.CAP_PROP_FPS)
            # 播放帧间隔毫秒数
            wait = int(1000 / fps) if fps else 1
            # 帧数计数器
            read_frame = 0

            # 循环读取视频帧
            while (isopen):
                # 读取帧图像
                ret, frame = cap.read()
                # 读取错误处理
                if not ret:

                    if read_frame < total_frame:
                        # 读取错误
                        logger.error("Err: Can't receive frame. Exiting ...")
                    else:
                        # 正常结束
                        logger.info("Info: Stream is End")
                    break

                # 帧数计数器+1
                read_frame = read_frame + 1
                dst = cv2.resize(frame, (1920 // 2, 1080 // 2), interpolation=cv2.INTER_CUBIC)  # 窗口大小
                # 计算当前播放时码
                timecode_h = int(read_frame / fps / 60 / 60)
                timecode_m = int(read_frame / fps / 60)
                timecode_s = read_frame / fps % 60
                s = math.modf(timecode_s)
                timecode_s = int(timecode_s)
                timecode_f = int(s[0] * fps)

                # 显示帧图像
                cv2.imshow('image', dst)

                # 播放间隔
                wk = cv2.waitKey(wait)

                # 按键值  & 0xFF是一个二进制AND操作 返回一个不是单字节的代码
                keycode = wk & 0xff

                # 空格键暂停
                if keycode == ord(" "):
                    cv2.waitKey(0)

                # p键退出
                if keycode == ord('p'):
                    logger.info("Info: By user Cancal ...")
                    break

            # 释放实例
            cap.release()

            # 销毁窗口
            cv2.destroyAllWindows()
        except Exception as e:
            logger.error(e)

    # 根据进程 ID 获取对应的文件路径
    def get_process_filepath(self, pid):
        try:
            process = psutil.Process(pid)
            return process.exe()
        except psutil.AccessDenied as e:
            logger.error(e)
            return ""

    # 判断文件是否为视频文件
    def is_video_file(self, filepath):
        try:
            video_extensions = ['.avi', '.mp4', '.mkv']  # 视频文件的后缀名列表，可以根据实际需要进行修改
            file_extension = filepath[filepath.rfind('.'):].lower()
            if file_extension in video_extensions:
                return True
            return False
        except Exception as e:
            logger.error(e)

    # 获取视频窗口的名称
    def get_video_window_title(self):
        try:
            video_windows = []
            for window in psutil.process_iter(['name', 'pid']):
                pid = window.info['pid']
                filepath = self.get_process_filepath(pid)
                if self.is_video_file(filepath):
                    video_windows.append(window)
            return video_windows
        except Exception as e:
            logger.error(e)

    # 软件路径获取
    def find_app_path(self, file_path, target_path):
        with open(file_path, 'r') as file:
            for line in file:
                # 移除行尾的换行符并检查是否与目标路径匹配
                if target_path in line.strip():
                    return line.strip()  # 返回找到的路径
        return None  # 如果没有找到目标路径，返回None

    # 打开软件
    def open_software(self, file_path):
        try:
            os.startfile(file_path)
        except Exception as e:
            logger.error(e)


    def open_edge(self, url):
        try:
            # 检查Python的默认编码是否为UTF-8，如果不是，则重新加载sys模块以确保使用UTF-8编码
            # if sys.getdefaultencoding() != 'utf-8':
            #     importlib.reload(sys)
            # print("open baidu search:{}".format(rst))
            # print('https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=0&rsv_idx=1&tn=baidu&wd={}'.format(rst))
            # webbrowser.open(url="https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=0&rsv_idx=1&tn=baidu&wd={}".format(rst))
            webbrowser.open(url=url)
        except Exception as e:
            logger.error(e)

    # 按下alt + q进行录音
    def recording(self):
        # 定义音频流的缓冲区大小为1024个样本
        CHUNK = 1024
        # 定义音频数据的格式为16位整数
        FORMAT = pyaudio.paInt16
        # 定义音频流的通道数为1
        CHANNELS = 1
        # 定义音频流的采样率为44100 Hz
        RATE = 44100
        # 定义保存录音文件的文件名为"recording.wav"
        WAVE_OUTPUT_FILENAME = "recording.wav"

        # 创建PyAudio对象
        p = pyaudio.PyAudio()
        # 打开音频流，设置音频流的格式、通道数、采样率等参数
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        # 创建一个空列表用于存储录制的音频数据
        frames = []

        print("Press 'alt' + 'q' to start recording...")

        # 检测用户是否按下"alt"和"q"键，如果是，则跳出循环，开始录制音频。
        while True:
            if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                # print("Recording...")
                break

        # 在用户按下"alt"和"q"键后，持续读取音频数据并将其添加到frames列表中，直到用户松开按键
        while True:
            if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                data = stream.read(CHUNK)
                frames.append(data)
            else:
                break

        print("Recording stopped.")

        # 停止音频流。
        stream.stop_stream()
        # 关闭音频流
        stream.close()
        #  终止PyAudio对象
        p.terminate()

        # 创建一个WAV文件对象，设置文件的参数
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        # 将录制的音频数据写入WAV文件
        wf.writeframes(b''.join(frames))
        # 关闭WAV文件
        wf.close()

    def is_file_closed(self, file_path):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'notepad.exe' and file_path in proc.info['cmdline']:
                    return False
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return True

    # 弹出txt文本并显示内容，关闭后自动删除
    def dialog_txt(self, string):
        # 在桌面上创建文本文件
        desktop_path = os.path.expanduser("~\\Desktop")
        file_path = os.path.join(desktop_path, "text.txt")

        # 创建并写入文件
        try:
            with open(file_path, "w") as file:
                file.write(string)
            print(f"文本文件已创建：{file_path}")
            subprocess.Popen(['start', file_path], shell=True)
        except Exception as e:
            print(f"创建文件时发生错误：{e}")
            return

        # 监控文件是否被关闭
        while not self.is_file_closed(file_path):
            time.sleep(1)  # 休眠一秒后再次检查

        # 如果文件被关闭，则删除它
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"文本文件已删除：{file_path}")
        except Exception as e:
            print(f"删除文件时发生错误：{e}")

    # 定时闹钟
    def alarm_clock(self, alarm_time):
        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            if current_time == alarm_time:
                self.message_beep()
                break
            time.sleep(1)  # 每隔一秒检查一次时间

    def calculate_remaining_time(self, target_time_str):
        current_time = datetime.datetime.now()
        if '时' in target_time_str:
            target_time_parts = target_time_str.split("时")
        elif '点' in target_time_str:
            target_time_parts = target_time_str.split("点")
        target_hour = int(target_time_parts[0])
        target_minute = int(target_time_parts[1].split("分")[0])
        target_time = datetime.datetime(current_time.year, current_time.month, current_time.day, target_hour,
                                        target_minute)

        # 如果目标时间已经过去，则设置为明天的同一时间
        if target_time < current_time:
            target_time += datetime.timedelta(days=1)

        remaining_time = (target_time - current_time).total_seconds()
        return remaining_time

    def wait_until_time(self, target_time_str, task):
        remaining_time = self.calculate_remaining_time(target_time_str)
        time.sleep(remaining_time)  # 等待剩余时间
        return f"时间到了！现在要{task}。"

