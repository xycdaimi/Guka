"""
This code is the tool registration part. By registering the tool, the model can call the tool.
This code provides extended functionality to the model, enabling it to call and interact with a variety of utilities
through defined interfaces.
"""
import comunication
import copy
import inspect
from pprint import pformat
import traceback
from types import GenericAlias
from typing import get_origin, Annotated
import subprocess
import socket
import log
import datetime
logger = log.get_log(__name__)
_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = {}


def register_tool(func: callable):
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = []
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:
            raise TypeError(f"Annotation type for `{name}` must be typing.Annotated")

        typ, (description, required) = annotation.__origin__, annotation.__metadata__
        typ: str = str(typ) if isinstance(typ, GenericAlias) else typ.__name__
        if not isinstance(description, str):
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params.append({
            "name": name,
            "description": description,
            "type": typ,
            "required": required
        })
    tool_def = {
        "name": tool_name,
        "description": tool_description,
        "params": tool_params
    }
    print("[registered tool] " + pformat(tool_def))
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS[tool_name] = tool_def

    return func


def dispatch_tool(tool_name: str, tool_params: dict) -> str:
    if tool_name not in _TOOL_HOOKS:
        return f"Tool `{tool_name}` not found. Please use a provided tool."
    tool_call = _TOOL_HOOKS[tool_name]
    try:
        ret = tool_call(**tool_params)
    except:
        ret = traceback.format_exc()
    return str(ret)


def get_tools() -> dict:
    return copy.deepcopy(_TOOL_DESCRIPTIONS)


# Tool Definitions

# @register_tool
# def random_number_generator(
#         seed: Annotated[int, 'The random seed used by the generator', True],
#         range: Annotated[tuple[int, int], 'The range of the generated numbers', True],
# ) -> int:
#     """
#     Generates a random number x, s.t. range[0] <= x < range[1]
#     """
#     if not isinstance(seed, int):
#         raise TypeError("Seed must be an integer")
#     if not isinstance(range, tuple):
#         raise TypeError("Range must be a tuple")
#     if not isinstance(range[0], int) or not isinstance(range[1], int):
#         raise TypeError("Range must be a tuple of integers")

#     import random
#     return random.Random(seed).randint(*range)


@register_tool
def get_weather(
        city_name: Annotated[str, 'The name of the city to be queried', True],
) -> str:
    """
    Get the current weather for `city_name`，不要有多余的解释，回答禁止加上什么时候获取的
    """

    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    print("a")
    import requests
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        print("1")
        resp.raise_for_status()
        print("2")
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()
    return str(ret)

@register_tool
def regular_reminder(
        time: Annotated[str, "要定时到的时间，格式必须为`H时M分`", True],
        text: Annotated[str, '要提醒的内容的中文文本，如果是英文需要翻译成中文', True],
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       设置闹钟，定时提醒主人我做事情，到达指定时间将进行提醒，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        audio.send_data(conn, comunication.STRING, "定时提醒")
        audio.send_data(conn, comunication.JSON, {'time':time,'text':text})
        return "好的，主人。我将在"+time+"提醒您"+text+"。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我没有听清楚您说的话。"

@register_tool
def open_app(
        app_name: Annotated[str, '应用程序的名称', True],
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       打开名字为`app_name`的应用程序，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        audio.send_data(conn, comunication.STRING, "打开:"+app_name)
        data_type, data = audio.receive_data(conn)
        if data:
            return "好的，主人，马上帮您打开"+app_name+"。"
        else:
            return "抱歉，主人。应用列表里没有这个应用，我无法打开它。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我现在无法帮您打开"+app_name+"。"

@register_tool
def set_audio_volume(
        volume: Annotated[int, '音量设置的数值，从0到100之间', True],
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       当有说明具体的数值时，使用这个函数设置电脑音量，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        if not isinstance(volume, int):
            raise TypeError("volume must be an integer")
        audio.send_data(conn, comunication.STRING, "音量设置")
        audio.send_data(conn, comunication.JSON,{"volume":volume})
        return "好的，主人，已经为您设置音量。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我没有成功设置音量。"


@register_tool
def lock_computer(
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       锁屏电脑，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        audio.send_data(conn, comunication.STRING, "锁定电脑")
        return "好的，主人，马上帮您锁屏。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我现在无法帮您锁屏。"

@register_tool
def get_local_time(
) -> str:
    """
       获取现在的时间
    """
    try:
        # 获取当前时间
        current_time = datetime.datetime.now()
        # 格式化当前时间
        formatted_time_without_weekday = current_time.strftime("%Y-%m-%d %H:%M:%S")  # 包括年、月、日、时、分、秒
        # 获取星期几的英文缩写（例如：Mon）
        weekday_abbr = current_time.strftime("%a")
        # 定义英文星期缩写到中文的映射
        weekday_abbr_to_chinese = {
            "Mon": "星期一",
            "Tue": "星期二",
            "Wed": "星期三",
            "Thu": "星期四",
            "Fri": "星期五",
            "Sat": "星期六",
            "Sun": "星期日"
        }
        # 获取对应的中文星期几
        chinese_weekday = weekday_abbr_to_chinese[weekday_abbr]
        # 拼接完整的格式化时间字符串，包括中文星期几
        formatted_time = f"{formatted_time_without_weekday} {chinese_weekday}"
        # 打印格式化后的当前时间
        logger.info(formatted_time)
        return "当前时间："+formatted_time
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我没有获取到现在的时间。"


@register_tool
def close_computer(
        time: Annotated[str, "要定时到的时间，格式必须为`H时M分`", True],
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       定时关闭用户的电脑，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        audio.send_data(conn, comunication.STRING, "定时关机")
        audio.send_data(conn, comunication.STRING, time)
        return "好的，主人，已经设置定时关机。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我现在无法帮您定时关闭电脑。"

@register_tool
def restart_computer(
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       重启电脑，直接将返回的字符串作为回复，不要自己回复
    """
    try:
        audio.send_data(conn, comunication.STRING, "重启电脑")
        return "好的，主人，马上帮您重启电脑。"
    except Exception as e:
        logger.error(e)
        return "抱歉，主人，我现在无法帮您重启电脑。"

@register_tool
def get_www(
        name: Annotated[str, '网站的中文名称，该名称必须是用户输入的字符串里包含的', True],
        audio: Annotated[comunication.Com, '这是用来发送数据所封装好的类的实例', True],
        conn: Annotated[socket.socket, '这是一个与客户端的socket连接', True],
) -> str:
    """
       打开对应名字为`name`的网站，直接将返回的字符串作为回复，不要有多余的解释，回复语句不要出现网址
    """
    if not isinstance(name, str):
        raise TypeError("网站的名字必须是字符串")
    try:
        audio.send_data(conn, comunication.STRING, "打开网址:"+name)
        data_type, data = audio.receive_data(conn)
        if data == "open":
            return "主人，现在正在打开"+name+"的网站。"
        else:
            return "抱歉，主人，我没有在浏览器的收藏夹里找到这个网站，无法打开它。"
    except Exception as e:
        logger.error(e)
        return '抱歉，主人，我没有听清楚你说什么，能再说一遍吗？'

@register_tool
def get_shell(
        query: Annotated[str, 'The command should run in Linux shell', True],
) -> str:
    """
       Use shell to run command
    """
    if not isinstance(query, str):
        raise TypeError("Command must be a string")
    try:
        result = subprocess.run(query, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


# if __name__ == "__main__":
    # print(dispatch_tool("get_shell", {"query": "pwd"}))
    # print(get_tools())