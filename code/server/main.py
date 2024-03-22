import log
logger = log.setup_log(file_name="server.log")
import chatglm
import speak
import pyaudio
import os
import shutil
import wave
import threading
import comunication
import tts
import vits
import numpy as np
clients = []
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
def start_main(audio, chat, say, svc, conn,addr):
    try:
        file_path = 'recoding'+str(addr)+'.wav'
        audio.wav_rw('wb',file_path)
        ttstr = tts.TTSController(str(addr)+'.wav')
        while True:
            data = conn.recv(audio.CHUNK)
            if not data:
                break
            elif data == b'end':
                break
            elif data == b'zf' or data == b'dq':
                textdata = conn.recv(1024).decode()
                break
            audio.accept_data(data)
        if data == b'end':
            audio.wav_close()
            user_input=say.forward(file_path)
            logger.info(user_input)
            if user_input != '':
                audio.send_data(conn,1,user_input.encode())
                #conn.sendall(user_input.encode())
                flag = conn.recv(audio.CHUNK)
                if flag == b'ok':
                    res = chat.forward(user_input)
                    logger.info(res)
                    ttstr.textToaudio(res)
                    svc.forward([str(addr)+'.wav'],str(addr))
                    audio.send_data(conn,1,res.encode())
                    with wave.open('./results/'+str(addr)+'.wav', 'rb') as wav_file:
                        while True:
                            data = wav_file.readframes(1024)
                            if not data:  
                                break  # 没有更多数据了
                            conn.sendall(data)
                    logger.info('回答发送完毕')
                else:
                    logger.info('回答结束')
        elif data == b'zf':
            if textdata:
                res = chat.forward(textdata)
                textdata = ''
                logger.info(res)
                ttstr.textToaudio(res)
                svc.forward([str(addr)+'.wav'],str(addr))
                audio.send_data(conn,1,res.encode())
                with wave.open('./results/'+str(addr)+'.wav', 'rb') as wav_file:
                    while True:
                        data = wav_file.readframes(1024)
                        if not data:  
                            break  # 没有更多数据了
                        conn.sendall(data)
                logger.info('回答发送完毕')
        elif data == b'dq':
            if textdata:
                ttstr.textToaudio(textdata)
                textdata = ''
                svc.forward([str(addr)+'.wav'],str(addr))
                with wave.open('./results/'+str(addr)+'.wav', 'rb') as wav_file:
                    while True:
                        data = wav_file.readframes(1024)
                        if not data:
                            break  # 没有更多数据了
                        conn.sendall(data)
    except Exception as e:
        logger.error(e)
    finally:
        remove_file(file_path)
        remove_file('./raw/'+str(addr)+'.wav')
        remove_file('./results/'+str(addr)+'.wav')
        clients.remove(conn)
        conn.close()
if __name__ == '__main__':
    try:
        chat = chatglm.ChatGLM('history_chat.npy')
        say = speak.Yuyin('./model/whisper/medium.pt')
        svc = vits.Phonetic_cloning()
        #host = '127.0.0.1'
        host = '192.168.137.246'
        port = 11222
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "recording.wav"
        audio = comunication.Com(host, port)
        while True:
            conn, addr = audio.s.accept()
            clients.append(conn)
            client_thread = threading.Thread(target=start_main,args=(audio,chat,say,svc,conn,addr,))
            client_thread.start()
        audio.close_down()
        svc.clear()
    except Exception as e:
        logger.error(e)
