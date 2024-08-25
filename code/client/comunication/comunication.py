import json
import struct
import wave

import keyboard
import numpy

import log
import pyaudio
import socket
logger = log.get_log(__name__)

STRING = 1
AUDIO = 2
JSON = 3
FLAG = 4
LONG_AUDIO = 5
class Com(object):
    def __init__(self, host, port, chunk=1024,
                 for_mat=pyaudio.paInt16,
                 channels=1, rate=44100):
        self.wf = None
        try:
            self.ser_back = ''
            self.CHUNK = chunk
            self.FORMAT = for_mat
            self.CHANNELS = channels
            self.RATE = rate
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
            self.p = pyaudio.PyAudio()
            self.out_stream = self.p.open(format=pyaudio.paFloat32,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      output=True,
                                      frames_per_buffer=self.CHUNK*10)
            self.in_stream = self.p.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK)
            logger.info('通讯模块开启')
        except Exception as e:
            logger.error(e)

    def wav_rw(self, rw='wb', output='recording.wav'):
        self.wf = wave.open(output, rw)
        self.wf.setnchannels(self.CHANNELS)
        self.wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wf.setframerate(self.RATE)

    def wav_close(self):
        self.wf.close()

    def accept_data(self, data):
        try:
            self.frames = []
            self.frames.append(data)
            self.wf.writeframes(b''.join(self.frames))

        except Exception as e:
            logger.error(e)

    def receive_all(self, size):
        data = b''
        while len(data) < size:
            packet = self.s.recv(size - len(data))
            if not packet:
                raise EOFError("Connection closed unexpectedly")
            data += packet
        return data

    def receive_data(self):
        # 接收数据类型
        data_type_bytes = self.receive_all(4)
        data_type = struct.unpack('!I', data_type_bytes)[0]
        # 接收数据长度
        data_length_bytes = self.receive_all(4)
        data_length = struct.unpack('!I', data_length_bytes)[0]
        print("类型："+str(data_type)+"长度："+str(data_length))
        # 接收数据本身
        data = self.receive_all(data_length)
        if data_type == STRING or data_type == FLAG:
            data = data.decode('utf-8')
        elif data_type == JSON:
            data = json.loads(data.decode('utf-8'))
        # else:
        #     print(len(data))
        #     unpacked_data = struct.unpack('f' * (len(data)//4), data)
        #
        #     # 将解包后的数据转换为 NumPy 数组
        #     log_data = numpy.array(unpacked_data, dtype=numpy.float32)
        #     print(log_data)
        return data_type, data

    def send_data(self, data_type, data):
        # 发送数据类型（这里用简单的整数表示）
        self.s.sendall(struct.pack('!I', data_type))
        if data_type == STRING or data_type == FLAG:
            data = data.encode('utf-8')
        elif data_type == JSON:
            data = json.dumps(data).encode('utf-8')
        # 发送数据长度
        data_length = len(data)
        if data_type == LONG_AUDIO:
            data_length *= 4
        self.s.sendall(struct.pack('!I', data_length))
        # 发送数据本身
        self.s.sendall(data)

    def close_down(self):
        try:
            self.in_stream.stop_stream()
            self.in_stream.close()
            self.out_stream.stop_stream()
            self.out_stream.close()
            self.p.terminate()
            self.s.close()
            logger.info('连接关闭')
        except Exception as e:
            logger.error(e)

    def write_audio(self, data):
        self.out_stream.write(data)

    def read_audio(self):
        try:
            while True:
                if keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                    data = self.in_stream.read(1024)
                    self.send_data(AUDIO, data)
                else:
                    self.send_data(STRING, "end")
                    break
            data_type, data = self.receive_data()
            if isinstance(data, str):
                return data
            else:
                return ""
        except Exception as e:
            logger.error(e)
