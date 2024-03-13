#!python

import asyncio
import shazamio
import time
from pydub import AudioSegment
import os
import requests


from ShazamAPI import Shazam




# async def main():
#   shazam = shazamio.Shazam()
#   out = await shazam.recognize_song('main.py')
#   print(out)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())

# use shazamio to recognize song from file "test song.mp4a"
async def recognizeSong(songName, duration, segmentNumber):
  pathToAudioFile = f"./input songs/segments/{songName}"

  shazam = shazamio.Shazam()

  start = time.time()
  out = await shazam.recognize_song(pathToAudioFile)
  end = time.time()

  # print("Time taken (seconds): ", end - start)
  # try:
  if out and out["track"] and out["track"]["sections"] and out["track"]["sections"][0] and out["track"]["sections"][0]["metadata"]:
    print(f"{duration}s  part {segmentNumber}: {out['track']['title']}")
    # print("Title: ", out["track"]["title"])
    # print("metadata: ", out["track"]["sections"][0]["metadata"])
    # print(out)
  else:
    print(f"{duration}s  part {segmentNumber}: No match found {out}")
  # except Exception as e:
  #   print(out)
  #   raise e


def recognizeSongWithShazam(pathToAudioFile):
  mp3_file_content_to_recognize = open(pathToAudioFile, 'rb').read()

  shazam = Shazam(mp3_file_content_to_recognize)
  recognize_generator = shazam.recognizeSong()
  m = None
  # try:
  match = next(recognize_generator) # current offset & shazam response to recognize requests
  m = match
  match =  match[1]
  if match and match.get("track") and match.get("track").get("title"):
    print(f"Shazam: {os.path.basename(pathToAudioFile)}: {match['track']['title']}")
  else:
    print(f"Shazam: {os.path.basename(pathToAudioFile)}: NO MATCH FOUND    {match}")
    return "no match found"

  # except Exception as e:
  #   print("error", e)
  #   print("match", m)

def recognizeSongWithAudD(pathToAudioFile):
  song = open(pathToAudioFile, 'rb').read()

  response = requests.post(
      "https://enterprise.audd.io/",
      data={"api_token": "93184b11c98558a04e54e3644c33b1a5"},
      files={"file": song}
    )

  # print the response
  if response.json() and response.json().get("result"):

    titles = [songData['title'] for item in response.json().get("result") for songData in item['songs']]

    print(f"AudD: {os.path.basename(pathToAudioFile)}: {titles}")
  else:
    print(f"AudD: {os.path.basename(pathToAudioFile)}: NO MATCH FOUND     {response.json()}")

def splitAudioIntoSegments(audioFileName):
  songName = audioFileName[:-4]
  outputFolder = f"./input songs/segments/{songName}/"
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  # Load the song (replace 'your_song.m4a' with the path to your file)
  song = AudioSegment.from_file(f"./input songs/{audioFileName}", format="mp3")  

  # Extract the first 24 seconds
  first30s = song[:30000]  # 30000 milliseconds = 30 seconds

  first30s.export( f"{outputFolder}/30s.mp3", format="mp3")

  # 5 segments of 6s, 10 segments of 3s, 15 segments of 2s, 20 segments of 1.5s
  numberOfSegments = [5, 10, 15, 20] 

  # Split the first 24 seconds into segments of 6s, 4s, 2s, 1s
  for num in numberOfSegments:
    segmentLength = 30000 // num

    for i in range(num):
      segment = first30s[i*segmentLength:(i+1)*segmentLength]
      segment.export(f"{outputFolder}/{segmentLength/1000}s_segment_{i+1}.mp3", format="mp3")

def recongizeSongFromAudioFileSegments(audioFileName):
  songName = audioFileName[:-4]
  pathToAudioFile = f"./input songs/segments/{songName}"  

  # 5 segments of 6s, 10 segments of 3s, 15 segments of 2s, 20 segments of 1.5s
  numberOfSegments = [5, 10, 15, 20] 

  recognizeSongWithAudD(f"{pathToAudioFile}/30s.mp3")
  for num in numberOfSegments:
    segmentLength = 30 / num

    for i in range(num):
      res = recognizeSongWithAudD(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")

      if segmentLength <= 3:
        time.sleep(10)
    print("")

  recognizeSongWithShazam(f"{pathToAudioFile}/30s.mp3")
  for num in numberOfSegments:
    segmentLength = 30 / num

    for i in range(num):
      res = recognizeSongWithShazam(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")

      if res == "no match found":
        time.sleep(15)
        # alternateRecognizeSong(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")
      elif segmentLength <= 3:
        time.sleep(10)
    print("")



def compressAudioFile(audioFileName):
  songName = audioFileName[:-4]
  outputFolder = f"./input songs/compressed/{songName}/"
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  # Load the original MP3 file
  original_audio = AudioSegment.from_mp3(f"./input songs/{audioFileName}")

  # take the middle 6 seconds of the song
  middle = len(original_audio) // 2
  sixSeconds = original_audio[middle-3000:middle+3000]

  # Define compression levels (bitrate in kbps)
  compressionLevels = [8, 12, 16, 24, 32, 48, 64, 96]  


  # Compress the audio at each compression level
  for level in compressionLevels:
      # Compress the audio to the specified bitrate
      compressedAudio = sixSeconds.set_frame_rate(44100).set_channels(2)
      compressedAudio.export(
          f"{outputFolder}/compressed_{level}kbps.mp3",
          format="mp3",
          codec="libmp3lame",
          bitrate=f"{level}k",
      )
      print(f"Audio compressed at {level} kbps")

def recongizeSongFromCompressedAudioFiles(audioFileName):
  songName = audioFileName[:-4]
  pathToAudioFile = f"./input songs/compressed/{songName}"

  # Define compression levels (bitrate in kbps)
  compressionLevels = [8, 12, 16, 24, 32, 48, 64, 96]  

  for level in compressionLevels:
    res = recognizeSongWithAudD(f"{pathToAudioFile}/compressed_{level}kbps.mp3")
    time.sleep(10)
  
  for level in compressionLevels:
    res = recognizeSongWithShazam(f"{pathToAudioFile}/compressed_{level}kbps.mp3")

    if res == "no match found":
      time.sleep(15)
    else:
      time.sleep(2)
  

# SEGMENTS
# Step 1: Split the audio into segments
# splitAudioIntoSegments("Eminem - Rap God (Explicit).mp3")
      
# Step 2: Recognize the song from each segment
# recongizeSongFromAudioFileSegments("Eminem - Rap God (Explicit).mp3")

# COMPRESSED FILES
# Step 1: Compress the audio file at different bitrates
compressAudioFile("Bob Marley & The Wailers - Could You Be Loved.mp3")

# Step 2: Recognize the song from each compressed audio file
recongizeSongFromCompressedAudioFiles("Bob Marley & The Wailers - Could You Be Loved.mp3")





