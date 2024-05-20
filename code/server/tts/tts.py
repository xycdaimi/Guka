import asyncio
import edge_tts
import simpleaudio

class TTSController(object):

    __voice__ = None
    __output_file__ = None
    __loop__ = None

    def __init__(self, output_file = "output.wav"):
        output_file = "./raw/"+output_file
        self.__voice__ = "zh-CN-XiaoyiNeural"
        self.__output_file__ = output_file
        self.__loop__ = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(self.__loop__)

    async def amain(self,text):
        """Main function"""
        communicate = edge_tts.Communicate(text, self.__voice__)
        await communicate.save(self.__output_file__)
    
    def textToaudio(self, text):
        try:
            self.__loop__.run_until_complete(self.amain(text))
        finally:
            self.__loop__.close()
    
    def speaking(self, text):
        try:
            self.__loop__.run_until_complete(self.amain(text))
        finally:
            self.__loop__.close()
        # 播放音频
        wave_obj = simpleaudio.WaveObject.from_wave_file(self.__output_file__)
        play_obj = wave_obj.play()
        play_obj.wait_done()

#if __name__ == "__main__":
#    tts_controller = TTSController()
#    tts_controller.speaking("你好,这是一个语音合成功能的测试")
