#import openai
from openai import OpenAI
from pyht import Client
from dotenv import load_dotenv
from pyht.client import TTSOptions
import os
import requests
from tqdm import tqdm  
from PIL import Image
import time
from moviepy.editor import VideoFileClip, AudioFileClip
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel




app = FastAPI()

class Question(BaseModel):
    question: str
 



def get_response(question):
    client = OpenAI(
        api_key="da8a6b3575474154893006a8b673fe67",
        base_url="https://api.aimlapi.com",
    )
    response = client.chat.completions.create(
    model= "gpt-4o",
    messages=[
            {
                "role": "system",
                "content": "For the given user prompt, respond as Joe Biden in a concise manner. The goal is to produce a coherent and effective response that is brief and under 10 seconds."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        max_tokens=200,  # Adjust the max_tokens to limit the length of the response
        temperature=0.7  # Adjust temperature for more controlled responses
    )
    message = response.choices[0].message.content
    print(f"{message}")
    return message





def get_audio(text):
    load_dotenv()

    client = Client(
        user_id="RYQUFTAm5jN4yqwNo9zk1yuVsQJ2",
        api_key="ab9cff6bb28b43ba942766a160d121ac",
    )

    options = TTSOptions(voice="s3://voice-cloning-zero-shot/d87b6e1a-f5d1-4507-8249-8d55bc057b8a/joe-biden/manifest.json")

    output_file = "audio.mp3"
    if not os.path.exists(output_file):
        open(output_file, 'w').close()

    with open(output_file, "wb") as f:
        for chunk in tqdm(client.tts(text, options)):
            f.write(chunk)

    print(f"Output saved to {output_file}")
    return output_file



def get_image(text):
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/ultra",
        headers={
            "authorization": f"sk-fBGQHFpCAlqjPGZgIF6AWbHRcm6d5DEkCO2YqEySxxT2sqw5",
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "prompt": text,
            "output_format": "png",
        },
    )

    if response.status_code == 200:
        with open("./image.png", 'wb') as file:
            file.write(response.content)
        image = Image.open("./image.png")
        resized_image = image.resize((768, 768), resample=Image.LANCZOS)
        
        # Save the resized image
        resized_image.save("./resized_image.png")
    else:
        raise Exception(str(response.json()))
    return resized_image



def generate_video_id(image):
    response = requests.post(
    f"https://api.stability.ai/v2beta/image-to-video",
    headers={
        "authorization": f"sk-fBGQHFpCAlqjPGZgIF6AWbHRcm6d5DEkCO2YqEySxxT2sqw5"
    },
    files={
        "image": open("./resized_image.png", "rb")
    },
    data={
        "seed": 0,
        "cfg_scale": 1.8,
        "motion_bucket_id": 127
    },
    )

    return response.json().get('id')




def get_video(id):
    generation_id = id
    time.sleep(30)

    response = requests.request(
        "GET",
        f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
        headers={
            'accept': "video/*",  # Use 'application/json' to receive base64 encoded JSON
            'authorization': f"sk-fBGQHFpCAlqjPGZgIF6AWbHRcm6d5DEkCO2YqEySxxT2sqw5"
        },
    )
    output_file='video.mp4'
    if not os.path.exists(output_file):
        # Create an empty file if it doesn't exist
        open(output_file, 'w').close()
    if response.status_code == 202:
        print("Generation in-progress, try again in 10 seconds.")
    elif response.status_code == 200:
        print("Generation complete!")
        with open(output_file, 'wb') as file:
            file.write(response.content)
    else:
        raise Exception(str(response.json()))
    return output_file




def combine_audio_video(video_file, audio_file, output_file):
    video_clip = VideoFileClip(video_file)
    audio_clip = AudioFileClip(audio_file)
    video_with_audio = video_clip.set_audio(audio_clip)
    video_with_audio.write_videofile(output_file, codec='libx264', audio_codec='aac')
    return output_file



@app.post("/reply")
def main(question: Question):
    try:
        text = get_response(question.question)
        audio = get_audio(text)
        image = get_image(text)
        video_id = generate_video_id(image)
        video = get_video(video_id)
        output_file = 'output_video.mp4'
        combine_audio_video(video, audio, output_file)
        file_path = os.path.abspath(output_file)
        return FileResponse(file_path, media_type='video/mp4', filename="output_video.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    


