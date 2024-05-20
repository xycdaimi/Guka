import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from pet import pet
import comunication
from User import User

class Login(object):
    def __init__(self, host, port):
        self.user = None
        self.audio = None
        self.via = None
        self.form = None
        self.host = host
        self.port = port

    def setupUi(self, Form):
        self.form = Form
        self.form.setObjectName("Form") 
        desktop = QtWidgets.QApplication.desktop()
        self.form.setFixedSize(desktop.width() // 4, desktop.height() // 2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.form.setFont(font)
        self.frame = QtWidgets.QFrame(self.form)
        self.frame.setStyleSheet("QFrame{background-color:rgb(205,205,205)}"
                                 "QFrame{border-radius:10px}")
        op = QtWidgets.QGraphicsOpacityEffect()
        op.setOpacity(1)
        self.frame.setGraphicsEffect(op)
        self.frame.setGeometry(QtCore.QRect(14, 20, self.form.width() -30, self.form.height() - 40))
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.via = QtWidgets.QLabel(self.frame)
        pix = QtGui.QPixmap('./resource/icon/icon.png')
        self.via.setGeometry(self.frame.width() // 2 - 100, 20, 200, 200)
        self.via.setPixmap(pix)
        # self.via.setStyleSheet("border: 2px solid red")
        self.via.setScaledContents(True)
        self.usernameLabel = QtWidgets.QLabel(self.frame)
        self.usernameLabel.setGeometry(QtCore.QRect(100, 280, 70, 30))
        self.usernameLabel.setObjectName("usernameLabel")
        self.usernameLabel.setFont(font)
        self.usernameEdit = QtWidgets.QLineEdit(self.frame)
        self.usernameEdit.setGeometry(QtCore.QRect(180, 280, 180, 30))
        self.usernameEdit.setText("")
        self.usernameEdit.setObjectName("usernameEdit")
        self.usernameEdit.setFont(font)
        self.passwordLabel = QtWidgets.QLabel(self.frame)
        self.passwordLabel.setGeometry(QtCore.QRect(100, 320, 70, 30))
        self.passwordLabel.setObjectName("passwordLabel")
        self.passwordLabel.setFont(font)
        self.passwordEdit = QtWidgets.QLineEdit(self.frame)
        self.passwordEdit.setGeometry(QtCore.QRect(180, 320, 180, 30))
        self.passwordEdit.setObjectName("passwordEdit")
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        # self.passwordEdit.setFont(font)
        self.checkBox = QtWidgets.QCheckBox(self.frame)
        self.checkBox.setGeometry(QtCore.QRect(100, 360, 220, 20))
        self.checkBox.setObjectName("checkBox")
        self.buttonBox = QtWidgets.QDialogButtonBox(self.frame)
        self.buttonBox.setGeometry(QtCore.QRect(100, 400, 180, 30))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("登录")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setStyleSheet(
            "QPushButton{color:black}"
            "QPushButton:hover{color:red}"
            "QPushButton{background-color:rgb(180,180,180)}"
            "QPushButton{border:2px}"
            "QPushButton{border-radius:10px}"
            "QPushButton{padding:2px 4px}"
            "QPushButton{font-size:14pt}")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText("注册")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setStyleSheet(
            "QPushButton{color:black}"
            "QPushButton:hover{color:red}"
            "QPushButton{background-color:rgb(180,180,180)}"
            "QPushButton{border:2px}"
            "QPushButton{border-radius:10px}"
            "QPushButton{padding:2px 4px}"
            "QPushButton{font-size:14pt}")
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.clicked.connect(self.on_button_clicked)
        self.retranslateUi(self.form)
        QtCore.QMetaObject.connectSlotsByName(self.form)
        if os.path.exists("./resource/user.json"):
            self.user = User.User.load_from_json("user.json")
            self.usernameEdit.setText(self.user.password)
            self.passwordEdit.setText(self.user.password)
            self.checkBox.setChecked(True)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Guka"))
        # 创建图标对象
        icon = QIcon("./resource/icon/icon.png")
        # 设置窗口图标
        Form.setWindowIcon(icon)
        self.usernameLabel.setText(_translate("Form", "用户名"))
        self.passwordLabel.setText(_translate("Form", "密  码"))
        self.checkBox.setText(_translate("Form", "记住用户名和密码"))

    def on_button_clicked(self, button):
        username = self.usernameEdit.text()
        password = self.passwordEdit.text()
        self.audio = comunication.Com(self.host, self.port)
        self.audio.send_data(comunication.STRING, button.text())
        if button.text() == "登录":
            self.audio.send_data(comunication.JSON, {'username': username, 'password': password})
            data_type, data = self.audio.receive_data()
            if data == "ok":
                data_type, data = self.audio.receive_data()
                self.user = User.User(data['uid'], username, password)
                if self.checkBox.isChecked():
                    self.user.save_to_json("user.json")
                guka = pet.DesktopPet(self.host, self.port, self.user)
                guka.app.setQuitOnLastWindowClosed(False)
                guka.app.exec_()
                self.form.close()
            else:
                msgBox = QMessageBox()
                # 设置弹窗的标题和文本
                msgBox.setWindowTitle('错误提示')
                msgBox.setText(data)
                msgBox.setIcon(QIcon("./resource/icon/icon.png"))
                # 显示弹窗，并等待用户响应
                msgBox.exec_()
        elif button.text() == "注册":
            uid = User.generate_user_id()
            self.audio.send_data(comunication.JSON, {'uid': uid, 'username': username, 'password': password})
            data_type, data = self.audio.receive_data()
            if data == "ok":
                self.user = User.User(uid, username, password)
                if self.checkBox.isChecked():
                    self.user.save_to_json("user.json")
                guka = pet.DesktopPet(self.host, self.port, self.user)
                guka.app.setQuitOnLastWindowClosed(False)
                guka.app.exec_()
                self.form.close()
            else:
                msgBox = QMessageBox()
                # 设置弹窗的标题和文本
                msgBox.setWindowTitle('错误提示')
                msgBox.setText(data)
                # 设置弹窗的图标类型（可选）
                msgBox.setIcon(QIcon("./resource/icon/icon.png"))
                # 显示弹窗，并等待用户响应
                msgBox.exec_()

# if __name__ == "__main__":
#     import sys
#
#     app = QtWidgets.QApplication(sys.argv)
#     widget = QtWidgets.QWidget()
#     ui = Login()
#     ui.setupUi(widget)
#     widget.show()
#     sys.exit(app.exec_())
