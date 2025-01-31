from pydub import AudioSegment
import math

def audio_to_buzzer(input_WAV_file, output_file):
    # Custom variables
    segment_duration_ms = 5  # Analyze in x ms chunks
    buzzer_cutoff = -25  # dBS cutoff for buzzer on/off

    audio = AudioSegment.from_wav(input_WAV_file)
    audio_length = len(audio)
    chunks = [audio[i * segment_duration_ms:(i + 1) * segment_duration_ms] for i in range(int(audio_length/segment_duration_ms))]
    chunks_volume = [sound_chunk.dBFS//1 for sound_chunk in chunks]
    chunks_volume2 = [-100 if math.isnan(chunk_volume) else chunk_volume for chunk_volume in chunks_volume]
    chunks_volume3 = [1 if int(chunk_volume) > buzzer_cutoff else 0 for chunk_volume in chunks_volume2]
    chunks_volume3.insert(0, segment_duration_ms)
    output_str = ""
    for chunk_volume in chunks_volume3:
        output_str += f"{chunk_volume},"
    with open(output_file, "w") as f:
        f.write(output_str)
    print(f"Audio conversion complete: {len(chunks)} audio chunks, {buzzer_cutoff} dBS cutoff")


# Megalovania first 8 seconds
WAV_file_path = "C:/Users/maxim/Desktop/Pico/alarmClock/Megalovania short WAV.wav"
output_python_file = "C:/Users/maxim/Desktop/Pico/alarmClock/buzzer_melody.txt"

audio_to_buzzer(WAV_file_path, output_python_file)