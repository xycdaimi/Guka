import re
import yaml
from yaml import YAMLError
import sys
import os
import log
import threading
from comunication import comunication
from tts import TTSController
import wave
from chatglm.client import client,svc
from chatglm.conversation import postprocess_text, preprocess_text, Conversation, Role
from chatglm.tool_registry import dispatch_tool, get_tools
from User import User
logger = log.get_log(__name__)
EXAMPLE_TOOL = {
    "name": "get_current_weather",
    "description": "Get the current weather in a given location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
    }
}
TOOL_USER_COMPUTER = ["get_www","restart_computer","close_computer","lock_computer","set_audio_volume","open_app","regular_reminder"]
calling_tool = False

def tool_call(*args, **kwargs) -> dict:
    print("=== Tool call===")
    print(args)
    print(kwargs)
    calling_tool = True
    return kwargs


def yaml_to_dict(tools: str) -> list[dict] | None:
    try:
        return yaml.safe_load(tools)
    except YAMLError:
        return None


def extract_code(text: str) -> str:
    pattern = r'```([^\n]*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    print(matches)
    return matches[-1][1]


# Append a conversation into history, while show it in a new markdown block
def append_conversation(
        conversation: Conversation,
        history: list[Conversation],
) -> None:
    history.append(conversation)


def main(
        prompt_text: str,
        uid: str,
        system_prompt: str,
        addr,
        conn,
        audio,
        top_p: float = 0.2,
        temperature: float = 0.1,
        repetition_penalty: float = 1.1,
        max_new_tokens: int = 1024,
        truncate_length: int = 1024,
        retry: bool = False
):
    # manual_mode = st.toggle('Manual mode',
    #                         help='Define your tools in YAML format. You need to supply tool call results manually.'
    #                         )

    # if manual_mode:
    #     with st.expander('Tools'):
    #         tools = st.text_area(
    #             'Define your tools in YAML format here:',
    #             yaml.safe_dump([EXAMPLE_TOOL], sort_keys=False),
    #             height=400,
    #         )
    #     tools = yaml_to_dict(tools)

    #     if not tools:
    #         logger.error('YAML format error in tools definition')
    # else:
    tools = get_tools()
    global calling_tool
    history: list[Conversation] = User.load_history(uid)
    if history == None:
        history = []
    history = []
    if prompt_text:
        prompt_text = prompt_text.strip()
        role = calling_tool and Role.OBSERVATION or Role.USER
        append_conversation(Conversation(role, prompt_text), history)
        calling_tool = False
        back_text = ""
        tool = ""
        for _ in range(5):
            output_text = ''
            for response in client.generate_stream(
                    system=system_prompt,
                    tools=tools,
                    history=history,
                    do_sample=True,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=[str(r) for r in (Role.USER, Role.OBSERVATION)],
                    repetition_penalty=repetition_penalty,
            ):
                token = response.token
                if response.token.special:
                    print("\n==Output:==\n", output_text)
                    match token.text.strip():
                        case '<|user|>':
                            if tool in TOOL_USER_COMPUTER:
                                output_text = back_text
                            append_conversation(Conversation(
                                Role.ASSISTANT,
                                postprocess_text(output_text),
                            ), history)
                            audio.send_data(conn,comunication.STRING,output_text)
                            ttstr = TTSController(uid+'.wav')
                            ttstr.textToaudio(output_text)
                            res = svc.forward2([uid+'.wav'])
                            audio.send_data(conn, comunication.LONG_AUDIO, res)
                            audio.send_data(conn, comunication.FLAG, "end")
                            audio.send_data(conn, comunication.FLAG, "ok")
                            rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+uid+'.wav',))
                            rmraw.start()
                            # with wave.open('./results/'+uid+'.wav', 'rb') as wav_file:
                            #     while True:
                            #         vioce_data = wav_file.readframes(1024)
                            #         if not vioce_data:
                            #             break  # 没有更多数据了
                            #         conn.sendall(vioce_data)
                            # rmfile = threading.Thread(target=User.remove_file,args=('./results/'+uid+'.wav',))
                            # rmfile.start()
                            return
                        # Initiate tool call
                        case '<|assistant|>':
                            append_conversation(Conversation(
                                Role.ASSISTANT,
                                postprocess_text(output_text),
                            ), history)
                            output_text = ''
                            continue
                        case '<|observation|>':
                            tool, *call_args_text = output_text.strip().split('\n')
                            call_args_text = '\n'.join(call_args_text)
                            append_conversation(Conversation(
                                Role.TOOL,
                                postprocess_text(output_text),
                                tool,
                            ), history)
                            try:
                                code = extract_code(call_args_text)
                                args = eval(code, {'tool_call': tool_call}, {})
                            except:
                                logger.error('Failed to parse tool call')
                                return
                            output_text = ''
                            if tool in TOOL_USER_COMPUTER:
                                args['audio'] = audio
                                args['conn'] = conn
                            observation = dispatch_tool(tool, args)
                            print(observation)
                            back_text = observation
                            if len(observation) > truncate_length:
                                observation = observation[:truncate_length] + ' [TRUNCATED]'
                            append_conversation(Conversation(
                                Role.OBSERVATION, observation
                            ), history)
                            calling_tool = False
                            break
                        case _:
                            logger.error(f'Unexpected special token: {token.text.strip()}')
                            return
                output_text += response.token.text
                # audio.send_data(conn,comunication.STRING,output_text+'▌')
            else:
                if tool in TOOL_USER_COMPUTER:
                    output_text = back_text
                audio.send_data(conn,comunication.STRING,output_text)
                ttstr = TTSController(uid+'.wav')
                ttstr.textToaudio(output_text)
                res = svc.forward2([uid+'.wav'])
                audio.send_data(conn, comunication.LONG_AUDIO, res)
                audio.send_data(conn, comunication.FLAG, "end")
                audio.send_data(conn, comunication.FLAG, "ok")
                rmraw = threading.Thread(target=User.remove_file,args=('./raw/'+uid+'.wav',))
                rmraw.start()
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
                # User.save_history(file_path=uid,history=history)
                return
