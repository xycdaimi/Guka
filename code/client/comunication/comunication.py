import struct
import log

logger = log.get_log(__name__)
import pyaudio
import socket
import keyboard


class Com(object):
    def __init__(self, host, port, chunk=1024,
                 for_mat=pyaudio.paInt16,
                 channels=1, rate=44100):
        try:
            self.ser_back = ''
            self.CHUNK = chunk
            self.FORMAT = for_mat
            self.CHANNELS = channels
            self.RATE = rate
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK)
            self.stream2 = self.p.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      output=True,
                                      frames_per_buffer=self.CHUNK*2)
            logger.info('通讯模块开启')
        except Exception as e:
            logger.error(e)

    def send_data(self, data):
        try:
            self.s.sendall(data)
        except Exception as e:
            logger.error(e)

    def receive_data(self):
        # 接收数据类型
        data_type = struct.unpack('!I', self.s.recv(4))[0]
        # 接收数据长度
        data_length = struct.unpack('!I', self.s.recv(4))[0]
        # 接收数据本身
        data = self.s.recv(data_length)
        if data_type == 1:
            data = data.decode()
        return data_type, data

    def close_down(self):
        try:
            self.stream2.stop_stream()
            self.stream2.close()
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            self.s.close()
            logger.info('连接关闭')
        except Exception as e:
            logger.error(e)

    def write_audio(self, audio_guka):
        try:
            self.stream2.write(audio_guka)
        except Exception as e:
            logger.error()

    def run_audio(self):
        try:
            while True:
                if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                    data = self.stream.read(self.CHUNK)
                    self.send_data(data)
                else:
                    break
            self.send_data(b'end')
            logger.info("Recording stopped.")
        except Exception as e:
            logger.error()

    def run_str(self, text, flag=b'zf'):
        try:
            self.send_data(flag)
            self.s.sendall(text.encode())
            if flag == b'zf':
                data_type, data = self.receive_data()
                self.ser_back = data
            elif flag == b'dq':
                self.ser_back = text
            return self.ser_back
        except Exception as e:
            logger.error(e)
