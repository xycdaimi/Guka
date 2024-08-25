import logging
import soundfile
import numpy as np
from comunication.comunication import Com
from inference import infer_tool
from inference.infer_tool import Svc
from inference.infer_tool import RealTimeVC
from spkmix import spk_mix_map

logging.getLogger('numba').setLevel(logging.WARNING)
chunks_dict = infer_tool.read_temp("inference/chunks_temp.json")


class Phonetic_cloning(object):
    def __init__(self, model_path="model/so-vits-svc/keli50000.pth", spk_list=['keli'], device=None, trans=[0],
                 config_path="model/so-vits-svc/config.json", clip=0):
        # wav文件名列表，放在raw文件夹下
        self.clean_names = ['zh.wav']
        # 音高调整，支持正负（半音）
        self.trans = trans
        # 合成目标说话人名称
        self.spk_list = spk_list
        # 音频强制切片，默认0为自动切片，单位为秒/s
        self.clip = clip
        # 模型路径
        self.model_path = model_path
        # 配置文件路径
        self.config_path = config_path
        # 推理设备，None则为自动选择cpu和gpu
        self.device = device

        # 默认-40，嘈杂的音频可以-30，干声保留呼吸可以-50
        self.slice_db = -40
        # 音频输出格式
        self.wav_format = 'wav'
        # 语音转换自动预测音高，转换歌声时不要打开这个会严重跑调
        self.auto_predict_f0 = True
        # 聚类方案或特征检索占比，范围0-1，若没有训练聚类模型或特征检索则默认0即可
        self.cluster_infer_ratio = 0.5
        # 噪音级别，会影响咬字和音质，较为玄学
        self.noice_scale = 0.4
        # 推理音频pad秒数，由于未知原因开头结尾会有异响，pad一小段静音段后就不会出现
        self.pad_seconds = 0.5
        # 两段音频切片的交叉淡入长度，如果强制切片后出现人声不连贯可调整该数值，如果连贯建议采用默认值0，单位为秒
        self.lg = 0
        # 自动音频切片后，需要舍弃每段切片的头尾。该参数设置交叉长度保留的比例，范围0-1,左开右闭
        self.lgr = 0.75
        # 选择F0预测器,可选择crepe,pm,dio,harvest,rmvpe,fcpe默认为pm(注意：crepe为原F0使用均值滤波器)
        self.f0p = "rmvpe"
        # 是否使用NSF_HIFIGAN增强器,该选项对部分训练集少的模型有一定的音质增强效果，但是对训练好的模型有反面效果，默认关闭
        self.enhance = False
        # 使增强器适应更高的音域(单位为半音数)|默认为0
        self.enhancer_adaptive_key = 0
        # F0过滤阈值，只有使用crepe时有效. 数值范围从0-1. 降低该值可减少跑调概率，但会增加哑音
        self.cr_threshold = 0.05
        # 扩散模型路径
        self.diffusion_model_path = "model/so-vits-svc/model_20000.pt"
        # 扩散模型配置文件路径
        self.diffusion_config_path = "model/so-vits-svc/config.yaml"
        # 扩散步数，越大越接近扩散模型的结果，默认100
        self.k_step = 100
        # 纯扩散模式，该模式不会加载sovits模型，以扩散模型推理
        self.only_diffusion = False
        # 是否使用浅层扩散，使用后可解决一部分电音问题，默认关闭，该选项打开时，NSF_HIFIGAN增强器将会被禁止
        self.shallow_diffusion = True
        # 是否使用角色融合
        self.use_spk_mix = False
        # 二次编码，浅扩散前会对原始音频进行二次编码，玄学选项，有时候效果好，有时候效果差
        self.second_encoding = False
        # 输入源响度包络替换输出响度包络融合比例，越靠近1越使用输出响度包络
        self.loudness_envelope_adjustment = 1

        # 聚类模型或特征检索索引路径，留空则自动设为各方案模型的默认路径，如果没有训练聚类或特征检索则随便填
        self.cluster_model_path = ""
        # 是否使用特征检索，如果使用聚类模型将被禁用，且cm与cr参数将会变成特征检索的索引路径与混合比例
        self.feature_retrieval = True
        if self.cluster_infer_ratio != 0:
            if self.cluster_model_path == "":
                if self.feature_retrieval:  # 若指定了占比但没有指定模型路径，则按是否使用特征检索分配默认的模型路径
                    self.cluster_model_path = "model/so-vits-svc/feature_and_index.pkl"
                else:
                    self.cluster_model_path = "model/so-vits-svc/kmeans_10000.pt"
        else:  # 若未指定占比，则无论是否指定模型路径，都将其置空以避免之后的模型加载
            self.cluster_model_path = ""

        self.svc_model = Svc(self.model_path,
                             self.config_path,
                             self.device,
                             self.cluster_model_path,
                             self.enhance,
                             self.diffusion_model_path,
                             self.diffusion_config_path,
                             self.shallow_diffusion,
                             self.only_diffusion,
                             self.use_spk_mix,
                             self.feature_retrieval)

    def forward1(self, clean_names=["output.wav"], name='output'):
        infer_tool.mkdir(["raw", "results"])

        if len(spk_mix_map) <= 1:
            self.use_spk_mix = False
        if self.use_spk_mix:
            self.spk_list = [spk_mix_map]

        infer_tool.fill_a_to_b(self.trans, clean_names)
        for clean_name, tran in zip(clean_names, self.trans):
            raw_audio_path = f"raw/{clean_name}"
            if "." not in raw_audio_path:
                raw_audio_path += ".wav"
            infer_tool.format_wav(raw_audio_path)
            for spk in self.spk_list:
                kwarg = {
                    "raw_audio_path": raw_audio_path,
                    "spk": spk,
                    "tran": tran,
                    "slice_db": self.slice_db,
                    "cluster_infer_ratio": self.cluster_infer_ratio,
                    "auto_predict_f0": self.auto_predict_f0,
                    "noice_scale": self.noice_scale,
                    "pad_seconds": self.pad_seconds,
                    "clip_seconds": self.clip,
                    "lg_num": self.lg,
                    "lgr_num": self.lgr,
                    "f0_predictor": self.f0p,
                    "enhancer_adaptive_key": self.enhancer_adaptive_key,
                    "cr_threshold": self.cr_threshold,
                    "k_step": self.k_step,
                    "use_spk_mix": self.use_spk_mix,
                    "second_encoding": self.second_encoding,
                    "loudness_envelope_adjustment": self.loudness_envelope_adjustment
                }
                audio = self.svc_model.slice_inference(**kwarg)
                key = "auto" if self.auto_predict_f0 else f"{self.tran}key"
                cluster_name = "" if self.cluster_infer_ratio == 0 else f"_{self.cluster_infer_ratio}"
                isdiffusion = "sovits"
                if self.shallow_diffusion:
                    isdiffusion = "sovdiff"
                if self.only_diffusion:
                    isdiffusion = "diff"
                if self.use_spk_mix:
                    spk = "spk_mix"
                res_path = f'results/{name}.{self.wav_format}'
                soundfile.write(res_path, audio, self.svc_model.target_sample, format=self.wav_format)

                '''
                samplerate = 44100
                duration = 1  # 秒  
                t = np.linspace(0, duration, int(samplerate * duration), False)
                data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)  # 乘以32767以将浮点数转换为16位整数的范围  

                # 将NumPy数组转换为字节流（bytes），因为PyAudio需要这种格式  
                # 注意：对于多声道数据，你需要按照声道顺序组织字节流  
                bytes_data = data.tobytes()
                '''

    def forward2(self, clean_names=["output.wav"]):
        infer_tool.mkdir(["raw", "results"])

        if len(spk_mix_map) <= 1:
            self.use_spk_mix = False
        if self.use_spk_mix:
            self.spk_list = [spk_mix_map]

        infer_tool.fill_a_to_b(self.trans, clean_names)
        for clean_name, tran in zip(clean_names, self.trans):
            raw_audio_path = f"raw/{clean_name}"
            if "." not in raw_audio_path:
                raw_audio_path += ".wav"
            infer_tool.format_wav(raw_audio_path)
            for spk in self.spk_list:
                realTime = RealTimeVC(raw_audio_path)
                print(realTime.audio.shape[0])
                # for...
                # while(realTime.length > realTime.chunk_len * realTime.block_number):
                ret = realTime.process(self.svc_model, spk, 0, auto_predict_f0=True)
                t = np.linspace(0, 1, int(ret.shape[0]), endpoint=False)
                res = np.sin(2 * np.pi * t) * ret
                res = res.astype(np.float32)
                return res
                # endfor...


def clear(self):
    self.svc_model.clear_empty()
