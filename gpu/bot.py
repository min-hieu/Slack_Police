import slack
import os 
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import time

def get_total_gpu(gpu_log_split):
    text = gpu_log_split[7]
    return int(text.split(': ')[1])

def get_gpu_temp(gpu_log):
    gpu_log_split = gpu_log.split('\n')
    gpu_stat_start = 8
    temperature_list = []
    for i in range(get_total_gpu(gpu_log_split)):
        gpu_offset = 10 * i
        temp_text = gpu_log_split[gpu_stat_start + gpu_offset + 2]
        temperature_list.append(int(temp_text.split(': ')[1].split()[0]))

    return temperature_list

def get_gpu_log():
    result = subprocess.run(['nvidia-smi', '-q', '-d', 'temperature'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')


env_path = Path('.') / '.env'
load_dotenv(dotenv_path = env_path)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
threshold = 36.5
sleep_time = 10 # in unit of minute
channel = "#gpu-overheat"

total_gpu = get_total_gpu(get_gpu_log().split('\n'))
overheat_count = 0 # counting consecutive period of overheat
while (1):
    warning_start = 0

    for i, gpu_tmp in enumerate(get_gpu_temp(get_gpu_log())):
        if gpu_tmp > threshold:
            if (warning_start == 0) and (overheat_count == 0):
                warning_start = 1
                overheat_count += 1
                client.chat_postMessage(channel=channel, text="=== GEOMETRY2 GPU OVERHEAT! ===")
            if (warning_start == 0) and (overheat_count > 0):
                time_elapsed = overheat_count * sleep_time
                warning_start = 1
                overheat_count += 1
                client.chat_postMessage(channel=channel, text=f"=== GEOMETRY2 OVERHEATED FOR OVER {time_elapsed}MINS ===")
            warning_text = f"GPU #{i} current temp: {gpu_tmp}°C"
            client.chat_postMessage(channel=channel, text=warning_text)


    if warning_start == 0: # reset overheat 
        overheat_count = 0
    else:
        client.chat_postMessage(channel=channel, text="===============================")


    time.sleep(sleep_time * 60)
