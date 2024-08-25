import User.User
from chatglm.client import client,svc, closeLock
from chatglm.conversation import postprocess_text, preprocess_text, Conversation, Role
import log
from User import User
import threading
from tts import TTSController
from comunication import comunication
import wave
import os
import copy
import time
logger = log.get_log(__name__)
said_text = {}
lock = threading.Lock()
def text_to_audio(conn, audio):
    i=0
    while True:
        audio_cache = said_text[conn]
        if len(audio_cache)>0:
            print(audio_cache)
            text = audio_cache[i]
            if text == "ok":
                # with lock:
                audio.send_data(conn, comunication.FLAG, text)
                said_text.pop(conn)
                break
            ttstr = TTSController(str.format('%d.wav'%i))
            ttstr.textToaudio(text)
            res = svc.forward2([str.format('%d.wav'%i)])
            # with lock:
            audio.send_data(conn, comunication.LONG_AUDIO, res)
            rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+str.format('%d.wav'%i),))
            rmraw.start()
            i += 1
        else:
            time.sleep(0.5)
    conn.close()

# Append a conversation into history, while show it in a new markdown block
def append_conversation(
        conversation: Conversation,
        history: list[Conversation],
) -> None:
    history.append(conversation)
def getAudio(file_path,text):
    ttstr = TTSController(file_path+'.wav')
    ttstr.textToaudio(text)
    svc_copy = copy.deepcopy(svc)
    svc_copy.forward([file_path+'.wav'],file_path)
    rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+file_path+'.wav',))
    rmraw.start()

def main(
        prompt_text: str,
        system_prompt: str,
        uid: str,
        addr,
        conn,
        audio,
        top_p: float = 0.8,
        temperature: float = 0.95,
        repetition_penalty: float = 1.0,
        max_new_tokens: int = 1024,
        retry: bool = False,
):

    history: list[Conversation] = User.load_history(uid)
    if history == None:
        history = []
    if prompt_text:
        prompt_text = prompt_text.strip()
        append_conversation(Conversation(Role.USER, prompt_text), history)
        output_text = ''
        audio_text = ''
        # said_text[conn] = []
        # textToAudio_th = threading.Thread(target=text_to_audio,args=(conn,audio,))
        # textToAudio_th.start()
        for response in client.generate_stream(
                system_prompt,
                tools=None,
                history=history,
                do_sample=True,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=[str(Role.USER)],
                repetition_penalty=repetition_penalty,
        ):
            token = response.token
            if response.token.special:
                #print("\n==Output:==\n", output_text)
                match token.text.strip():
                    case '<|user|>':
                        break
                    case _:
                        logger.error(f'Unexpected special token: {token.text.strip()}')
                        break
            output_text += response.token.text
            audio_text += response.token.text
            if response.token.text in ['.','。','?','？','!','！',';','；',':','：']:
                print(output_text)
                # with lock:
                said_text[conn].append(audio_text.strip('\n'))
                audio_text = ""
            if output_text:
                # with lock:
                audio.send_data(conn,comunication.STRING,output_text+ '▌')
        # with lock:
        if audio_text != "":
            said_text[conn].append(audio_text)
            audio_text = ""
        said_text[conn].append("ok")
        audio.send_data(conn,comunication.STRING,output_text)
        audio.send_data(conn,comunication.FLAG,"end")
        # ttstr = TTSController(uid+'.wav')
        # ttstr.textToaudio(output_text)
        # svc.forward2(conn, [uid+'.wav'])
        # rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+uid+'.wav',))
        # rmraw.start()



        # with wave.open('./results/'+uid+'.wav', 'rb') as wav_file:
        #     while True:
        #         vioce_data = wav_file.readframes(1024)
        #         if not vioce_data:
        #             break  # 没有更多数据了
        #         conn.sendall(vioce_data)
        # rmfile = threading.Thread(target=User.remove_file,args=('./results/'+uid+'.wav',))
        # rmfile.start()
        append_conversation(Conversation(
            Role.ASSISTANT,
            postprocess_text(output_text),
        ), history)
        User.save_history(file_path=uid,history=history)