<html>

# Guka智能桌面宠物

## GitHub

链接：https://github.com/xycdaimi/Guka

## 模型文件

### chatglm

   选择一种模型放到server/model文件夹里，再将模型调用的路径改一下

#### chatglm-6b

链接：https://pan.baidu.com/s/1onhN8IvCDShlvITvNmtCXA 
提取码：guka 
--来自百度网盘超级会员V1的分享

#### chatglm2-6b

链接：https://pan.baidu.com/s/1ZQf9OAd9_djecA1qdPpYkg 
提取码：guka 
--来自百度网盘超级会员V2的分享

### so-vits-svc

   checkpoint_best_legacy_500.pt和rmvpe.pt放入server/pretrain文件夹里，model放入server/pretrain/nsf_hifigan/里，其他的放入server/model/so-vits-svc/里

链接：https://pan.baidu.com/s/14mKvQWALmA5S8MVWbDdojg 
提取码：guka 
--来自百度网盘超级会员V2的分享

### whisper

   放到server/model/whisper/里

链接：https://pan.baidu.com/s/10pHoMNvRdy8WM_wCupop8Q 
提取码：guka 
--来自百度网盘超级会员V1的分享

## 关键文档（必须提供）

1. 任务书： docs/任务书.md
2. 设计文档： docs/设计文档.md (这个可以根据实际情况拆分为多份，如果有多份，则可以列出清单)
3. 项目介绍：docs/项目介绍.md (用于答辩时展示，具体内容见模板)
4. 演示视频：不超过10分钟的演示视频文件。
5. 跟踪调试记录：
   * docs/bugfix: 文档1、文档2..... （每个人至少3篇，说明书写者名称）

## 运行说明

### 客户端

#### 环境配置

1. 安装客户端文件夹client下的requirements.txt
   pip install -r requirements.txt
2. 在运行服务端后可运行main.py文件，客户端默认在windows系统中运行

### 服务端

#### 环境配置

1. 安装miniconda或anaconda，这里以miniconda为例。链接：http://t.csdnimg.cn/O1Thc
2. 安装cuda和cudnn。
3. 从网盘里下载好模型文件放入对应的文件夹。注意：请根据服务器的显存大小选择相应的模型文件，这里以12G显存为例，使用chatglm2-6b-int4和medium.pt模型和keli50000.pt
4. 安装服务端文件夹server下的requirements.txt
   pip install -r requirements.txt
5. 运行main.py文件，可放入后台。注：运行后只有关机或杀死进程才能终止程序。

### 部署运行

#### 局域网或公网ip部署

   客户端和服务端main.py里设置ip和端口为同一个，有公网ip就设置成公网ip，局域网就设置成服务器对应的ip地址

#### 无公网ip部署内网穿透部署

   无公网ip又想使用公网访问，安装cpolar进行内网穿透，使用：nc -zv 穿透后的tcp隧道域名 端口，可以判断隧道是否连接成功且获得该隧道公网的具体ip地址，服务端main.py设置ip：127.0.0.1，端口号设置成穿透映射的端口，客户端main.py设置隧道的ip地址和端口

## 代码说明

部分目录结构如下：

~~~
guka  
├─code                        应用代码目录
│  ├─client                   客户端目录
│  │  ├─comunication          通信模块
│  │  │  ├─comunication.py    通信模块文件
│  │  │  └─__init__.py        文件夹配置文件
│  │  │
│  │  ├─log                   日志模块
│  │  │  ├─log.py             日志模块文件
│  │  │  └─__init__.py        文件夹配置文件
│  │  │
│  │  ├─pet                   宠物模块
│  │  │  ├─pet.py             宠物模块文件
│  │  │  ├─windowsAPi.py      系统接口调用文件
│  │  │  │
│  │  │  ├─click              点击目录
│  │  │  │  └─click.gif       点击动画
│  │  │  │
│  │  │  ├─icon               图标目录
│  │  │  │  ├─guka.ico        图标文件
│  │  │  │  └─icon.png        托盘图标文件
│  │  │  │
│  │  │  ├─direction          移动目录
│  │  │  │  ├─left.gif        左移动画
│  │  │  │  └─right.gif       右移动画
│  │  │  │
│  │  │  ├─normal             待机目录
│  │  │  │  ├─eye.gif         眨眼动画
│  │  │  │  └─tou.gif         摇头动画
│  │  │  │
│  │  │  └─__init__.py        文件夹配置文件
│  │  │
│  │  ├─main.py               执行文件
│  │  ├─guka.log              应用日志文件
│  │  └─requirements.txt      配置安装文件
│  │
│  └─server        模块目录
│     ├─comunication          通信模块
│     │  ├─comunication.py    通信模块文件
│     │  └─__init__.py        文件夹配置文件
│     │
│     ├─tts                   文字转语音模块
│     │  ├─tts.py             文字转语音模块文件
│     │  └─__init__.py        文件夹配置文件
│     │
│     ├─log                   日志模块
│     │  ├─log.py             日志模块文件
│     │  └─__init__.py        文件夹配置文件
│     │
│     ├─speak                 语音模块
│     │  ├─speak.py           语音模块文件
│     │  └─__init__.py        文件夹配置文件
│     │
│     ├─chatglm               大语言模块
│     │  ├─chatglm.py         大语言模块文件
│     │  └─__init__.py        文件夹配置文件
│     │
│     ├─history_chat.npy      对话历史文件(没有时运行程序将自动生成)
│     ├─server.log            应用日志文件
│     ├─requirements.txt      配置安装文件
│     ├─model                 模型目录
│     │  ├─chatGLM-int4       大语言量化int4模型目录
│     │  ├─chatGLM-int8       大语言量化int8模型目录
│     │  └─whisper            语言识别模型目录
│     └─main.py               执行文件
│
├─docs                        文档目录
│  ├─任务书.md                任务计划文件
│  ├─设计文档.md              应用设计文件
│  ├─bugfix                   跟踪调试记录
│  │  ├─212106052谢宇宸.log
│  │  ├─212106038罗航.log
│  │  └─212106050伍定楠.log
│  ├─demo.eap                 用例图文件
│  ├─演示视频.mp4              项目演示视频
│  └─项目介绍.md               项目介绍文件
│
├─README.md                   说明文档
~~~

## 小组分工说明

罗航：负责用whisper模型、用so-vits-svc实现语音克隆

谢宇宸：负责使用chatglm模型实现宠物聊天语言互动功能,客户端和服务器的通信传输，edge-tts文字转语音，项目代码的整合，各部分的衔接。

伍定楠：负责智能桌面宠物的实现，例如：调用系统接口完成用户需求、鼠标互动，宠物动画的播放，用户辅助功能等等
</html>