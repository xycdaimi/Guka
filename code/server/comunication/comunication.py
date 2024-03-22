import log
logger = log.get_log(__name__)
import pyaudio
import wave
import socket
import struct

class Com(object):
    def __init__(self, host, port, wave_out_put_filename='recording.wav', record_seconds=5, chunk=1024,
                 for_mat=pyaudio.paInt16,
                 channels=1, rate=44100):
        try:
            self.CHUNK = chunk
            self.FORMAT = for_mat
            self.CHANNELS = channels
            self.RATE = rate
            self.RECORD_SECONDS = record_seconds
            self.WAVE_OUTPUT_FILENAME = wave_out_put_filename
            self.wf = None
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((host, port))
            self.s.listen()
            #(self.RECORD_SECONDS)
            #self.conn, self.addr = None
            #self.s.accept()
            self.p = pyaudio.PyAudio()
            self.frames = []
            logger.info('语音监听开启')
        except Exception as e:
            logger.error(e)
    
    def send_data(self, conn, data_type, data):
        # 发送数据类型（这里用简单的整数表示）
        conn.sendall(struct.pack('!I', data_type))
        # 发送数据长度
        data_length = len(data)
        conn.sendall(struct.pack('!I', data_length))
        # 发送数据本身
        conn.sendall(data)

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
            #self.conn.close()
            self.s.close()
            logger.info('连接关闭')
        except Exception as e:
            logger.error(e)

