#! /usr/bin/python3
import librosa 
import numpy as np
import pyaudio
from tensorflow import keras 
import os 
import redis

# Set up the audio streamchunk = 1024 
# Set up the audio stream  
chunk = 44100  
sample_format = pyaudio.paInt16  
channels = 1  
rate = 22050 
n_mfcc=13 
n_fft=2048  
hop_length=512

window_len = 22050

labels = ['down', 'left', 'right', 'up']
 
p = pyaudio.PyAudio() 
stream = p.open(format=sample_format, 
                channels=channels,                 
                rate=rate, 
                frames_per_buffer=chunk,                 
                input=True) 
 
model = keras.models.load_model(f'./final')

print("Listening...") 

os.environ['TF_MIN_LOG_LEVEL'] = '3' 

rd = redis.Redis(host="localhost")

while True:     
    try: 
        # Capture voice input from the microphone         
        data = stream.read(chunk) 
        samples = np.frombuffer(data, dtype=np.int16)         
        samples = samples.astype(np.float32) / 32767.0  # Normalize to [-1, 1] 
         
        
        direction = None

        for i in range(5):
            sample = samples[i * int(window_len / 4) : i * int(window_len / 4) + window_len]

            MFCCs = librosa.feature.mfcc(y=sample, n_mfcc=n_mfcc, hop_length=hop_length, n_fft=n_fft) 
            result = model.predict(MFCCs.T[..., np.newaxis][np.newaxis, ...], verbose = 0)[0]

            if max(result) > 0.7:
                direction = labels[np.argmax(result)]

        if direction:
            print(direction)
            rd.set("go_dir", direction)
    except KeyboardInterrupt:         
        break 
 
# Clean up the audio stream 
stream.stop_stream() 
stream.close() 
p.terminate()