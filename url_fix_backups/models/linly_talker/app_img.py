import os

import gradio as gr
from ASR import WhisperASR
from configs import *
from LLM import LLM
from src.cost_time import calculate_time
from TFG import SadTalker
from TTS import EdgeTTS
from zhconv import convert

description = """<p style="text - align: center; font - weight: bold;">"""
    <span style="font - size: 28px;">Linly 智能对话系统 (Linly - Talker)</span>
    <br>
    <span style="font - size: 18px;" id="paper - info">
        [<a href="https://zhuanlan.zhihu.com / p/671006998" target="_blank">知乎</a>]
        [<a href="https://www.bilibili.com / video / BV1rN4y1a76x/" target="_blank">bilibili</a>]
        [<a href="https://github.com / Kedreamix / Linly - Talker" target="_blank">GitHub</a>]
        [<a herf="https://kedreamix.github.io/" target="_blank">个人主页</a>]
    </span>
    <br>
    <span > Linly - Talker 是一款智能 AI 对话系统，结合了大型语言模型 (LLMs) 与视觉模型，是一种新颖的人工智能交互方式。</span>
</p>
""""""

use_ref_video = False
ref_video = None
ref_info = "pose"
use_idle_mode = False
length_of_audio = 5

@calculate_time


def Asr(audio):
    try:
        question = asr.transcribe(audio)
        question = convert(question, "zh - cn")
    except Exception as e:
        print("ASR Error: ", e)
        question = "Gradio存在一些bug，麦克风模式有时候可能音频还未传入，请重新点击一下语音识别即可"
        gr.Warning(question)
    return question

@calculate_time


def TTS_response(
    text,
        voice,
        rate,
        volume,
        pitch,
# BRACKET_SURGEON: disabled
# ):
    try:
        tts.predict(text, voice, rate, volume, pitch, "answer.wav", "answer.vtt")
    except Exception:
        os.system(f'edge - tts --text "{text}" --voice {voice} --write - media answer.wav')
    return "answer.wav", "answer.vtt"

@calculate_time


def LLM_response(question,
    voice="zh - CN - XiaoxiaoNeural",
    rate = 0,
    volume = 0,
# BRACKET_SURGEON: disabled
#     pitch = 0):
    answer = llm.generate(question)
    print(answer)
    TTS_response(answer, voice, rate, volume, pitch)
    return "answer.wav", "answer.vtt", answer

@calculate_time


def Talker_response(
    text,
        voice,
        rate,
        volume,
        pitch,
        source_image,
        preprocess_type,
        is_still_mode,
        enhancer,
        batch_size,
        size_of_image,
        pose_style,
        facerender,
        exp_weight,
        blink_every,
        fps,
# BRACKET_SURGEON: disabled
# ):
    voice = "zh - CN - XiaoxiaoNeural" if voice not in tts.SUPPORTED_VOICE else voice
    driven_audio, driven_vtt, _ = LLM_response(text, voice, rate, volume, pitch)
    video = talker.test2(
        source_image,
            driven_audio,
            preprocess_type,
            is_still_mode,
            enhancer,
            batch_size,
            size_of_image,
            pose_style,
            facerender,
            exp_weight,
            use_ref_video,
            ref_video,
            ref_info,
            use_idle_mode,
            length_of_audio,
            blink_every,
            fps = fps,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    if driven_vtt:
        return video, driven_vtt
    else:
        return video


def main():

    with gr.Blocks(analytics_enabled = False, title="Linly - Talker") as inference:
        gr.HTML(description)
        with gr.Row(equal_height = False):
            with gr.Column(variant="panel"):
                with gr.Tabs(elem_id="sadtalker_source_image"):
                    with gr.TabItem("Source image"):
                        with gr.Row():
                            source_image = gr.Image(
                                label="Source image",
                                    type="filepath",
                                    elem_id="img2img_image",
                                    width = 512,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )

                with gr.Tabs(elem_id="question_audio"):
                    with gr.TabItem("对话"):
                        with gr.Column(variant="panel"):
                            question_audio = gr.Audio(
                                sources=["microphone", "upload"],
                                    type="filepath",
                                    label="语音对话",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )
                            input_text = gr.Textbox(
                                label="Input Text", lines = 3, info="文字对话"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            with gr.Accordion(
                                "Advanced Settings", open = False, visible = True
# BRACKET_SURGEON: disabled
#                             ) as parameter_article:
                                voice = gr.Dropdown(
                                    tts.SUPPORTED_VOICE,
                                        value="zh - CN - XiaoxiaoNeural",
                                        label="Voice",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                         )
                                rate = gr.Slider(
                                    minimum=-100,
                                        maximum = 100,
                                        value = 0,
                                        step = 1.0,
                                        label="Rate",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                         )
                                volume = gr.Slider(
                                    minimum = 0,
                                        maximum = 100,
                                        value = 100,
                                        step = 1,
                                        label="Volume",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                         )
                                pitch = gr.Slider(
                                    minimum=-100,
                                        maximum = 100,
                                        value = 0,
                                        step = 1,
                                        label="Pitch",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                         )

                            asr_text = gr.Button("语音识别（语音对话后点击）")
                            asr_text.click(
                                fn = Asr, inputs=[question_audio], outputs=[input_text]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

                # with gr.Tabs(elem_id="response_audio"):
                #     with gr.TabItem("语音选择"):
                #         with gr.Column(variant='panel'):
                #             voice = gr.Dropdown(VOICES,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     values='zh - CN - XiaoxiaoNeural')

                with gr.Tabs(elem_id="text_examples"):
                    gr.Markdown("## Text Examples")"
                    examples = [
                        ["应对压力最有效的方法是什么？"],
                            ["如何进行时间管理？"],
                            [
                            "为什么有些人选择使用纸质地图或寻求方向，而不是依赖GPS设备或智能手机应用程序？"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                            [
                            "近日，苹果公司起诉高通公司，状告其未按照相关合约进行合作，高通方面尚未回应。这句话中“其”指的是谁？"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                            [
                            "三年级同学种树80颗，四、五年级种的棵树比三年级种的2倍多14棵，三个年级共种树多少棵?"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                            ["撰写一篇交响乐音乐会评论，讨论乐团的表演和观众的整体体验。"],
                            [
                            "翻译成中文：Luck is a dividend of sweat. The more you sweat, the luckier you get."
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ]
                    gr.Examples(
                        examples = examples,
                            inputs=[input_text],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

            # driven_audio = 'answer.wav'
            with gr.Column(variant="panel"):
                with gr.Tabs(elem_id="sadtalker_checkbox"):
                    with gr.TabItem("Settings"):
                        with gr.Accordion("Advanced Settings", open = False):
                            gr.Markdown(
                                "SadTalker: need help? please visit our [[best practice page](https://github.com / OpenTalker / SadTalker / blob / main / docs / best_practice.md)] for more detials"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            with gr.Column(variant="panel"):
                                pass
                                # width = gr.Slider(minimum = 64,
    elem_id="img2img_width",
    maximum = 2048,
    step = 8,
    label="Manually Crop Width",
# BRACKET_SURGEON: disabled
#     value = 512) # img2img_width
                                # height = gr.Slider(minimum = 64,
    elem_id="img2img_height",
    maximum = 2048,
    step = 8,
    label="Manually Crop Height",
# BRACKET_SURGEON: disabled
#     value = 512) # img2img_width
                                with gr.Row():
                                    pose_style = gr.Slider(
                                        minimum = 0,
                                            maximum = 45,
                                            step = 1,
                                            label="Pose style",
                                            value = 0,
# BRACKET_SURGEON: disabled
#                                             )  #
                                    exp_weight = gr.Slider(
                                        minimum = 0,
                                            maximum = 3,
                                            step = 0.1,
                                            label="expression scale",
                                            value = 1,
# BRACKET_SURGEON: disabled
#                                             )  #
                                    blink_every = gr.Checkbox(
                                        label="use eye blink", value = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )

                                with gr.Row():
                                    size_of_image = gr.Radio(
                                        [256, 512],
                                            value = 256,
                                            label="face model resolution",
                                            info="use 256 / 512 model? 256 is faster",
# BRACKET_SURGEON: disabled
#                                             )  #
                                    preprocess_type = gr.Radio(
                                        [
                                            "crop",
                                                "resize",
                                                "full",
                                                "extcrop",
                                                "extfull",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                                 ],
                                            value="crop",
                                            label="preprocess",
                                            info="How to handle input image?",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                             )

                                with gr.Row():
                                    is_still_mode = gr.Checkbox(
                                        label="Still Mode (fewer head motion,"
# BRACKET_SURGEON: disabled
#     works with preprocess `full`)""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )
                                    facerender = gr.Radio(
                                        ["facevid2vid", "PIRender"],
                                            value="facevid2vid",
                                            label="facerender",
                                            info="which face render?",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                             )

                                with gr.Row():
                                    batch_size = gr.Slider(
                                        label="batch size in generation",
                                            step = 1,
                                            maximum = 10,
                                            value = 1,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                             )
                                    fps = gr.Slider(
                                        label="fps in generation",
                                            step = 1,
                                            maximum = 30,
                                            value = 20,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                             )
                                    enhancer = gr.Checkbox(
                                        label="GFPGAN as Face enhancer(slow)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )

                with gr.Tabs(elem_id="sadtalker_genearted"):
                    gen_video = gr.Video(
                        label="Generated video", format="mp4", scale = 0.8
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                submit = gr.Button(
                    "Generate", elem_id="sadtalker_generate", variant="primary"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            submit.click(
                fn = Talker_response,
                    inputs=[
                    input_text,
                        voice,
                        rate,
                        volume,
                        pitch,
                        source_image,
                        preprocess_type,
                        is_still_mode,
                        enhancer,
                        batch_size,
                        size_of_image,
                        pose_style,
                        facerender,
                        exp_weight,
                        blink_every,
                        fps,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    outputs=[gen_video],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        with gr.Row():
            examples = [
                ["examples / source_image / full_body_2.png", "crop", False, False],
                    ["examples / source_image / full_body_1.png", "crop", False, False],
                    ["examples / source_image / full3.png", "crop", False, False],
                    ["examples / source_image / full4.jpeg", "crop", False, False],
                    ["examples / source_image / art_13.png", "crop", False, False],
                    ["examples / source_image / art_5.png", "crop", False, False],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]
            gr.Examples(
                examples = examples,
                    fn = Talker_response,
                    inputs=[source_image, preprocess_type, is_still_mode, enhancer],
                    outputs=[gen_video],
                    # cache_examples = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
    return inference

if __name__ == "__main__":
    # llm = LLM(mode='offline').init_model('Linly', 'Linly - AI / Chinese - LLaMA - 2 - 7B - hf')
    # llm = LLM(mode='offline').init_model('Gemini', 'gemini - pro',
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     api_key = "your api key")
    # llm = LLM(mode='offline').init_model('Qwen', 'Qwen / Qwen - 1_8B - Chat')
    llm = LLM(mode = mode).init_model("Qwen", "Qwen / Qwen - 1_8B - Chat")
    talker = SadTalker(lazy_load = True)
    asr = WhisperASR("base")
    tts = EdgeTTS()
    gr.close_all()
    demo = main()
    demo.queue()
    # demo.launch()
    demo.launch(
        server_name = ip,  # 本地端口localhost:127.0.0.1 全局端口转发:"0.0.0.0"
        server_port = port,
            # 似乎在Gradio4.0以上版本可以不使用证书也可以进行麦克风对话
        ssl_certfile = ssl_certfile,
            ssl_keyfile = ssl_keyfile,
            ssl_verify = False,
            debug = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )