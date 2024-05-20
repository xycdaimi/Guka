import log
logger = log.setup_log(file_name="server.log")
import os
import threading
import comunication
import tts
import signal
import sys
from User import User
from speak import speak
import wave
from chatglm import demo_chat, demo_tool
#, demo_ci
from enum import Enum
from chatglm.client import svc
class Mode(str, Enum):
    CHAT, TOOL, CI = '💬 Chat', '🛠️ Tool', '🧑‍💻 Code Interpreter'
DEFAULT_SYSTEM_PROMPT = '''
你的名字是咕卡，要记住这个名字，你是一只会说话、了解各种知识的宠物，可以自由回答问题，回答要尽量地简洁，像人类一样思考和表达。你可以调用各种API工具函数，例如打开应用等等，以此辅助我完成各项工作，陪我聊天和学习，给我带来欢声笑语，给予我精神上的寄托，请尽量使用中文回答我。
'''.strip()
clients = []
users = User.load_users_from_json(User.FILE_PATH)
def remove_file(file_path):
    try:
        if os.path.exists(file_path):
            # 删除文件
            os.remove(file_path)
            logger.info(f"{file_path} has been deleted.")
        else:
            logger.info(f"{file_path} does not exist.")
    except Exception as e:
        logger.error(e)
def get_client_index(clients, client_socket):
    try:
        return clients.index(client_socket)
    except ValueError:
        return -1
def start_main(audio, say, conn,addr):
    file_path = 'recoding'+str(addr)+'.wav'
    audio.wav_rw('wb',file_path)
    tab = 0
    while True:
        data_type, data = audio.receive_data(conn)
        if data == "登录":
            break
        elif data == "注册":
            break
        elif data == "end":
            audio.wav_close()
            break
        elif data == "对话":
            break
        elif data == '合成语音':
            break
        elif data_type == comunication.AUDIO:
            audio.accept_data(data)
    if data == "登录":
        audio.wav_close()
        rmreo = threading.Thread(target=remove_file,args=(file_path,))
        rmreo.start()
        data_type, data = audio.receive_data(conn)
        res = User.choice_user(users, data['username'], data['password'])
        if res == -1:
            audio.send_data(conn,comunication.STRING, "用户名错误")
        elif res == -2:
            audio.send_data(conn,comunication.STRING, "密码错误")
        elif res == -3:
            audio.send_data(conn,comunication.STRING, "用户不存在")
        else:
            audio.send_data(conn,comunication.STRING, "ok")
            audio.send_data(conn,comunication.JSON, {'uid': res.uid})
    elif data == "注册":
        audio.wav_close()
        rmreo = threading.Thread(target=remove_file,args=(file_path,))
        rmreo.start()
        data_type, data = audio.receive_data(conn)
        user = User.User(uid=data['uid'],username=data['username'],password=data['password'])
        res = User.is_registered(users,user)
        if res:
            audio.send_data(conn,comunication.STRING, "ok")
        else:
            audio.send_data(conn,comunication.STRING, "用户名已存在")
    elif data == "end":
        text = say.forward(file_path)
        audio.send_data(conn, comunication.STRING,text)
        rmreo = threading.Thread(target=remove_file,args=(file_path,))
        rmreo.start()
    elif data == '合成语音':
        audio.wav_close()
        rmreo = threading.Thread(target=remove_file,args=(file_path,))
        rmreo.start()
        data_type, data = audio.receive_data(conn)
        ttstr = tts.TTSController(str(addr)+'.wav')
        if data_type == comunication.STRING:
            ttstr.textToaudio(data.strip())
            svc.forward([str(addr)+'.wav'], str(addr))
            with wave.open('./results/'+str(addr)+'.wav', 'rb') as wav_file:
                while True:
                    vioce_data = wav_file.readframes(1024)
                    if not vioce_data:
                        break  # 没有更多数据了
                    conn.sendall(vioce_data)
            remove_file('./raw/'+str(addr)+'.wav')
            remove_file('./results/'+str(addr)+'.wav')
    elif data == "对话":
        audio.wav_close()
        rmreo = threading.Thread(target=remove_file,args=(file_path,))
        rmreo.start()
        data_type, data = audio.receive_data(conn)
        logger.info(data)
        if data['flag'] == "推理":
            match data['mode']:
                case Mode.CHAT:
                    demo_chat.main(
                        retry=data['retry'],
                        top_p=data['top_p'],
                        temperature=data['temperature'],
                        prompt_text=data['prompt_text'],
                        system_prompt=DEFAULT_SYSTEM_PROMPT,
                        repetition_penalty=data['repetition_penalty'],
                        max_new_tokens=data['max_new_token'],
                        uid=data['uid'],
                        addr=addr,
                        conn=conn,
                        audio=audio
                    )
                case Mode.TOOL:
                    demo_tool.main(
                        system_prompt=DEFAULT_SYSTEM_PROMPT,
                        retry=data['retry'],
                        top_p=data['top_p'],
                        temperature=data['temperature'],
                        prompt_text=data['prompt_text'],
                        repetition_penalty=data['repetition_penalty'],
                        max_new_tokens=data['max_new_token'],
                        truncate_length=1024,
                        uid=data['uid'],
                        addr=addr,
                        conn=conn,
                        audio=audio)
                case Mode.CI:
                    demo_ci.main(
                        retry=data.retry,
                        top_p=data.top_p,
                        temperature=data.temperature,
                        prompt_text=data.prompt_text,
                        repetition_penalty=data.repetition_penalty,
                        max_new_tokens=data.max_new_token,
                        truncate_length=1024,
                        uid=data.uid,
                        addr=addr,
                        conn=conn,
                        audio=audio)
                case _:
                    logger.error(f'Unexpected tab: {tab}')
    clients.remove(conn)
    conn.close()
if __name__ == '__main__':
    try:
        say = speak.Yuyin()
        #host = '127.0.0.1'
        host = '192.168.137.67'
        port = 11222
        audio = comunication.Com(host, port)
        def signal_handler(signal, frame):  
            print('Stopping...')
            audio.close_down()
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        while True:
            conn, addr = audio.s.accept()
            clients.append(conn)
            client_thread = threading.Thread(target=start_main,args=(audio,say,conn,addr,))
            client_thread.start()
    except Exception as e:
        logger.error(e)
