import User.User
from chatglm.client import client,svc
from chatglm.conversation import postprocess_text, preprocess_text, Conversation, Role
import log
from User import User
import threading
from tts import TTSController
from comunication import comunication
import wave
import os
import copy
logger = log.get_log(__name__)

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
        no = 0
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
            audio.send_data(conn,comunication.STRING,output_text+ '▌')
        audio.send_data(conn,comunication.STRING,output_text)
        audio.send_data(conn,comunication.STRING,"end")
        ttstr = TTSController(uid+'.wav')
        ttstr.textToaudio(output_text)
        svc.forward([uid+'.wav'],uid)
        rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+uid+'.wav',))
        rmraw.start()
        with wave.open('./results/'+uid+'.wav', 'rb') as wav_file:
            while True:
                vioce_data = wav_file.readframes(1024)
                if not vioce_data:
                    break  # 没有更多数据了
                conn.sendall(vioce_data)
        rmfile = threading.Thread(target=User.remove_file,args=('./results/'+uid+'.wav',))
        rmfile.start()
        append_conversation(Conversation(
            Role.ASSISTANT,
            postprocess_text(output_text),
        ), history)
        User.save_history(file_path=uid,history=history)