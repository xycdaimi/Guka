import json
from os import path, rename, remove
import requests
import search
import log

logger = log.setup_log(file_name="guka.log")
import pyaudio
from pet import pet
import sys
from urllib.request import urlretrieve


def check_exists(file):
    return path.exists(file)


def is_updated(old, new):
    updated = False
    if old < new:
        updated = True


def download(param, appname):
    try:
        urlretrieve(param, appname)
    except (RuntimeError, ConnectionError):
        urlretrieve(param, appname)


def get_json(update_file):
    with open(update_file, 'r', encoding='utf-8') as f:
        content = json.loads(f.read())
        return content


def get_json_server(r_version):
    r_content = requests.get(r_version).json()
    return r_content


def check_version():
    # 版本文件
    update_file = 'update.json'
    # 本地版本信息
    content = get_json(update_file)
    # 获取服务器版本信息
    r_content = get_json_server(content['version_url'])
    # 老版本号与新版本号
    old = content['version']
    new = r_content['version']
    # 零时名称
    appname = content['name'] + '_new.exe'
    # 是否有新版本
    updated = is_updated(old, new)
    # 有新版本并且没有下载好的文件
    if updated and not check_exists(appname):
        print("开始下载...")
        download(content['download_url'], appname)
        print("下载完成！")
    # 删除本地版本
    old_name = content['name'] + '.exe'
    if updated and check_exists(old_name):
        print("删除老版本")
        remove(old_name)
    # 更改新版本名称
    if updated and check_exists(appname) and not check_exists(old_name):
        print("更新名称")
        rename(appname, old_name)
    # 更新本地版本信息
    # 把远程版本号更新到本地
    if updated:
        content['version'] = r_content['version']
        with open(update_file, 'w', encoding='utf-8') as f:
            print("更新版本信息")
            json.dump(content, f, ensure_ascii=False)


def check_peizhi():
    output = "paths.json"
    if not check_exists(output):
        app = search.QApplication([])  # 创建一个QApplication实例来处理GUI事件
        search.json_file_paths('findExe.json', 'paths.json')  # 开始更新JSON文件并显示进度条


def get_ip():
    # 打开文件
    ip_address = '127.0.0.1'
    ip_port = 11222
    with open('ip.conf', 'r') as file:
        # 读取文件内容
        content = file.read()

        # 使用字符串分割和strip()函数来解析IP地址和端口
    lines = content.split('\n')
    for line in lines:
        if 'ip_address' in line:
            ip_address = line.split('=')[1].strip()
        elif 'port' in line:
            ip_port = int(line.split('=')[1].strip())
    return ip_address, ip_port


if __name__ == '__main__':
    check_peizhi()
    host, port = get_ip()
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    # 创建了一个QApplication对象，对象名为app，带两个参数argc,argv
    # 所有的PyQt5应用必须创建一个应用（Application）对象。sys.argv参数是一个来自命令行的参数列表。
    # app = pet.QApplication(sys.argv)
    # 窗口组件初始化
    pet = pet.DesktopPet(host, port, CHUNK, FORMAT, CHANNELS, RATE)
    # 1. 进入时间循环；
    # 2. wait，直到响应app可能的输入；
    # 3. QT接收和处理用户及系统交代的事件（消息），并传递到各个窗口；
    # 4. 程序遇到exit()退出时，机会返回exec()的值。
    pet.app.setQuitOnLastWindowClosed(False)
    sys.exit(pet.app.exec_())
