import json
from tool import windowsApi
import log
import keyboard
import os
import sys
import random
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import threading
import comunication
from liaotian import entrance
from User import conversation
logger = log.get_log(__name__)


# 切分字符串换行
def splice_chars(s):
    result = ""
    for i in range(0, len(s), 10):
        chunk = s[i:i + 10]
        result += chunk + "\n"
    # 移除最后一个多余的换行符
    if result and result[-1] == "\n":
        result = result[:-1]
    return result


# 获取关键词中间的字符串
def get_string_between(s, start_substring, end_substring):
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
def get_string_after(s, target):
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
def get_string_before(s, target):
    index = s.find(target)
    if index != -1:
        return s[:index]
    else:
        return None


def get_file_path(app, path):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for program in data['programs']:
        if program['program_name'].lower() == app.lower():
            return program['exe_file']
    return ""


class DesktopPet(QWidget):
    def __init__(self, host, port, user, parent=None, **kwargs):
        try:
            self.app = QApplication(sys.argv)
            self.user = user
            self.win = windowsApi.WindowsAPI()
            self.step = None
            self.timer = None
            self.is_follow_mouse = None
            self.host = host
            self.port = port
            self.text = ''
            self.random_index = None
            super(DesktopPet, self).__init__(parent)
            self.talk_entrance = entrance.MainWindow(self.host, self.port, self.user)
            self.start_pet()
        except Exception as e:
            logger.error(e)

    def start_pet(self):
        # 窗体初始化
        self.init()
        self.setShow = '隐藏'
        self.walkOrStop = '原地不动'
        # 托盘化初始
        self.initPall()
        # 宠物静态gif图加载
        self.initPetImage()
        audio_to_text = threading.Thread(target=self.audioTotext)
        audio_to_text.setDaemon(True)
        audio_to_text.start()
        # 宠物正常待机，实现随机切换动作
        self.petNormalAction()

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

    def initPall(self):
        try:
            # 导入准备在托盘化显示上使用的图标
            icons = os.path.join('./resource/icon/icon.png')
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
            self.look = QAction('聊天界面', self, triggered=self.talk_look)
            self.adding = QAction('添加应用', self, triggered=self.add_app)
            # 新建一个菜单项控件
            self.tray_icon_menu = QMenu(self)
            # 在菜单栏添加一个无子菜单的菜单项‘显示’
            self.tray_icon_menu.addAction(self.showing)
            # 在菜单栏添加一个无子菜单的菜单项‘自由走动’
            self.tray_icon_menu.addAction(self.walking)
            # 在菜单栏添加一个无子菜单的菜单项‘聊天界面’
            self.tray_icon_menu.addAction(self.look)
            self.tray_icon_menu.addAction(self.adding)
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

    def initPetImage(self):
        try:
            # 对话框定义
            self.talkLabel = QLabel(self)
            # 对话框样式设计
            self.talkLabel.setStyleSheet("font:15pt '楷体';border-width: 1px;color:blue;")
            # 定义显示图片部分
            self.image = QLabel(self)
            # QMovie是一个可以存放动态视频的类，一般是配合QLabel使用的,可以用来存放GIF动态图
            self.movie = QMovie("./resource/normal/eye.gif")
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
            for i in os.listdir("./resource/direction"):
                self.pet[0].append("./resource/direction/" + i)
            # 将宠物正常待机状态的对话放入pet2中
            for i in os.listdir("./resource/normal"):
                self.pet[1].append("./resource/normal/" + i)
        except Exception as e:
            logger(e)

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
            logger(e)

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
                self.movie = QMovie("./resource/click/click.gif")
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
            logger(e)

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
            logger(e)

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
            logger(e)

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
                now_name = './resource/direction/right.gif'
                self.select_movie(new_y, now_name, screen_height)
            elif new_x >= screen_width - self.width():
                now_name = './resource/direction/left.gif'
                self.select_movie(new_y, now_name, screen_height)
            self.move(new_x, new_y)
            # 宠物大小
            self.movie.setScaledSize(QSize(200, 200))
            # 将动画添加到label中
            self.image.setMovie(self.movie)
            # 开始播放动画
            self.movie.start()
        except Exception as e:
            logger(e)

    def select_movie(self, new_y, now_name, screen_height):
        try:
            self.movie = QMovie(now_name)
            if 0 < new_y < screen_height - self.height():
                szx = random.randint(1, 3)
            elif new_y <= 0:
                szx = 3
            else:
                szx = 1
            self.step = 0
            self.move_gif(now_name, szx)
        except Exception as e:
            logger.error(e)

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

    def quit(self):
        try:
            self.talk_entrance.close()
            self.close()
            sys.exit(0)
        except Exception as e:
            logger(e)

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter("Executable Files (*.exe)")
        file_path, _ = file_dialog.getOpenFileName(None, "选择可执行文件", "", "Executable Files (*.exe)")
        if file_path:
            self.line_edit_path.setText(file_path)

    def handle_ok(self, dialog, line_edit_name):
        file_path = self.line_edit_path.text()
        file_name = line_edit_name.text()
        if not file_path or not file_name:
            QMessageBox.warning(dialog, '警告', '文件路径和名称不能为空！')
            return
            # 在这里处理文件路径和名称，例如打印它们或进行其他操作
        program = {'program_name': file_name, 'exe_file': file_path}
        with open('./resource/paths.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['programs'].append(program)
        with open('./resource/paths.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        dialog.accept()

    def add_app(self):
        # 创建弹窗
        dialog = QDialog()
        dialog.setWindowTitle('文件选择与命名')
        # 创建布局
        layout = QVBoxLayout(dialog)
        # 文件路径输入框
        self.line_edit_path = QLineEdit(dialog)
        layout.addWidget(self.line_edit_path)
        # 文件名输入框
        line_edit_name = QLineEdit(dialog)
        layout.addWidget(line_edit_name)
        # 选择文件按钮
        button_select = QPushButton('选择文件', dialog)
        button_select.clicked.connect(self.select_file)
        layout.addWidget(button_select)
        # 确定按钮
        button_ok = QPushButton('确定', dialog)
        button_ok.clicked.connect(lambda: self.handle_ok(dialog, line_edit_name))
        layout.addWidget(button_ok)
        # 显示弹窗
        dialog.exec_()

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
            logger(e)

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

    def randomPosition(self):
        try:
            screen_geo = QDesktopWidget().screenGeometry()
            pet_geo = self.geometry()
            width = (screen_geo.width() - pet_geo.width()) * random.random()
            height = (screen_geo.height() - pet_geo.height()) * random.random()
            self.move(width, height)
        except Exception as e:
            logger.error(e)

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
            self.setCursor(Qt.ClosedHandCursor)
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
            # 鼠标图形设置为箭头key
            self.setCursor(QCursor(Qt.ArrowCursor))
        except Exception as e:
            logger.error(e)

    # 鼠标移进时调用
    def enterEvent(self, event):
        try:
            # 设置鼠标形状 Qt.ClosedHandCursor   非指向手
            self.setCursor(QCursor(Qt.OpenHandCursor))
        except Exception as e:
            logger.error(e)

    def contextMenuEvent(self, event):
        try:
            # 定义菜单
            menu = QMenu(self)
            # 定义菜单项
            hide = menu.addAction(self.setShow)
            # 菜单项自由走动，点击后调用walk函数
            walk = menu.addAction(self.walkOrStop)
            talkLook = menu.addAction("聊天界面")
            addapp = menu.addAction("添加应用")
            quitAction = menu.addAction("退出")
            # 使用exec_()方法显示菜单。从鼠标右键事件对象中获得当前坐标。mapToGlobal()
            # 方法把当前组件的相对坐标转换为窗口（window）的绝对坐标。
            action = menu.exec_(self.mapToGlobal(event.pos()))
            # 点击事件为退出
            if action == quitAction:
                self.close()
                sys.exit()
            # 点击事件为隐藏
            elif action == hide:
                # 通过设置透明度方式隐藏宠物
                self.showwin()
            # 点击事件为自由走动
            elif action == walk:
                self.walk()
            elif action == addapp:
                self.add_app()
            elif action == talkLook:
                self.talk_look()
        except Exception as e:
            logger.error(e)

    def talk_look(self):
        try:
            self.talk_entrance.show()
        except Exception as e:
            logger.error(e)


    def audioTotext(self):
        while True:
            logger.info("Press 'alt' + 'q' to start recording...")
            while True:
                if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                    self.talk_entrance.audio = comunication.Com(self.host, self.port)
                    logger.info("Recording...")
                    break
            input_text = self.talk_entrance.audio.read_audio()
            logger.info(input_text)
            self.talk_entrance.audio.close_down()
            if '切换功能' in input_text:
                self.talk_entrance.mode = '🛠️ Tool'
            elif '切换聊天' in input_text:
                self.talk_entrance.mode = '💬 Chat'
            elif '切换代码' in input_text:
                self.talk_entrance.mode = '🧑‍💻 Code Interpreter'
            elif '回来' == input_text:
                screen = QDesktopWidget().screenGeometry()
                # 计算屏幕中心坐标
                center_x = screen.width() / 2
                center_y = screen.height() / 2
                self.move(center_x, center_y)
            elif '音量放大' in input_text:
                self.win.get_default_audio_volume('音量放大')
            elif '音量减小' in input_text:
                self.win.get_default_audio_volume('音量减小')
            elif '静音' in input_text:
                self.win.get_default_audio_volume('静音')
            elif '音量最大' in input_text:
                self.win.get_default_audio_volume('音量最大')
            elif '立即关机' in input_text:
                self.win.close_computer()
            elif '取消关机' in input_text:
                self.win.unclose_computer()
            else:
                # self.talk_entrance.show()
                self.talk_entrance.plainTextEdit.setPlainText(input_text)
                self.talk_entrance.pushButton.click()