import os
from openai import OpenAI
import pyaudio
import wave
import whisperx
import torch
import requests
import gc
import json
from dotenv import load_dotenv

def fun_play_wav(filename):
    print("播放音檔")
    chunk = 1024
    audio_path = os.path.join(assert_directory, filename)
    wf = wave.open(audio_path, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()
    
def fun_record(sec: int):
    chunk = 1024                     # 記錄聲音的樣本區塊大小
    sample_format = pyaudio.paInt16 # 樣本格式，可使用 paFloat32、paInt32、paInt24、paInt16、paInt8、paUInt8、paCustomFormat
    channels = 1                     # 聲道數量
    fs = 44100# 取樣頻率，常見值為 44100 ( CD )、48000 ( DVD )、22050、24000、12000 和 11025。
    seconds = sec                    # 錄音秒數
    filename = "whisperX.wav"            # 錄音檔名
    p = pyaudio.PyAudio()            # 建立 pyaudio 物件
    print("開始錄音...")
    stream = p.open(format=sample_format, channels=channels,rate=fs, frames_per_buffer=chunk, input=True)
    frames = []                      # 建立聲音串列
    for _ in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)          
    stream.stop_stream()             # 將聲音記錄到串列中
    stream.close()                   # 停止錄音
    p.terminate()                    # 關閉串流
    print('錄音結束...')
    wf = wave.open(filename, 'wb')   # 開啟聲音記錄檔
    wf.setnchannels(channels)        # 設定聲道
    wf.setsampwidth(p.get_sample_size(sample_format))  # 設定格式
    wf.setframerate(fs)              # 設定取樣頻率
    wf.writeframes(b''.join(frames))  # 存檔
    wf.close()

def fun_whisperX():
    print("執行 WhisperX")
    print("辨識中...")
    audio_path = os.path.join(assert_directory, "whisperX.wav")
    result = modelx.transcribe(audio_path)
    print(f"辨識: \n {result['segments'][0]['text']}")
    return result["segments"][0]["text"]

def fun_llm(messages):
    print("執行 LLM")
    # 讀取 prompt.txt 檔案
    with open(os.path.join(assert_directory, "prompt.txt"), "r", encoding="utf-8") as f:
        prompt = f.read()
    history = [
        {
            "role": "system", 
            "content": prompt
        },{
            "role": "user",
            "content": messages
        }
    ]
    completion = client.chat.completions.create(model="llama3-8b-8192", messages=history, temperature=0.7,)
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def fun_tts(text):
    print("執行 TTS")
    refer_wav_path = tts_path
    prompt_text = tts_text
    prompt_language = "中文"
    text_language = "中文"
    url = f"{tts_api}/?refer_wav_path={refer_wav_path}&prompt_text={prompt_text}&prompt_language={prompt_language}&text={text}&text_language={text_language}"
    response = requests.get(url)
    # response輸出為音檔
    with open(os.path.join(assert_directory, "SoVITS_LLM.wav"), "wb") as f:
        f.write(response.content)

def fun_irremote(value):
    print("執行 IR Remote")
    irremote_url = f"{web_api}/irremote"
    log_url = f"{web_api}/log"
    body = json.dumps(value)
    headers = {"Content-Type": "application/json"}
    irremote_res = requests.post(irremote_url, headers=headers, data=body)
    log_res = requests.post(log_url, headers=headers, data=body)
    print(irremote_res.text)
    print(log_res.text)

if __name__ == '__main__':
    try:
        # 初始化
        # 載入環境變數
        load_dotenv(".voice.env")
        groq_api_url = os.getenv("GROQ_API_URL")
        groq_api_key = os.getenv("GROQ_API_KEY")
        wihisperx_model = os.getenv("WHISPERX_MODEL")
        web_api = os.getenv("WEB_API")
        tts_api = os.getenv("TTS_API")
        tts_path = os.getenv("TTS_PATH")
        tts_text = os.getenv("TTS_TEXT")

        # 取得當前目錄
        assert_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        # 初始化 LLM
        client = OpenAI(base_url=groq_api_url, api_key=groq_api_key)
        # 載入模型 (WhisperX)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        modelx = whisperx.load_model(wihisperx_model, device, compute_type="int8" if device == "cpu" else None)

        while True:
            try:
                # 呼叫 def_record() 錄音
                fun_record(3)
                # 呼叫 def_whisperX() 辨識
                detect = fun_whisperX()
                # 判斷是否有偵測到 "Hey" 或 "OK" 和 "Whisper"
                if ('Hey' in detect or 'OK' in detect) and ('Whisper' in detect or 'whisper' in detect):
                    fun_play_wav("hello.wav")
                    print('哈囉，請問有什麼需求嗎?')
                    # 播放提示音
                    fun_play_wav("提示音.wav")
                    # 呼叫 def_record() 錄音
                    fun_record(5)
                    # 呼叫 def_whisperX() 辨識
                    text = fun_whisperX()
                    # 判斷是否有偵測到 "冷氣" 或 "電風扇" 或 "電視" 或 "查詢"
                    if '冷氣' in text or '電風扇' in text or '電視' in text or '查詢' in text:
                        # 呼叫 def_llm() 生成回答
                        llm_res = fun_llm(text)
                        # 呼叫 def_tts() 生成音檔
                        fun_tts(llm_res)
                        value={}
                        if "查詢" in text:
                            if "控制" in text:
                                ans="好的，最近一次的控制紀錄是2023/09/25"
                            elif "心率" in text or "心律" in text:
                                ans="好的，最近一次的心率紀錄為70"
                            elif "睡眠" in text:
                                ans="好的，最近一次的睡眠時間為6小時30分鐘"
                            elif "步數" in text:
                                ans="好的，最近一天的步數為7000步"
                        if '冷氣' in text:
                            value['devices']='aircon'
                            value['name'] = '大金冷氣'
                            if '上下' in text and ('擺動' in text or '搖擺' in text):
                                value['signal']='H-swing'
                            elif '左右' in text and ('擺動' in text or '搖擺' in text):
                                value['signal']='V-swing'
                            elif '開' in text and '冷氣' in text:
                                value['signal']='on'
                            elif '關' in text and '冷氣' in text:
                                value['signal']='off'
                        if '電風扇' in text:
                            value['devices'] = 'fan'
                            value['name'] = '電風扇'
                            if '弱風' in text:
                                value['signal'] = 'L-wind'
                            elif '強風' in text:
                                value['signal'] = 'H-wind'
                            if '上下' in text and ('擺動' in text or '搖擺' in text):
                                value['signal']='H-swing'
                            elif '左右' in text and ('擺動' in text or '搖擺' in text):
                                value['signal']='V-swing'
                            elif '開' in text and '風扇' in text:
                                value['signal'] = 'on'
                            elif '關' in text and '風扇' in text:
                                value['signal'] = 'off'
                        if '電視' in text:
                            value['devices'] = 'tv'
                            value['name'] = '電視'
                            if '開' in text and '電視' in text:
                                value['signal'] = 'on'
                            elif '關' in text and '電視' in text:
                                value['signal'] = 'off'
                            elif '轉' in text and '台' in text:
                                value['signal'] = text[-3:-1]
                            elif '確定' in text:
                                value['signal'] = 'ok'
                        # 呼叫 def_irremote() 控制裝置
                        # fun_irremote(value)
                        print(value)
                        print(text)
                        # 呼叫 def_play_wav() 播放音檔
                        fun_play_wav("SoVITS_LLM.wav")
                    else:
                        print('抱歉，我聽不懂你的需求')
                        fun_play_wav("sorry.wav")
            except KeyboardInterrupt:
                print("Ctrl+C")
                break
            except IndexError:
                print("未檢測到語音")
    except Exception as e:
        print(f"初始化時發生錯誤: {e}")
    # finally:
    #     # 刪除模型
    #     del modelx
    #     # 釋放記憶體
    #     gc.collect()
    #     print("程式結束")