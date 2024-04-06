import json
from log import log
import comunication
from pet import windowsApi
import keyboard
import pyaudio
import os
import sys
import random
from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import threading
from pet import browser
logger = log.get_log(__name__)

class DesktopPet(QWidget):
    # region 初始化窗口
    def __init__(self, host, port, chunk=1024,
                 for_mat=pyaudio.paInt16,
                 channels=1, rate=44100, parent=None, **kwargs):
        try:
            self.timer = None
            self.is_follow_mouse = None
            self.win = windowsApi.WindowsAPI()
            self.host = host
            self.port = port
            self.CHUNK = chunk
            self.FORMAT = for_mat
            self.CHANNELS = channels
            self.RATE = rate
            self.audio = None
            self.text = ''
            self.random_index = None
            self.app = QApplication(sys.argv)
            super(DesktopPet, self).__init__(parent)
            # 窗体初始化
            self.init()
            self.setShow = '隐藏'
            self.walkOrStop = '原地不动'
            # 托盘化初始
            self.initPall()
            # 宠物静态gif图加载
            self.initPetImage()
            t_audio = threading.Thread(target=self.audioToaudio)
            t_audio.setDaemon(True)
            t_audio.start()
            # 宠物正常待机，实现随机切换动作
            self.petNormalAction()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 窗体初始化
    def init(self):
        try:
            # 初始化
            # 设置窗口属性:窗口无标题栏且固定在最前面
            # FrameWindowHint:无边框窗口
            # WindowStaysOnTopHint: 窗口总显示在最上面
            # SubWindow: 新窗口部件是一个子窗口，而无论窗口部件是否有父窗口部件
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            # setAutoFillBackground(True)表示的是自动填充背景,False为透明背景
            self.setAutoFillBackground(False)
            # 窗口透明，窗体空间不透明
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            # 重绘组件、刷新
            self.repaint()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 托盘化设置初始化
    def initPall(self):
        try:
            # 导入准备在托盘化显示上使用的图标
            icons = os.path.join('./pet/icon/icon.png')
            # 设置右键显示最小化的菜单项
            # 菜单项退出，点击后调用quit函数
            quit_action = QAction('退出', self, triggered=self.quit)
            # 设置这个点击选项的图片
            quit_action.setIcon(QIcon(icons))
            # 菜单项显示，点击后调用showing函数
            self.showing = QAction(self.setShow, self, triggered=self.showwin)
            # 菜单项自由走动，点击后调用walk函数
            self.walking = QAction(self.walkOrStop, self, triggered=self.walk)
            # 菜单项输入，点击后调用keyboard_input函数
            keyboard_input = QAction('键盘输入', self, triggered=self.keyboard_input)
            # 新建一个菜单项控件
            self.tray_icon_menu = QMenu(self)
            # 在菜单栏添加一个无子菜单的菜单项‘显示’
            self.tray_icon_menu.addAction(self.showing)
            # 在菜单栏添加一个无子菜单的菜单项‘自由走动’
            self.tray_icon_menu.addAction(self.walking)
            # 在菜单栏添加一个无子菜单的菜单项‘输入’
            self.tray_icon_menu.addAction(keyboard_input)
            # 在菜单栏添加一个无子菜单的菜单项‘退出’
            self.tray_icon_menu.addAction(quit_action)
            # QSystemTrayIcon类为应用程序在系统托盘中提供一个图标
            self.tray_icon = QSystemTrayIcon(self)
            # 设置托盘化图标
            self.tray_icon.setIcon(QIcon(icons))
            # 设置托盘化菜单项
            self.tray_icon.setContextMenu(self.tray_icon_menu)
            # 展示
            self.tray_icon.show()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物静态gif图加载初始化
    def initPetImage(self):
        try:
            # 对话框定义
            self.talkLabel = QLabel(self)
            # 对话框样式设计
            self.talkLabel.setStyleSheet("font:15pt '楷体';border-width: 1px;color:blue;")
            # 定义显示图片部分
            self.image = QLabel(self)
            # QMovie是一个可以存放动态视频的类，一般是配合QLabel使用的,可以用来存放GIF动态图
            self.movie = QMovie("./pet/normal/eye.gif")
            # 设置标签大小
            self.movie.setScaledSize(QSize(200, 200))
            # 将Qmovie在定义的image中显示
            self.image.setMovie(self.movie)
            self.movie.start()
            self.resize(1024, 1024)
            # 调用自定义的randomPosition，会使得宠物出现位置随机
            self.randomPosition()
            # 将QLabel向上移动50个像素,向左移动70个像素
            self.image.move(self.image.x() + 70, self.image.y() + 50)
            # 展示
            self.show()
            self.pet = [[], []]
            # 将宠物移动状态的动图放入pet中
            for i in os.listdir("./pet/direction"):
                self.pet[0].append("./pet/direction/" + i)
            # 将宠物正常待机状态的对话放入pet2中
            for i in os.listdir("./pet/normal"):
                self.pet[1].append("./pet/normal/" + i)
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物动作播放
    def petNormalAction(self):
        try:
            # 每隔一段时间做个动作
            # 定时器设置
            self.timer = QTimer()
            # 时间到了自动执行
            self.timer.timeout.connect(self.randomAct)
            # 动作时间切换设置
            if self.random_index == 0:
                self.timer.start(40)
            else:
                self.timer.start(3000)
            # 宠物状态设置为正常
            self.condition = 0
            # 每隔一段时间切换对话
            self.talkTimer = QTimer()
            self.talkTimer.timeout.connect(self.talk)
            self.talkTimer.start(3000)
            # 对话状态设置为常态
            self.talk_condition = 0
            # 宠物对话框
            self.talk()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 随机动作切换
    def randomAct(self):
        try:
            # condition记录宠物状态，宠物状态为0时，代表正常待机
            if not self.condition:
                if self.walkOrStop == '原地不动':
                    self.random_index = random.randint(0, len(self.pet) - 1)
                    now_name = random.choice(self.pet[self.random_index])
                    # 随机选择装载在pet1里面的gif图进行展示，实现随机切换
                    self.movie = QMovie(now_name)
                    if self.random_index == 0:
                        # 移动
                        szx = random.randint(1, 3)
                        self.move_gif(now_name, szx)
                    # 宠物大小
                    self.movie.setScaledSize(QSize(200, 200))
                    # 将动画添加到label中
                    self.image.setMovie(self.movie)
                    # 开始播放动画
                    self.movie.start()
                # condition不为0，转为切换特有的动作，实现宠物的点击反馈
                # 这里可以通过else-if语句往下拓展做更多的交互功能
                else:
                    self.random_index = 1
                    now_name = random.choice(self.pet[self.random_index])
                    # 随机选择装载在pet1里面的gif图进行展示，实现随机切换
                    self.movie = QMovie(now_name)
                    # 宠物大小
                    self.movie.setScaledSize(QSize(200, 200))
                    # 将动画添加到label中
                    self.image.setMovie(self.movie)
                    # 开始播放动画
                    self.movie.start()
            else:
                # 读取特殊状态图片路径
                self.movie = QMovie("./pet/click/click.gif")
                # 宠物大小
                self.movie.setScaledSize(QSize(200, 200))
                # 将动画添加到label中
                self.image.setMovie(self.movie)
                # 开始播放动画
                self.movie.start()
                # 宠物状态设置为正常待机
                self.condition = 0
                self.talk_condition = 0
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物对话框行为处理
    def talk(self):
        try:
            if not self.talk_condition:
                self.talkLabel.setText(self.text)
                # 设置样式
                self.talkLabel.setStyleSheet(
                    "font: bold;"
                    "font:15pt '楷体';"
                    "color:green;"
                    "background-color: black"
                    "url(:/)"
                )
                # 根据内容自适应大小
                self.talkLabel.adjustSize()
            else:
                # talk_condition为1显示为别点我，这里同样可以通过if-else-if来拓展对应的行为
                self.talkLabel.setText("别点我")
                self.talkLabel.setStyleSheet(
                    "font: bold;"
                    "font:25pt '楷体';"
                    "color:green;"
                    "background-color: white"
                    "url(:/)"
                )
                self.talkLabel.adjustSize()
                # 设置为正常状态
                self.talk_condition = 0
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物移动窗口
    def move_gif(self, gif_name, szx):
        try:
            if 'left' in gif_name:
                if szx == 1:
                    self.xx = self.yy = -1
                elif szx == 2:
                    self.xx = -1
                    self.yy = 0
                else:
                    self.xx = -1
                    self.yy = 1
            elif 'right' in gif_name:
                if szx == 1:
                    self.xx = 1
                    self.yy = -1
                elif szx == 2:
                    self.xx = 1
                    self.yy = 0
                else:
                    self.xx = self.yy = 1
            self.animate_move()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物移动动画切换选择
    def moveWidget(self):
        try:
            # 结束条件
            if self.step > self.total_steps:
                self.petNormalAction()
            # 计步器
            self.step += 1
            new_x = self.x() + self.xx
            new_y = self.y() + self.yy
            # 获取屏幕尺寸
            screen = self.app.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # 判断并重置
            if new_x <= 0:
                now_name = './pet/direction/right.gif'
                self.movie = QMovie(now_name)
                if 0 < new_y < screen_height - self.height():
                    szx = random.randint(1, 3)
                elif new_y <= 0:
                    szx = 3
                else:
                    szx = 1
                self.step = 0
                self.move_gif(now_name, szx)
            elif new_x >= screen_width - self.width():
                now_name = './pet/direction/left.gif'
                self.movie = QMovie(now_name)
                if 0 < new_y < screen_height - self.height():
                    szx = random.randint(1, 3)
                elif new_y <= 0:
                    szx = 3
                else:
                    szx = 1
                self.step = 0
                self.move_gif(now_name, szx)
            self.move(new_x, new_y)
            # 宠物大小
            self.movie.setScaledSize(QSize(200, 200))
            # 将动画添加到label中
            self.image.setMovie(self.movie)
            # 开始播放动画
            self.movie.start()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 播放定时器设置
    def animate_move(self):
        try:
            # 计时器
            self.timer = QTimer()
            self.timer.timeout.connect(self.moveWidget)
            # 设置定时器间隔为40毫秒
            self.timer.setInterval(40)
            self.step = 0
            # 总步数
            self.total_steps = 150
            self.timer.start()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物程序退出
    def quit(self):
        try:
            self.close()
            sys.exit()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物显示设置
    def showwin(self):
        try:
            # setWindowOpacity（）设置窗体的透明度，通过调整窗体透明度实现宠物的展示和隐藏
            if self.setShow == '隐藏':
                self.setWindowOpacity(0)
                self.setShow = '显示'
                self.showing.setText(self.setShow)
            else:
                self.setWindowOpacity(1)
                self.setShow = '隐藏'
                self.showing.setText(self.setShow)
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物走动设置
    def walk(self):
        try:
            # 将宠物自由走动状态的动图放入pet1中
            if self.walkOrStop == '自由走动':
                self.walkOrStop = '原地不动'
                self.walking.setText(self.walkOrStop)
                self.timer.stop()
                self.petNormalAction()
            else:
                self.walkOrStop = '自由走动'
                self.walking.setText(self.walkOrStop)
                self.timer.stop()
                self.petNormalAction()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物初始位置随机设置
    def randomPosition(self):
        try:
            screen_geo = QDesktopWidget().screenGeometry()
            pet_geo = self.geometry()
            width = (screen_geo.width() - pet_geo.width()) * random.random()
            height = (screen_geo.height() - pet_geo.height()) * random.random()
            self.move(width, height)
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物拖动实现
    # 鼠标左键按下时, 宠物将和鼠标位置绑定
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                self.is_follow_mouse = True
                # 更改宠物状态为点击
                self.condition = 1
                # 更改宠物对话状态
                self.talk_condition = 1
                # 即可调用对话状态改变
                self.talk()
                # 即刻加载宠物点击动画
                self.timer.stop()
                self.randomAct()
            # globalPos() 事件触发点相对于桌面的位置
            # pos() 程序相对于桌面左上角的位置，实际是窗口的左上角坐标
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            # 拖动时鼠标图形的设置
            self.setCursor(QCursor(Qt.OpenHandCursor))
        except Exception as e:
            logger.error(e)

    # 鼠标移动时调用，实现宠物随鼠标移动
    def mouseMoveEvent(self, event):
        try:
            # 如果鼠标左键按下，且处于绑定状态
            if Qt.LeftButton and self.is_follow_mouse:
                # 宠物随鼠标进行移动
                self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()
        except Exception as e:
            logger.error(e)

    # 鼠标释放调用，取消绑定
    def mouseReleaseEvent(self, event):
        try:
            self.is_follow_mouse = False
            self.talkLabel.setText("")
            self.condition = 0
            self.timer.stop()
            self.randomAct()
            self.petNormalAction()
            # 鼠标图形设置为箭头
            self.setCursor(QCursor(Qt.ArrowCursor))
        except Exception as e:
            logger.error(e)

    # 鼠标移进时调用
    def enterEvent(self, event):
        try:
            # 设置鼠标形状 Qt.ClosedHandCursor   非指向手
            self.setCursor(Qt.ClosedHandCursor)
        except Exception as e:
            logger.error(e)

    # endregion

    # region 宠物右键菜单
    def contextMenuEvent(self, event):
        try:
            # 定义菜单
            menu = QMenu(self)
            # 定义菜单项
            hide = menu.addAction(self.setShow)
            # 菜单项自由走动，点击后调用walk函数
            walk = menu.addAction(self.walkOrStop)
            # 菜单项输入，点击后调用keyboard_input函数
            keyboard_input = menu.addAction("键盘输入")
            quitAction = menu.addAction("退出")
            # 使用exec_()方法显示菜单。从鼠标右键事件对象中获得当前坐标。mapToGlobal()方法把当前组件的相对坐标转换为窗口（window）的绝对坐标。
            action = menu.exec_(self.mapToGlobal(event.pos()))
            # 点击事件为退出
            if action == quitAction:
                self.close()
                sys.exit()
            # 点击事件为隐藏
            if action == hide:
                # 通过设置透明度方式隐藏宠物
                self.showwin()
            # 点击事件为自由走动
            if action == walk:
                self.walk()
            # 点击事件为键盘输入
            if action == keyboard_input:
                self.keyboard_input()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 辅助函数
    # 切分字符串换行
    def splice_chars(self, s):
        result = ""
        for i in range(0, len(s), 10):
            chunk = s[i:i + 10]
            result += chunk + "\n"
        # 移除最后一个多余的换行符
        if result and result[-1] == "\n":
            result = result[:-1]
        return result

    # 获取关键词中间的字符串
    def get_string_between(self, s, start_substring, end_substring):
        # 查找起始子字符串的位置
        start_index = s.find(start_substring) + len(start_substring)
        # 如果起始子字符串不存在，返回None
        if start_index == -1:
            return None
            # 查找结束子字符串的位置
        end_index = s.find(end_substring, start_index)
        # 如果结束子字符串不存在或者它在起始子字符串之前，返回None
        if end_index == -1 or end_index <= start_index:
            return None
            # 返回两个子字符串之间的字符串
        return s[start_index:end_index]

    # 获取关键词后面的字符串
    def get_string_after(self, s, target):
        # 查找目标字符串的位置
        index = s.find(target)
        # 如果找到了目标字符串
        if index != -1:
            # 获取目标字符串后面的所有字符
            return s[index + len(target):]
        else:
            # 如果没有找到目标字符串，返回空字符串
            return ""

    # 获取关键词前面的字符串
    def get_string_before(self, s, target):
        index = s.find(target)
        if index != -1:
            return s[:index]
        else:
            return None

    def get_file_path(self, app, path):
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for program in data['programs']:
            if program['program_name'].lower() == app.lower():
                return program['exe_file']
        return ""

    # endregion

    # region 键盘交互
    def keyboard_input(self):
        try:
            input_dialog = QtWidgets.QInputDialog(self)
            input_dialog.setInputMode(QInputDialog.TextInput)
            input_dialog.setWindowTitle('键盘交互')
            input_dialog.setLabelText('请输入')
            # input_dialog.textValueChanged.connect('输入框 发生变化时 响应')
            # 设置 输入对话框大小
            input_dialog.setFixedSize(500, 100)
            input_dialog.show()
            screen = self.app.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            # 设置位置在中间
            input_dialog.move((screen_width / 2) - 250, (screen_height / 2) - 50)
            if input_dialog.exec_() == input_dialog.Accepted:
                # 点击ok 后 获取输入对话框内容
                textInput = input_dialog.textValue()
                if '重启电脑' in textInput:
                    self.win.restart_computer()
                elif '关闭电脑' in textInput:
                    self.win.close_computer()
                elif '锁定电脑' in textInput:
                    self.win.lock_computer()
                elif '删除' in textInput and '文件' in textInput:
                    res = self.get_string_between(textInput, '删除', '文件')
                    t = threading.Thread(target=self.win.delete_file, args=(res,))
                    t.start()
                elif '复制' in textInput and '文件到' in textInput:
                    start_copy = self.get_string_between(textInput, '复制', '文件到')
                    target = self.get_string_after(textInput, '文件到')
                    t = threading.Thread(target=self.win.copy_file, args=(start_copy, target,))
                    t.start()
                elif '现在时间' in textInput:
                    te = '当前时间：' + self.win.get_local_time()
                    t = threading.Thread(target=self.textTotextToaudio, args=(te, 1,))
                    t.start()
                elif '杀死进程号' in textInput:
                    pid = self.get_string_after(textInput, '杀死进程号')
                    self.win.kill_process_by_pid(pid)
                elif '杀死进程名' in textInput:
                    name = self.get_string_after(textInput, '杀死进程名')
                    self.win.kill_process_by_name(name)
                elif '音量放大' in textInput:
                    self.win.get_default_audio_volume('音量放大')
                elif '音量减小' in textInput:
                    self.win.get_default_audio_volume('音量减小')
                elif '静音' in textInput:
                    self.win.get_default_audio_volume('静音')
                elif '音量最大' in textInput:
                    self.win.get_default_audio_volume('音量最大')
                elif '打开视频' in textInput:
                    file = self.get_string_after(textInput, '打开视频')
                    t = threading.Thread(target=self.win.open_video, args=(file,))
                    t.start()
                elif '打开' in textInput:
                    res = self.get_string_after(textInput, '打开')
                    path = self.get_file_path(res, 'paths.json')
                    if path == "":
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('主人，列表中没有这个应用，我无法打开它。', 1,))
                        t.start()
                    else:
                        self.win.open_software(path)
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('已经为您打开' + res, 1,))
                        t.start()
                elif '点' in textInput and '提醒我' in textInput:
                    if '分' in textInput:
                        txt = self.get_string_before(textInput, '分') + '分'
                    else:
                        txt = self.get_string_before(textInput, '点') + '点'
                    tark = self.get_string_after(textInput, '提醒我')
                    if txt and tark:
                        t = threading.Thread(target=self.notebooktime, args=(txt, tark,))
                        t.start()
                    else:
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('主人，我没有听清楚，能再说一遍吗？', 1,))
                        t.start()
                elif '搜索' in textInput:
                    txt = self.get_string_after(textInput, '搜索')
                    url = "https://www.baidu.com/s?wd=" + txt
                    brow = browser.MainWindow(url)
                    brow.show()
                    # t = threading.Thread(target=self.win.baidu_search, args=(txt,))
                    # t.start()
                elif '回来' == textInput:
                    screen = QDesktopWidget().screenGeometry()
                    # 计算屏幕中心坐标
                    center_x = screen.width() / 2
                    center_y = screen.height() / 2
                    self.move(center_x, center_y)
                else:
                    tt = threading.Thread(target=self.textTotextToaudio, args=(textInput,))
                    tt.start()

        except Exception as e:
            logger.error(e)

    # endregion

    # region 语音交互
    def audioToaudio(self):
        try:
            while True:
                logger.info("Press 'alt' + 'q' to start recording...")
                while True:
                    if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                        logger.info("Recording...")
                        self.audio = comunication.Com(self.host, self.port, self.CHUNK, self.FORMAT, self.CHANNELS,
                                                      self.RATE)
                        break
                self.audio.run_audio()
                datatype, textInput = self.audio.receive_data()
                if '重启电脑' in textInput:
                    self.win.restart_computer()
                elif '关闭电脑' in textInput:
                    self.win.close_computer()
                elif '锁定电脑' in textInput:
                    self.win.lock_computer()
                elif '现在时间' in textInput:
                    te = '当前时间：' + self.win.get_local_time()
                    t = threading.Thread(target=self.textTotextToaudio, args=(te,1,))
                    t.start()
                elif '杀死进程号' in textInput:
                    pid = self.get_string_after(textInput, '杀死进程号')
                    self.win.kill_process_by_pid(pid)
                elif '杀死进程名' in textInput:
                    name = self.get_string_after(textInput, '杀死进程名')
                    self.win.kill_process_by_name(name)
                elif '音量放大' in textInput:
                    self.win.get_default_audio_volume('音量放大')
                elif '音量减小' in textInput:
                    self.win.get_default_audio_volume('音量减小')
                elif '关闭声音' in textInput:
                    self.win.get_default_audio_volume('静音')
                elif '音量最大' in textInput:
                    self.win.get_default_audio_volume('音量最大')
                elif '打开' in textInput:
                    res = self.get_string_after(textInput, '打开')
                    path = self.get_file_path(res, 'paths.json')
                    if path == "":
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('主人，列表中没有这个应用，我无法打开它。', 1,))
                        t.start()
                    else:
                        self.win.open_software(path)
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('已经为您打开' + res, 1,))
                        t.start()
                elif '点' in textInput and '提醒我' in textInput:
                    if '分' in textInput:
                        txt = self.get_string_before(textInput, '分') + '分'
                    else:
                        txt = self.get_string_before(textInput, '点') + '点'
                    tark = self.get_string_after(textInput, '提醒我')
                    if txt and tark:
                        t = threading.Thread(target=self.notebooktime, args=(txt, tark,))
                        t.start()
                    else:
                        t = threading.Thread(target=self.textTotextToaudio,
                                             args=('主人，我没有听清楚，能再说一遍吗？', 1,))
                        t.start()
                elif '回来' == textInput:
                    screen = QDesktopWidget().screenGeometry()
                    # 计算屏幕中心坐标
                    center_x = screen.width() / 2
                    center_y = screen.height() / 2
                    self.move(center_x, center_y)
                else:
                    self.audio.send_data(b'ok')
                    data_type, data = self.audio.receive_data()
                    self.audio.ser_back = data
                    # data_type, data = self.audio.receive_data()
                    # audio_guka = data
                    if len(self.audio.ser_back) < 30:
                        self.text = self.audio.ser_back
                        self.talk()
                    else:
                        win_txt = threading.Thread(target=self.win.dialog_txt, args=(self.audio.ser_back,))
                        win_txt.start()
                    t = threading.Thread(target=self.soundAudio, args=())
                    t.start()
        except Exception as e:
            logger.error(e)

    # endregion

    # region 事件提醒
    def notebooktime(self, target_time_str, task):
        self.textTotextToaudio('好的，我会在'+target_time_str+'提醒您。', 1)
        text = self.win.wait_until_time(target_time_str, task)
        self.textTotextToaudio(text, 1)
    # endregion

    # region 播放音频
    def soundAudio(self):
        try:
            while True:
                # data_type, data = self.audio.receive_data()
                data = self.audio.s.recv(1024)
                if not data:
                    break  # 没有更多数据，退出循环
                # 将接收到的数据写入流进行播放（注意：这里假设音频数据已经是PCM格式）
                self.audio.write_audio(data)
            self.text = ''
        except Exception as e:
            logger.error(e)
    # endregion

    # region 键盘交互聊天
    def textTotextToaudio(self, text, flag=0):
        self.audio = comunication.Com(self.host, self.port, self.CHUNK, self.FORMAT, self.CHANNELS, self.RATE)
        if flag:
            self.text = self.audio.run_str(text, b'dq')
        else:
            txt = self.audio.run_str(text)
            if len(txt) <= 30:
                self.text = self.audio.ser_back
                self.talk()
            else:
                win_txt = threading.Thread(target=self.win.dialog_txt, args=(self.audio.ser_back,))
                win_txt.start()
        t = threading.Thread(target=self.soundAudio, args=())
        t.start()
    # endregion
