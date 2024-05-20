import json 
import uuid
import numpy as np
import os
import log
from chatglm import conversation
from dataclasses import asdict
logger = log.get_log(__name__)
FILE_PATH = 'users.json'
users = []
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
def generate_user_id():
    return uuid.uuid4()
# 自定义序列化函数，用于处理 UUID 对象  
def default_converter(o):  
    if isinstance(o, uuid.UUID):  
        return str(o)  
    raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')
 
class User:
    def __init__(self, uid, username, password):  
        self.uid = uid  
        self.username = username  
        self.password = password
  
    def to_dict(self):  
        return {  
            'uid': self.uid,
            'username': self.username,
            'password': self.password
        }  
  
    @staticmethod  
    def from_dict(user_dict):  
        return User(user_dict['uid'], user_dict['username'], user_dict['password'])
    
    def save_to_json(self, file_path):  
        with open(file_path, 'w') as file:  
            json.dump(self.to_dict(), file)  
  
    @staticmethod
    def load_from_json(file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")
        try:
            with open(file_path, 'r') as file:
                user_dict = json.load(file)
            return User.from_dict(user_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析JSON文件 {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"在加载 {file_path} 时发生错误: {e}")
  
# 加载用户数据从JSON文件  
def load_users_from_json(file_path):  
    try:  
        with open(file_path, 'r') as file:  
            users_data = json.load(file)  
            if not users_data:  # 检查users_data是否为空列表  
                # 如果文件存在但内容为空，可以写入一个空的JSON数组  
                with open(file_path, 'w') as outfile:  
                    json.dump([], outfile)  
                return {}  
            else:  
                return {user['uid']: User.from_dict(user) for user in users_data}  
    except FileNotFoundError:  
        # 如果文件不存在，创建一个新的空文件并写入一个空的JSON数组  
        with open(file_path, 'w') as outfile:  
            json.dump([], outfile)  
        return {}


def save_history( file_path: str, history: list[conversation.Conversation]):
    # 将Conversation对象列表转换为字典列表，因为枚举类型在NumPy中可能不是直接可序列化的  
    conversation_dicts = [asdict(conv) for conv in history]  
    # 保存为.npy文件  
    np.save('./historyData/'+file_path, conversation_dicts)
    print(f"历史记录已保存到 {file_path}.npy")

def load_history(file_path: str):
    if os.path.exists('./historyData/'+file_path+'.npy'):
        # 从.npy文件加载字典列表  
        conversation_dicts = np.load('./historyData/'+file_path+'.npy', allow_pickle=True)  
        # 将字典列表转换回Conversation对象列表  
        history = [conversation.Conversation(**conv_dict) for conv_dict in conversation_dicts]
        if history == None:
            history = []
    else:
        history =[]
    return history

# 将用户数据保存到JSON文件
def save_users_to_json(users, file_path):
    with open(file_path, 'w') as file:
        json.dump([user.to_dict() for user in users.values()], file, default=default_converter)  


# 根据UID获取用户数据
def get_user_by_uid(users, uid):
    return users.get(uid)

def choice_user(users, username, password):
    # 遍历用户数据，查找匹配的账号  
    for user in users.values():
        if user.username == username:
            # 如果找到匹配的账号，比较密码是否匹配  
            if user.password == password:
                return user  # 账号密码正确
            else:
                return -2
        else:
            return -1
    return -3
# 添加用户数据  
def add_user(users, user):
    if user.uid not in users:
        users[user.uid] = user
        print(f"User {user.uid} added successfully.")
    else:
        print(f"User {user.uid} already exists.")

# 函数用于检查用户名是否已注册  
def is_registered(users,register):  
    # 遍历用户数据字典，检查用户名是否已存在  
    for user in users.values():  
        if user.username == register.username:
            return False  # 用户名已注册
    add_user(users,register)
    save_users_to_json(users,FILE_PATH)
    return True  # 用户名注册成功
# 修改用户数据  
def update_user(users, uid, new_user_data):
    if uid in users:  
        users[uid] = User(uid, **new_user_data)
        print(f"User {uid} updated successfully.")
    else:
        print(f"User {uid} does not exist.")
  
# 删除用户数据  
def delete_user(users, uid):
    if uid in users:  
        del users[uid]  
        print(f"User {uid} deleted successfully.")
    else:
        print(f"User {uid} does not exist.")
