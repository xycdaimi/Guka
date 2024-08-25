import log
import socket
import struct
import pyaudio
import wave
import json
logger = log.get_log(__name__)

STRING = 1
AUDIO = 2
JSON = 3
FLAG = 4
LONG_AUDIO = 5
class Com(object):
    def __init__(self, host, port):
        try:
            self.CHUNK = 1024
            self.FORMAT = pyaudio.paInt16
            self.CHANNELS = 1
            self.RATE = 44100
            self.RECORD_SECONDS = 5
            self.WAVE_OUTPUT_FILENAME = 'recording.wav'
            self.wf = None
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((host, port))
            self.s.listen()
            self.p = pyaudio.PyAudio()
            self.frames = []
        except Exception as e:
            logger.error(e)
    
    def send_data(self, conn, data_type, data):
        # 发送数据类型（这里用简单的整数表示）
        conn.sendall(struct.pack('!I', data_type))
        if data_type == STRING or data_type == FLAG:
            data = data.encode('utf-8')
        elif data_type == JSON:
            data = json.dumps(data).encode('utf-8')
        # 发送数据长度
        data_length = len(data)
        if data_type == LONG_AUDIO:
            data_length *= 4
        print("类型："+str(data_type)+" length"+str(data_length))
        conn.sendall(struct.pack('!I', data_length))
        # 发送数据本身
        conn.sendall(data)
    def receive_all(self, conn, size):  
        data = b''  
        while len(data) < size:  
            packet = conn.recv(size - len(data))  
            if not packet:  
                raise EOFError("Connection closed unexpectedly")  
            data += packet  
        return data
    def receive_data(self, conn):
        # 接收数据类型
        data_type_bytes = self.receive_all(conn, 4)
        data_type = struct.unpack('!I', data_type_bytes)[0]
        # 接收数据长度
        data_length_bytes = self.receive_all(conn, 4)
        data_length = struct.unpack('!I', data_length_bytes)[0]
        # 接收数据本身
        data = conn.recv(data_length)
        if data_type == STRING or data_type == FLAG:
            data = data.decode('utf-8')
        elif data_type == JSON:
            data = json.loads(data.decode('utf-8'))
        return data_type, data
        
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
    def close_down(self):
        try:
            self.p.terminate()
            self.s.close()
            logger.info('连接关闭')
        except Exception as e:
            logger.error(e)

