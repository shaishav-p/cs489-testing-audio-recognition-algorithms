#!python

import time
import os
import requests

from pydub import AudioSegment
from ShazamAPI import Shazam

'''
Recognize a song from an audio file using Shazam's API
@param pathToAudioFile: path to the audio file to recognize
@return: None
'''
def recognizeSongWithShazam(pathToAudioFile):
  mp3_file_content_to_recognize = open(pathToAudioFile, 'rb').read()

  shazam = Shazam(mp3_file_content_to_recognize)
  recognize_generator = shazam.recognizeSong()
  m = None

  match = next(recognize_generator) # current offset & Shazam response to recognize requests
  m = match

  # extract song match details from the API's json response
  match =  match[1]
  if match and match.get("track") and match.get("track").get("title"):
    print(f"Shazam: {os.path.basename(pathToAudioFile)}: {match['track']['title']}")
  else:
    print(f"Shazam: {os.path.basename(pathToAudioFile)}: NO MATCH FOUND    {match}")
    return "no match found"


'''
Recognize a song from an audio file using AudD's API
@param pathToAudioFile: path to the audio file to recognize
@return: None
'''
def recognizeSongWithAudD(pathToAudioFile):
  song = open(pathToAudioFile, 'rb').read()

  response = requests.post(
      "https://enterprise.audd.io/",
      data={"api_token": "93184b11c98558a04e54e3644c33b1a5"},
      files={"file": song}
    )

  # extract song match details from API's json response
  if response.json() and response.json().get("result"):
    titles = [songData['title'] for item in response.json().get("result") for songData in item['songs']]
    print(f"AudD: {os.path.basename(pathToAudioFile)}: {titles}")
  else:
    print(f"AudD: {os.path.basename(pathToAudioFile)}: NO MATCH FOUND     {response.json()}")



'''
Create a folder for the audio file and split the first 30s of the audio file into segments of different lengths (6s, 4s, 2s, 1s)
@param audioFileName: name of the audio file to split into segments
@return: None
'''
def splitAudioIntoSegments(audioFileName):
  songName = audioFileName[:-4]
  outputFolder = f"./input songs/segments/{songName}/"
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  # Load the song from the input songs folder
  song = AudioSegment.from_file(f"./input songs/{audioFileName}", format="mp3")  

  # Extract the first 30 seconds of the song
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


'''
Iterate through all segments of the audio file and call Shazam and AudD's APIs for each segment to recognize the song
@param audioFileName: name of the audio file to recognize
@return: None
'''
def recognizeSongFromAudioFileSegments(audioFileName):
  songName = audioFileName[:-4]
  pathToAudioFile = f"./input songs/segments/{songName}"  

  # 5 segments of 6s, 10 segments of 3s, 15 segments of 2s, 20 segments of 1.5s
  numberOfSegments = [5, 10, 15, 20] 

  # Call AudD's API to recognize the song from each segment
  recognizeSongWithAudD(f"{pathToAudioFile}/30s.mp3")
  for num in numberOfSegments:
    segmentLength = 30 / num

    for i in range(num):
      res = recognizeSongWithAudD(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")

      if segmentLength <= 3:
        # We pause for 10 seconds after each request to AudD's API to avoid the API's rate limiting
        time.sleep(10)
    print("")

  # Call Shazam's API to recognize the song from each segment
  recognizeSongWithShazam(f"{pathToAudioFile}/30s.mp3")
  for num in numberOfSegments:
    segmentLength = 30 / num

    for i in range(num):
      res = recognizeSongWithShazam(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")

      if res == "no match found":
        time.sleep(15)
        # alternateRecognizeSong(f"{pathToAudioFile}/{segmentLength}s_segment_{i+1}.mp3")
      elif segmentLength <= 3:
        # We pause for 10 seconds after each request to Shazam's API to avoid the API's rate limiting
        time.sleep(10)
    print("")


'''
Create a folder for the audio file and compress the audio file at different bitrates (8, 12, 16, 24, 32, 48, 64, 96 kbps)
@param audioFileName: name of the audio file to compress
@return: None
'''
def compressAudioFile(audioFileName):
  songName = audioFileName[:-4]
  outputFolder = f"./input songs/compressed/{songName}/"

  # Create the output folder if it doesn't exist
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  # Load the original MP3 file
  original_audio = AudioSegment.from_mp3(f"./input songs/{audioFileName}")

  # Take the middle 6 seconds of the song
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


'''
Iterate through all compressed audio files and call Shazam and AudD's APIs for each compressed audio file to recognize the song
@param audioFileName: name of the audio file to recognize
@return: None
'''
def recognizeSongFromCompressedAudioFiles(audioFileName):
  songName = audioFileName[:-4]
  pathToAudioFile = f"./input songs/compressed/{songName}"

  # Define compression levels (bitrate in kbps)
  compressionLevels = [8, 12, 16, 24, 32, 48, 64, 96]  

  # Call AudD's API to recognize the song from each compressed audio file
  for level in compressionLevels:
    res = recognizeSongWithAudD(f"{pathToAudioFile}/compressed_{level}kbps.mp3")

    # We pause for 10 seconds after each request to AudD's API to avoid the API's rate limiting
    time.sleep(10)
  
  # Call Shazam's API to recognize the song from each compressed audio file
  for level in compressionLevels:
    res = recognizeSongWithShazam(f"{pathToAudioFile}/compressed_{level}kbps.mp3")

    # We pause for after each request to AudD's API to avoid the API's rate limiting
    # If no match is found, we pause for 15 seconds due to Shazam's rate limiting policy for no matches
    if res == "no match found":
      time.sleep(15)
    else:
      time.sleep(2)


'''
Create a folder for the audio file and store the first 3s and middle 3s of the audio file in the folder
@param audioFileName: name of the audio file to get the first 3s and middle 3s
@return: None
'''
def getFirstAndMiddle3s(audioFileName):
  songName = audioFileName[:-4]
  outputFolder = f"./input songs/firstAndMiddle3s/{songName}/"

  # Create the output folder if it doesn't exist
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  # Load the original MP3 file
  original_audio = AudioSegment.from_mp3(f"./input songs/{audioFileName}")

  # Take the first 3 seconds
  first3s = original_audio[:3000]  # 3000 milliseconds = 3 seconds
  first3s.export( f"{outputFolder}/first3s.mp3", format="mp3")

  # Extract the middle 3 seconds
  middle = len(original_audio) // 2
  middle3s = original_audio[middle-1500:middle+1500]
  middle3s.export( f"{outputFolder}/middle3s.mp3", format="mp3")


'''
Call the Shazam and AudD's APIs for the first 3s and middle 3s of the audio file to recognize the song
@param audioFileName: name of the audio file to recognize
@return: None
'''
def recognizeSongFromFirstAndMiddle3s(audioFileName):
  songName = audioFileName[:-4]
  pathToAudioFile = f"./input songs/firstAndMiddle3s/{songName}"

  # Call AudD's API to recognize the song from the first 3s and middle 3s
  recognizeSongWithAudD(f"{pathToAudioFile}/first3s.mp3")
  recognizeSongWithAudD(f"{pathToAudioFile}/middle3s.mp3")

  # Call Shazam's API to recognize the song from the first 3s and middle 3s
  recognizeSongWithShazam(f"{pathToAudioFile}/first3s.mp3")
  recognizeSongWithShazam(f"{pathToAudioFile}/middle3s.mp3")



# -----------------------------------------------------------------------------------------------
# Uncomment the function calls to run the different experiments
# Note: the api_token in the recognizeSongWithAudD function should be updated with a valid token
# -----------------------------------------------------------------------------------------------

# SEGMENTS
# Step 1: Split the audio into segments
# splitAudioIntoSegments("Eminem - Rap God (Explicit).mp3")
      
# Step 2: Recognize the song from each segment
# recognizeSongFromAudioFileSegments("Eminem - Rap God (Explicit).mp3")



# COMPRESSED FILES
# Step 1: Compress the audio file at different bitrates
# compressAudioFile("Bob Marley & The Wailers - Could You Be Loved.mp3")

# Step 2: Recognize the song from each compressed audio file
# recognizeSongFromCompressedAudioFiles("Bob Marley & The Wailers - Could You Be Loved.mp3")



# FIRST 3s and MID 3s
# Step 1: Get the first 3s and middle 3s of the audio file
# getFirstAndMiddle3s("Bob Marley & The Wailers - Could You Be Loved.mp3")

# Step 2: Recognize the song from the first 3s and middle 3s
# recognizeSongFromFirstAndMiddle3s("Bob Marley & The Wailers - Could You Be Loved.mp3")
