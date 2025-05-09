#!/usr/local/bin/python3
import whisper
import os
import argparse
from pathlib import Path

def transcriptions_to_srt(segments, srt_file):
    """
    Generate SRT file from Whisper transcription segments.
    """
    with open(srt_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = segment['start']
            end_time = segment['end']
            # Format time as SRT (HH:MM:SS,mmm)
            start_srt = f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{start_time%60:06.3f}".replace('.', ',')
            end_srt = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{end_time%60:06.3f}".replace('.', ',')
            f.write(f"{i}\n{start_srt} --> {end_srt}\n{segment['text'].strip()}\n\n")

def transcriptions_to_txt(segments, txt_file):
    """
    Generate plain text file from Whisper transcription segments, without timestamps.
    """
    with open(txt_file, 'w', encoding='utf-8') as f:
        for segment in segments:
            f.write(f"{segment['text'].strip()}\n")

def wav_to_subtitles(audio_file, output_dir="output", generate_txt=False):
    """
    Convert audio file to SRT (and optionally TXT) using Whisper.
    
    Args:
        audio_file (str): Path to input audio file (WAV, M4A, MP3).
        output_dir (str): Directory for output files.
        generate_txt (bool): If True, generate plain text file.
    """
    # Verify audio file exists
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Input file {audio_file} not found")
    
    # Validate file extension
    valid_extensions = {'.wav', '.m4a', '.mp3'}
    if Path(audio_file).suffix.lower() not in valid_extensions:
        raise ValueError(f"Input file must be one of: {', '.join(valid_extensions)}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output file paths
    base_name = Path(audio_file).stem
    srt_file = os.path.join(output_dir, f"{base_name}.srt")
    txt_file = os.path.join(output_dir, f"{base_name}.txt")
    
    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
    
    # Transcribe audio
    print(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file, verbose=False)
    
    # Generate SRT
    print(f"Generating subtitles to {srt_file}...")
    transcriptions_to_srt(result["segments"], srt_file)
    
    # Generate TXT if requested
    if generate_txt:
        print(f"Generating plain text to {txt_file}...")
        transcriptions_to_txt(result["segments"], txt_file)
    
    print(f"Subtitles saved to {srt_file}")
    if generate_txt:
        print(f"Plain text saved to {txt_file}")

def main():
    """
    Parse command-line arguments and run the conversion.
    """
    parser = argparse.ArgumentParser(description="Convert audio to SRT subtitles using Whisper.")
    parser.add_argument("audio_file", help="Path to input audio file (WAV, M4A, MP3)")
    parser.add_argument("-t", "--text", action="store_true", help="Also generate plain text file without timestamps")
    args = parser.parse_args()
    
    wav_to_subtitles(args.audio_file, generate_txt=args.text)

if __name__ == "__main__":
    main()