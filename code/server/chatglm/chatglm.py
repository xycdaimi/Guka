import log
logger = log.get_log(__name__)
import torch
import os
import numpy as np
from transformers import AutoTokenizer, AutoModel
#语言模型类
class ChatGLM(object):
    # Load tokenizer and PyTorch weights form the Hub
    def __init__(self,file_path):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("model/chatGLM-int4", trust_remote_code=True)
            is_gpu_available = torch.cuda.is_available()
            if is_gpu_available:
                self.model = AutoModel.from_pretrained("model/chatGLM-int4", trust_remote_code=True).half().cuda()
                logger.info('使用GPU')
            else:
                self.model = AutoModel.from_pretrained("model/chatGLM-int4", trust_remote_code=True).cpu().float()
                logger.info('使用CPU')
            self.model = self.model.eval()
            start = [(
                '你是一只会说话、了解各种知识的宠物，可以自由回答问题，像人类一样思考和表达。你需要辅助我完成各项工作，陪我聊天和学习，给我带来欢声笑语，给予我精神上的寄托。',
                '好的主人'),('你要记住，你的名字是咕卡，当我询问你的名字时，你要回复我。','好的主人，我的名字是咕卡，我会帮助您完成各种工作。'),('咕卡！','我在的，主人，有什么需要帮助的吗？'),
                ('你是？', '我的名字是咕卡，主人。'),('你好呀','您好，主人。')]
            self.history = start
            if os.path.exists(file_path):
                # 载入对话历史
                self.history = np.load(file_path, allow_pickle=True).tolist()
                logger.info('历史对话加载完成')
            else:
                np.save('history_chat', self.history)
                logger.info('历史对话不存在，对话已重新保存')
            logger.info('对话模型初始化完成')
        except Exception as e:
            logger.error(e)
    def forward(self, user_input):
        try:
            response, self.history = self.model.chat(self.tokenizer,user_input, history=self.history)
            self.del_history()
            return response
        except Exception as e:
            logger.error(e)

    def del_history(self):
        while len(self.history) > 200:
            self.history.pop(5)
