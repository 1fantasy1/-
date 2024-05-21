from modelscope.pipelines import pipeline as pipeline_ali
from modelscope.utils.constant import Tasks
from moviepy.editor import VideoFileClip
import os
import ffmpeg
from faster_whisper import WhisperModel
import math
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM,pipeline

def convert_seconds_to_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = math.floor((seconds % 1) * 1000)
    output = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"
    return output


# 制作字幕文件
def make_srt(file_path, model_name="small"):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cuda":
        model = WhisperModel(model_name, device="cuda", compute_type="float16", download_root="./model_from_whisper",
                             local_files_only=False)
    else:
        model = WhisperModel(model_name, device="cpu", compute_type="int8", download_root="./model_from_whisper",
                             local_files_only=False)
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

    segments, info = model.transcribe(file_path, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    count = 0
    with open('./video.srt', 'w') as f:  # Open file for writing
        for segment in segments:
            count += 1
            duration = f"{convert_seconds_to_hms(segment.start)} --> {convert_seconds_to_hms(segment.end)}\n"
            text = f"{segment.text.lstrip()}\n\n"

            f.write(f"{count}\n{duration}{text}")  # Write formatted string to the file
            print(f"{duration}{text}", end='')

    with open("./video.srt", 'r', encoding="utf-8") as file:
        srt_data = file.read()

    return "转写完毕"

# 翻译字幕
def make_tran():
    pipeline_ins = pipeline(task=Tasks.translation, model=model_dir_ins)

    with open("./video.srt", 'r', encoding="utf-8") as file:
        gweight_data = file.read()

    result = gweight_data.split("\n\n")

    if os.path.exists("./two.srt"):
        os.remove("./two.srt")

    for res in result:

        line_srt = res.split("\n")
        try:
            outputs = pipeline_ins(input=line_srt[2])
        except Exception as e:
            print(str(e))
            break
        print(outputs['translation'])

        with open("./two.srt", "a", encoding="utf-8") as f:
            f.write(f"{line_srt[0]}\n{line_srt[1]}\n{line_srt[2]}\n{outputs['translation']}\n\n")

    return "翻译完毕"

# 合并字幕
def merge_sub(video_path,srt_path):

    if os.path.exists("./test_srt.mp4"):
        os.remove("./test_srt.mp4")

    ffmpeg.input(video_path).output("./test_srt.mp4", vf="subtitles=" + srt_path).run()

    return "./test_srt.mp4"