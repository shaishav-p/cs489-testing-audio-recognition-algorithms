from pydub import AudioSegment
import requests

# load song
song = open(f"./input songs/segments/Eminem - Rap God (Explicit)/1.5s_segment_1.mp3", 'rb').read()

response = requests.post(
    "https://enterprise.audd.io/",
    data={"api_token": "93184b11c98558a04e54e3644c33b1a5"},
    files={"file": song}
    )

# print the response
print(response.status_code)
print(response.json())
