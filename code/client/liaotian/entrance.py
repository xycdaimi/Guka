import sys
import threading
import time
from tool import collectSearch
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser
from PyQt5.QtGui import QFont, QFontMetrics, QCloseEvent
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import log
from User import User
import json
import comunication
from liaotian.new_widget import Set_question
from liaotian.untitled import Ui_MainWindow
from tool import windowsApi
from User import conversation

logger = log.get_log(__name__)


def get_file_path(app, path):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for program in data['programs']:
        if program['program_name'].lower() == app.lower():
            return program['exe_file']
    return ""


class WorkerThread(QThread):
    data_received = pyqtSignal(str)  # 定义信号，携带字符串类型的数据
    his = pyqtSignal(str)

    def __init__(self, host, port, mode, text, user, parent=None):
        super().__init__(parent)
        self.audio = None
        self.user = user
        self.host = host
        self.port = port
        self.mode = mode
        self.text = text
        self.frame = b''
        self.flag = True
        self.chunk = 1024
        self.win = windowsApi.WindowsAPI()

    def run(self):
        self.audio = comunication.Com(self.host, self.port)
        self.audio.send_data(comunication.STRING, "对话")
        self.audio.send_data(comunication.JSON,
                             {'flag': "推理", 'mode': self.mode, 'retry': 0, 'top_p': 0.8,
                              'temperature': 0.95, 'prompt_text': self.text,
                              'repetition_penalty': 1.1, 'max_new_token': 256,
                              'uid': str(self.user.uid)})
        if self.mode == '💬 Chat':
            txt_buffer = ''
            while True:
                data_type, data = self.audio.receive_data()
                if data == "end":
                    break
                txt_buffer = data
                self.data_received.emit(data)
            self.his.emit(txt_buffer)
            QApplication.processEvents()
        elif self.mode == '🛠️ Tool':
            data_type, data = self.audio.receive_data()
            if '打开网址:' in data:
                data = data.split(":")[1].strip()
                bk = collectSearch.BookMark()
                bookList = bk.get_folder_data()
                bookList = collectSearch.explode_dict_array(bookList, "children")
                bookList = bookList[['name', 'url']]
                url = bookList.loc[bookList['name'] == data, 'url']
                if not url.empty:
                    value = url.iloc[0]
                    t = threading.Thread(target=self.win.open_edge,
                                         args=(value,))
                    t.start()
                    self.audio.send_data(comunication.STRING, "open")
                else:
                    self.audio.send_data(comunication.STRING, "err")
                data_type, data = self.audio.receive_data()
            elif '重启电脑' == data:
                t = threading.Thread(target=self.win.restart_computer,
                                     args=())
                t.start()
                data_type, data = self.audio.receive_data()
            elif '定时关机' == data:
                data_type, data = self.audio.receive_data()
                t = threading.Thread(target=self.win.close_time_computer,
                                     args=(data,))
                t.start()
                data_type, data = self.audio.receive_data()
            elif '锁定电脑' == data:
                data_type, data = self.audio.receive_data()
                t = threading.Thread(target=self.win.lock_computer,
                                     args=())
                t.start()
            elif '音量设置' == data:
                data_type, data = self.audio.receive_data()
                t = threading.Thread(target=self.win.set_auidio_volume,
                                     args=(float(data['volume']),))
                t.start()
                data_type, data = self.audio.receive_data()
            elif '打开:' in data:
                data = data.split(":")[1].strip()
                path = get_file_path(data, './resource/paths.json')
                if path != "":
                    self.win.open_software(path)
                self.audio.send_data(comunication.STRING, path)
                data_type, data = self.audio.receive_data()
            elif '定时提醒' == data:
                data_type, data = self.audio.receive_data()
                logger.info(data)
                t = threading.Thread(target=self.regular_reminder,
                                     args=(data,))
                t.start()
                data_type, data = self.audio.receive_data()
            self.data_received.emit(data)
            self.his.emit(data)
        get_audio = threading.Thread(target=self.audio_get)
        get_audio.start()
        audio_sound = threading.Thread(target=self.sound_audio)
        audio_sound.start()

    def regular_reminder(self, data):
        text = self.win.wait_until_time(data['time'], data['text'])
        logger.info(text)
        self.data_received.emit(text)
        self.his.emit(text)
        self.audio = comunication.Com(self.host, self.port)
        self.audio.send_data(comunication.STRING, '合成语音')
        self.audio.send_data(comunication.STRING, text)
        get_audio = threading.Thread(target=self.audio_get)
        get_audio.start()
        audio_sound = threading.Thread(target=self.sound_audio)
        audio_sound.start()

    def sound_audio(self):
        while True:
            if len(self.frame) > 0:
                data = self.frame[:self.chunk]
                self.frame = self.frame[self.chunk:]
                self.audio.write_audio(data)
            else:
                if not self.flag and not len(self.frame):
                    break

    def audio_get(self):
        self.flag = True
        self.frame = b''
        while True:
            data = self.audio.s.recv(1024)
            if not data:
                break  # 没有更多数据，退出循环
            if data:
                self.frame += data
        self.flag = False
        # if self.frame:
        #     self.audio.write_audio(self.frame)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, host, port, user, parent=None):
        super(MainWindow, self).__init__(parent)
        self.frame = b''
        self.setupUi(self)
        self.host = host
        self.port = port
        self.user = user
        self.audio = None
        self.mode = '💬 Chat'
        self.sum = 0  # 气泡数量
        self.widgetlist = []  # 记录气泡
        self.history = User.load_history(str(self.user.uid))
        self.text = ""  # 存储信息
        self.icon = QtGui.QPixmap("./resource/icon/1.jpg")  # 头像
        self.guka_icon = QtGui.QPixmap("./resource/icon/icon.png")
        # 设置聊天窗口样式 隐藏滚动条
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 信号与槽
        self.pushButton.clicked.connect(self.create_widget)  # 创建气泡
        # self.pushButton.clicked.connect(self.set_widget)            #修改气泡长宽
        self.plainTextEdit.undoAvailable.connect(self.Event)  # 监听输入框状态
        scrollbar = self.scrollArea.verticalScrollBar()
        scrollbar.rangeChanged.connect(self.adjustScrollToMaxValue)  # 监听窗口滚动条范围

    # 回车绑定发送
    def Event(self):
        if not self.plainTextEdit.isEnabled():  # 这里通过文本框的是否可输入
            self.plainTextEdit.setEnabled(True)
            self.pushButton.click()
            self.plainTextEdit.setFocus()

    # 创建气泡
    def create_widget(self):
        self.text = self.plainTextEdit.toPlainText()
        self.plainTextEdit.setPlainText("")
        self.sum += 1
        Set_question.set_return(self, self.icon, self.text, QtCore.Qt.RightToLeft)  # 调用new_widget.py中方法生成右气泡
        self.widgetlist.append(self.widget)
        QApplication.processEvents()
        font = QFont()
        font.setPointSize(16)
        fm = QFontMetrics(font)
        text_width = fm.width(self.text) + 125  # 根据字体大小生成适合的气泡宽度
        if text_width > 632:  # 宽度上限
            text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
        self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
        self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        conversation.append_conversation(conversation.Conversation(
            conversation.Role.USER,
            self.text,
            self.widget.minimumSize().width(),
            self.widget.minimumSize().height()+25,
        ), self.history)
        QApplication.processEvents()
        if self.mode == '💬 Chat':
            self.sum += 1
            Set_question.set_return(self, self.guka_icon, "", QtCore.Qt.LeftToRight)  # 调用new_widget.py中方法生成右气泡
            self.widgetlist.append(self.widget)
            QApplication.processEvents()
            text_width = fm.width("") + 125  # 根据字体大小生成适合的气泡宽度
            if self.sum != 0:
                if text_width > 632:  # 宽度上限
                    text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
                self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
                self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
                self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
                self.thread = WorkerThread(self.host, self.port, self.mode, self.text, self.user)
                self.thread.data_received.connect(self.set_Text)
                self.thread.his.connect(self.add_history)
                # 启动线程
                self.thread.start()
                QApplication.processEvents()
        elif self.mode == '🛠️ Tool':
            self.thread = WorkerThread(self.host, self.port, self.mode, self.text, self.user)
            self.thread.data_received.connect(self.set_tool_text)
            self.thread.his.connect(self.add_history)
            # 启动线程
            self.thread.start()
            # self.audio = comunication.Com(self.host, self.port)
            # self.audio.send_data(comunication.STRING, "对话")
            # self.audio.send_data(comunication.JSON,
            #                      {'flag': "推理", 'mode': self.mode, 'retry': 0, 'top_p': 0.8,
            #                       'temperature': 0.95, 'prompt_text': self.text,
            #                       'repetition_penalty': 1.1, 'max_new_token': 256,
            #                       'uid': "56125a13-ac5b-447e-9468-ed47b54556bf"})

            # data_type, data = self.audio.receive_data()
            # if data_type == comunication.STRING:
            #     self.sum += 1
            #     Set_question.set_return(self, self.guka_icon, data.strip(), QtCore.Qt.LeftToRight)  # 调用new_widget.py中方法生成右气泡
            #     self.widgetlist.append(self.widget)
            #     QApplication.processEvents()
            #     text_width = fm.width(data.strip()) + 125  # 根据字体大小生成适合的气泡宽度
            #     if text_width > 632:  # 宽度上限
            #         text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
            #     self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
            #     self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
            #     self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
            #     QApplication.processEvents()

    def add_history(self, data):
        conversation.append_conversation(conversation.Conversation(
            conversation.Role.ASSISTANT,
            data,
            self.widget.minimumSize().width(),
            self.widget.minimumSize().height()+25,
        ), self.history)
        t = threading.Thread(target=User.save_history,
                             args=(str(self.user.uid), self.history,))
        t.start()

    def set_tool_text(self, data):
        data = data.strip()
        font = QFont()
        font.setPointSize(16)
        fm = QFontMetrics(font)
        self.sum += 1
        Set_question.set_return(self, self.guka_icon, data.strip(), QtCore.Qt.LeftToRight)  # 调用new_widget.py中方法生成右气泡
        self.widgetlist.append(self.widget)
        QApplication.processEvents()
        text_width = fm.width(data.strip()) + 125  # 根据字体大小生成适合的气泡宽度
        if text_width > 632:  # 宽度上限
            text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
        self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
        self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        QApplication.processEvents()

    def set_Text(self, data):
        data = data.strip()
        font = QFont()
        font.setPointSize(16)
        fm = QFontMetrics(font)
        text_width = fm.width(data) + 125  # 根据字体大小生成适合的气泡宽度
        if self.sum != 0:
            if text_width > 632:  # 宽度上限
                text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
            f = self.widget.findChild(QTextBrowser)
            f.setText(data)
            self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
            self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
            self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        QApplication.processEvents()

    # if self.sum % 2:   # 根据判断创建左右气泡
    #      Set_question.set_return(self, self.icon, self.text,QtCore.Qt.LeftToRight)    # 调用new_widget.py中方法生成左气泡
    #      QApplication.processEvents()                                # 等待并处理主循环事件队列
    # else:
    #     Set_question.set_return(self, self.icon, self.text,QtCore.Qt.RightToLeft)   # 调用new_widget.py中方法生成右气泡
    #     QApplication.processEvents()                                # 等待并处理主循环事件队列

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.check_size)

    def check_size(self):
        if self.sum == 0:
            if len(self.history):
                for i in range(0, len(self.history)):
                    if self.history[i].role.value == conversation.Role.USER.value:
                        self.create_guka_widget(self.history[i].content,
                                                self.history[i].width, self.history[i].height, "R")
                    else:
                        self.create_guka_widget(self.history[i].content,
                                                self.history[i].width, self.history[i].height)
        else:
            if len(self.history) > self.sum:
                for i in range(self.sum - 1, len(self.history)):
                    if self.history[i].role.value == conversation.Role.USER.value:
                        self.create_guka_widget(self.history[i].content,
                                                self.history[i].width, self.history[i].height, "R")
                    else:
                        self.create_guka_widget(self.history[i].content,
                                                self.history[i].width, self.history[i].height)

    def create_guka_widget(self, text, width, height, direction="L"):
        if direction == "L":
            set_direction = QtCore.Qt.LeftToRight
            tou = self.guka_icon
        else:
            set_direction = QtCore.Qt.RightToLeft
            tou = self.icon
        self.sum += 1
        Set_question.set_return(self, tou, text, set_direction)  # 调用new_widget.py中方法生成气泡
        QApplication.processEvents()
        self.widgetlist.append(self.widget)
        # font = QFont()
        # font.setPointSize(16)
        # fm = QFontMetrics(font)
        # text_width = fm.width(self.text) + 125  # 根据字体大小生成适合的气泡宽度
        # if text_width > 632:  # 宽度上限
        #     text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
        self.widget.setMinimumSize(width, height)  # 规定气泡大小
        self.widget.setMaximumSize(width, height)  # 规定气泡大小
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        QApplication.processEvents()

    # def set_text(self, audio):
    #     first = True
    #     while True:
    #         data_type, data = audio.receive_data()
    #         logger.info(data)
    #         if data == "end":
    #             break
    #         if first:
    #             first = False
    #             self.text = data
    #             self.pushButton.click()
    #         self.set_guka_widget(data)
    #     # 你可以通过这个下面代码中的数组单独控制每一条气泡
    #     # self.widgetlist.append(self.widget)
    #     # print(self.widgetlist)
    #     # for i in range(self.sum):
    #     #     f=self.widgetlist[i].findChild(QTextBrowser)    #气泡内QTextBrowser对象
    #     #     print("第{0}条气泡".format(i),f.toPlainText())
    #     #     f.setText("1111")
    #     #     font = QFont()
    #     #     font.setPointSize(16)
    #     #     fm = QFontMetrics(font)
    #     #     f.setMinimumSize(fm.width("1111")+125,int(self.textBrowser.document().size().height()) + 50)
    #     #     print("第{0}条气泡".format(i), f.toPlainText())
    #
    # # 修改气泡长宽
    # def set_widget(self):
    #     font = QFont()
    #     font.setPointSize(16)
    #     fm = QFontMetrics(font)
    #     text_width = fm.width(self.text) + 125  # 根据字体大小生成适合的气泡宽度
    #     if self.sum != 0:
    #         if text_width > 632:  # 宽度上限
    #             text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
    #         self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         self.scrollArea.verticalScrollBar().setValue(10)
    #         self.text = ''
    #
    # def set_guka_widget(self, text):
    #     font = QFont()
    #     font.setPointSize(16)
    #     fm = QFontMetrics(font)
    #     text_width = fm.width(text) + 125  # 根据字体大小生成适合的气泡宽度
    #     if self.sum != 0:
    #         if text_width > 632:  # 宽度上限
    #             text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
    #         f = self.widgetlist[self.sum - 1].findChild(QTextBrowser)
    #         f.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         f.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         self.scrollArea.verticalScrollBar().setValue(10)
    #
    # def set_user_widget(self, text):
    #     font = QFont()
    #     font.setPointSize(16)
    #     fm = QFontMetrics(font)
    #     text_width = fm.width(text) + 125  # 根据字体大小生成适合的气泡宽度
    #     if self.sum != 0:
    #         if text_width > 632:  # 宽度上限
    #             text_width = int(self.textBrowser.document().size().width()) + 100  # 固定宽度
    #         self.widget.setMinimumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         self.widget.setMaximumSize(text_width, int(self.textBrowser.document().size().height()) + 50)  # 规定气泡大小
    #         self.scrollArea.verticalScrollBar().setValue(10)

    # 窗口滚动到最底部
    def adjustScrollToMaxValue(self):
        scrollbar = self.scrollArea.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event: QCloseEvent) -> None:
        self.close()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     win = MainWindow('127.0.0.1',11222)
#     win.show()
#     sys.exit(app.exec_())
