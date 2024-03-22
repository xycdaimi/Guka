import log
logger = log.get_log(__name__)
import whisper
from zhconv import convert
class Yuyin(object):
    def __init__(self, file_path):
        try:
            self.model = whisper.load_model(file_path)
            logger.info('语音识别模型初始化完成')
        except Exception as e:
            logger.error(e)
    def forward(self, user_input):
        try:
            result = self.model.transcribe(user_input, language='Chinese')
            back = convert(result["text"], 'zh-cn')
            return back
        except Exception as e:
            logger.error(e)
