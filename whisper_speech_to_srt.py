#!/usr/local/bin/python3
import whisper
import os
import argparse
import subprocess
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
            end_srt   = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{end_time%60:06.3f}".replace('.', ',')
            f.write(f"{i}\n{start_srt} --> {end_srt}\n{segment['text'].strip()}\n\n")

def transcriptions_to_txt(segments, txt_file):
    """
    Generate plain text file from Whisper transcription segments, without timestamps.
    """
    with open(txt_file, 'w', encoding='utf-8') as f:
        for segment in segments:
            f.write(f"{segment['text'].strip()}\n")

def convert_to_wav(input_file, wav_path):
    """
    Convert input media (e.g., MP4) to WAV using ffmpeg.
    """
    cmd = [
        'ffmpeg',
        '-y',              # overwrite output
        '-i', input_file,
        '-ac', '1',        # mono
        '-ar', '16000',    # 16 kHz sample rate
        wav_path
    ]
    subprocess.run(cmd, check=True)

def wav_to_subtitles(media_file, output_dir="output", generate_txt=False):
    """
    Convert media file to SRT (and optionally TXT) using Whisper.

    Args:
        media_file (str): Path to input media (WAV, M4A, MP3, MP4).
        output_dir (str): Directory for output files.
        generate_txt (bool): If True, generate plain text file.
    """
    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Input file {media_file} not found")

    # Supported extensions
    ext = Path(media_file).suffix.lower()
    valid_audio = {'.wav', '.m4a', '.mp3'}
    temp_wav = None

    if ext == '.mp4':
        # Convert MP4 to WAV first
        base = Path(media_file).stem
        temp_wav = os.path.join(Path(output_dir), f"{base}_temp.wav")
        os.makedirs(output_dir, exist_ok=True)
        print(f"Converting {media_file} to WAV...")
        convert_to_wav(media_file, temp_wav)
        audio_path = temp_wav
    elif ext in valid_audio:
        audio_path = media_file
        os.makedirs(output_dir, exist_ok=True)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: WAV, M4A, MP3, MP4.")

    # Paths for outputs
    base_name = Path(media_file).stem
    srt_file = os.path.join(output_dir, f"{base_name}.srt")
    txt_file = os.path.join(output_dir, f"{base_name}.txt")

    # Load Whisper
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # tiny, base, small, medium, large

    # Transcribe
    print(f"Transcribing {audio_path}...")
    result = model.transcribe(audio_path, verbose=False)

    # Write SRT
    print(f"Writing subtitles to {srt_file}...")
    transcriptions_to_srt(result['segments'], srt_file)

    # Optional TXT
    if generate_txt:
        print(f"Writing text to {txt_file}...")
        transcriptions_to_txt(result['segments'], txt_file)

    # Clean up temp
    if temp_wav and os.path.exists(temp_wav):
        os.remove(temp_wav)

    print(f"Done. SRT saved to {srt_file}")
    if generate_txt:
        print(f"Plain text saved to {txt_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert audio/video to SRT subtitles using Whisper."
    )
    parser.add_argument(
        'media_file',
        help='Path to input media file (WAV, M4A, MP3, MP4)'
    )
    parser.add_argument(
        '-t', '--text',
        action='store_true',
        help='Also generate plain text output without timestamps'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='Directory for output files'
    )
    args = parser.parse_args()

    wav_to_subtitles(
        args.media_file,
        output_dir=args.output,
        generate_txt=args.text
    )

if __name__ == '__main__':
    main()
