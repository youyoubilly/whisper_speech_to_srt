#!/usr/local/bin/python3
import whisper
import os
import argparse
import subprocess
from pathlib import Path
import time
import sys

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

def transcriptions_to_lrc(segments, lrc_file, title=""):
    """
    Generate LRC (lyrics) file from Whisper transcription segments.
    
    Args:
        segments (list): List of Whisper transcription segments.
        lrc_file (str): Path to output LRC file.
        title (str): Optional title for the LRC metadata.
    """
    with open(lrc_file, 'w', encoding='utf-8') as f:
        # Write LRC metadata headers
        f.write(f"[ti:{title}]\n")
        f.write("[ar:]\n")
        f.write("[al:]\n")
        f.write("[by:Whisper STT]\n")
        f.write("[offset:0]\n")
        f.write("\n")
        
        # Write lyrics with timestamps
        for segment in segments:
            start_time = segment['start']
            # Convert to total minutes and seconds
            total_minutes = int(start_time // 60)
            total_seconds = int(start_time % 60)
            # Get centiseconds (hundredths of a second)
            centiseconds = int((start_time % 1) * 100)
            
            # Format as LRC: [MM:SS.xx]text
            lrc_timestamp = f"[{total_minutes:02d}:{total_seconds:02d}.{centiseconds:02d}]"
            f.write(f"{lrc_timestamp}{segment['text'].strip()}\n")

def find_audio_files(directory, recursive=False):
    """
    Find all supported audio/video files in a directory.
    
    Args:
        directory (str): Path to directory to search.
        recursive (bool): If True, search subdirectories recursively.
    
    Returns:
        list: List of audio/video file paths.
    """
    supported_extensions = {'.wav', '.m4a', '.mp3', '.aac', '.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm', '.m4v', '.3gp'}
    audio_files = []
    
    directory_path = Path(directory)
    
    if recursive:
        # Recursively find all audio files (case-insensitive)
        for ext in supported_extensions:
            audio_files.extend(directory_path.rglob(f"*{ext}"))
            audio_files.extend(directory_path.rglob(f"*{ext.upper()}"))
    else:
        # Only search immediate directory (case-insensitive)
        for ext in supported_extensions:
            audio_files.extend(directory_path.glob(f"*{ext}"))
            audio_files.extend(directory_path.glob(f"*{ext.upper()}"))
    
    # Remove duplicates (in case file system is case-insensitive) and sort
    audio_files = list(set(audio_files))
    return sorted([str(f) for f in audio_files])

def get_srt_output_path(media_file, output_dir=None):
    """
    Return the expected SRT output path for a media file.
    Matches the path logic used in wav_to_subtitles.
    """
    base_name = Path(media_file).stem
    if output_dir is None:
        return Path(media_file).parent / f"{base_name}.srt"
    return Path(output_dir) / f"{base_name}.srt"

def classify_media_files(media_files, output_dir=None):
    """
    Split media files into those with an existing SRT and those without.

    Returns:
        tuple: (with_srt, without_srt) where each item is (media_path, srt_path).
    """
    with_srt = []
    without_srt = []
    for media_file in media_files:
        srt_path = get_srt_output_path(media_file, output_dir)
        if srt_path.exists():
            with_srt.append((media_file, str(srt_path)))
        else:
            without_srt.append((media_file, str(srt_path)))
    return with_srt, without_srt

def print_batch_classification(audio_files, with_srt, without_srt):
    """Print classified file lists for folder batch processing."""
    print(f"\nFound {len(audio_files)} audio file(s):")

    if with_srt:
        print(f"\nAlready have SRT ({len(with_srt)}):")
        for i, (media_path, srt_path) in enumerate(with_srt, 1):
            print(f"  {i}. {media_path}")
            print(f"     -> {srt_path}")

    if without_srt:
        print(f"\nNeed processing ({len(without_srt)}):")
        for i, (media_path, _) in enumerate(without_srt, 1):
            print(f"  {i}. {media_path}")

def prompt_batch_action(audio_files, with_srt, without_srt, model_name):
    """
    Interactively ask whether to skip existing SRT files or reprocess all.

    Returns:
        list: Media file paths to process, or None if cancelled.
    """
    total = len(audio_files)
    n_with = len(with_srt)
    n_without = len(without_srt)

    print(f"\nAbout to process using the '{model_name}' model.")

    if n_with == 0:
        print(f"\nNo existing SRT files found. {total} file(s) will be processed.")
        response = input("Continue? (y/n): ").strip().lower()
        if response not in ('y', 'yes'):
            print("Operation cancelled.")
            return None
        return list(audio_files)

    if n_without == 0:
        print("\nChoose an action:")
        print("  [1] Skip all (nothing to do)")
        print(f"  [2] Reprocess all {total} file(s) (overwrite existing SRT)")
        print("  [3] Cancel")
        while True:
            choice = input("Enter choice (1/2/3): ").strip()
            if choice == '1':
                print("All files skipped (SRT already exists).")
                return []
            if choice == '2':
                return list(audio_files)
            if choice == '3':
                print("Operation cancelled.")
                return None
            print("Invalid choice. Please enter 1, 2, or 3.")

    print("\nChoose an action:")
    print(f"  [1] Skip existing, process {n_without} new file(s) only")
    print(f"  [2] Reprocess all {total} file(s) (overwrite existing SRT)")
    print("  [3] Cancel")
    while True:
        choice = input("Enter choice (1/2/3): ").strip()
        if choice == '1':
            return [media_path for media_path, _ in without_srt]
        if choice == '2':
            return list(audio_files)
        if choice == '3':
            print("Operation cancelled.")
            return None
        print("Invalid choice. Please enter 1, 2, or 3.")

def resolve_files_to_process(audio_files, with_srt, without_srt, model_name, skip_existing, force):
    """
    Determine which files to process based on CLI flags or interactive prompt.

    Returns:
        tuple: (files_to_process, skipped_count) or (None, 0) if cancelled.
    """
    if force:
        return list(audio_files), 0

    if skip_existing:
        files_to_process = [media_path for media_path, _ in without_srt]
        skipped = len(with_srt)
        if not files_to_process:
            print("All files skipped (SRT already exists).")
        return files_to_process, skipped

    files_to_process = prompt_batch_action(audio_files, with_srt, without_srt, model_name)
    if files_to_process is None:
        return None, 0
    skipped = len(audio_files) - len(files_to_process)
    return files_to_process, skipped

def convert_to_wav(input_file, wav_path):
    """
    Extract audio from video/audio file and convert to WAV using ffmpeg.
    Supports any video/audio format that ffmpeg can handle.
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

def wav_to_subtitles(media_file, output_dir=None, generate_srt=True, generate_txt=False, generate_lrc=False, model_name="base", language=None):
    """
    Convert media file to SRT, TXT, and LRC using Whisper.

    Args:
        media_file (str): Path to input media (audio: WAV, M4A, MP3, AAC; video: MP4, MOV, AVI, MKV, FLV, WEBM, M4V, 3GP).
        output_dir (str, optional): Directory for output files. If None, use input file's directory.
        generate_srt (bool): If True, generate SRT subtitle file (default: True).
        generate_txt (bool): If True, generate plain text file (default: False).
        generate_lrc (bool): If True, generate LRC lyrics file (default: False).
        model_name (str): Whisper model to use (default: "base").
        language (str, optional): Language code (e.g., 'en', 'zh', 'es'). If None, auto-detect.
    """
    # Start timing
    start_time = time.time()

    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Input file {media_file} not found")

    # Supported extensions
    ext = Path(media_file).suffix.lower()
    valid_audio = {'.wav', '.m4a', '.mp3', '.aac'}
    valid_video = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm', '.m4v', '.3gp'}
    temp_wav = None
    output_dir_arg = output_dir

    # Determine output directory
    if output_dir is None:
        output_dir = Path(media_file).parent
    else:
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)

    if ext in valid_video:
        # Extract audio from video file and convert to WAV
        base = Path(media_file).stem
        temp_wav = os.path.join(output_dir, f"{base}_temp.wav")
        print(f"Extracting audio from {media_file} and converting to WAV...")
        convert_to_wav(media_file, temp_wav)
        audio_path = temp_wav
    elif ext in valid_audio:
        audio_path = media_file
    else:
        supported_formats = ', '.join(sorted(valid_audio | valid_video))
        raise ValueError(f"Unsupported file type: {ext}. Supported formats: {supported_formats}.")

    # Paths for outputs
    base_name = Path(media_file).stem
    srt_file = str(get_srt_output_path(media_file, output_dir_arg))
    txt_file = str(output_dir / f"{base_name}.txt")
    lrc_file = str(output_dir / f"{base_name}.lrc")

    # Load Whisper
    print(f"Loading Whisper model ({model_name})...")
    import ssl
    import urllib.request
    ssl._create_default_https_context = ssl._create_unverified_context
    model = whisper.load_model(model_name)

    # Transcribe
    print(f"Transcribing {audio_path}...")
    transcribe_options = {'verbose': False}
    if language:
        transcribe_options['language'] = language
        print(f"Using language: {language}")
    else:
        print("Language: auto-detect")
    result = model.transcribe(audio_path, **transcribe_options)

    # Write outputs based on flags
    outputs_generated = []
    
    if generate_srt:
        print(f"Writing subtitles to {srt_file}...")
        transcriptions_to_srt(result['segments'], srt_file)
        outputs_generated.append(f"SRT: {srt_file}")
    
    if generate_txt:
        print(f"Writing text to {txt_file}...")
        transcriptions_to_txt(result['segments'], txt_file)
        outputs_generated.append(f"TXT: {txt_file}")
    
    if generate_lrc:
        print(f"Writing lyrics to {lrc_file}...")
        transcriptions_to_lrc(result['segments'], lrc_file, title=base_name)
        outputs_generated.append(f"LRC: {lrc_file}")

    # Clean up temp
    if temp_wav and os.path.exists(temp_wav):
        os.remove(temp_wav)

    # Calculate and print elapsed time
    elapsed_time = time.time() - start_time
    print(f"Conversion completed in {elapsed_time:.2f} seconds.")

    # Print summary
    print(f"\nDone! Generated {len(outputs_generated)} file(s):")
    for output in outputs_generated:
        print(f"  - {output}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert audio/video to SRT subtitles using Whisper."
    )
    parser.add_argument(
        'media_file',
        help='Path to input media file or directory (audio: WAV, M4A, MP3, AAC; video: MP4, MOV, AVI, MKV, FLV, WEBM, M4V, 3GP)'
    )
    parser.add_argument(
        '-s', '--srt',
        action='store_true',
        default=False,
        help='Generate SRT subtitle file'
    )
    parser.add_argument(
        '-t', '--text',
        action='store_true',
        default=False,
        help='Generate plain text file'
    )
    parser.add_argument(
        '-l', '--lrc',
        action='store_true',
        default=False,
        help='Generate LRC lyrics file'
    )
    parser.add_argument(
        '-o', '--output',
        nargs='?',
        const='output',
        default=None,
        help='Directory for output files (default: same as input file; use -o for ./output)'
    )
    parser.add_argument(
        '--large-v3',
        action='store_true',
        help='Use large-v3 model instead of base model'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process audio files in subdirectories recursively (only applies when input is a directory)'
    )
    parser.add_argument(
        '--lang', '--language',
        type=str,
        default=None,
        help='Language code for transcription (e.g., en, zh, es, fr). If not specified, auto-detect.'
    )
    batch_group = parser.add_mutually_exclusive_group()
    batch_group.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip media files that already have an SRT output (directory mode only)'
    )
    batch_group.add_argument(
        '--force',
        action='store_true',
        help='Reprocess all files, overwriting existing SRT (directory mode only; skips prompt)'
    )
    args = parser.parse_args()

    model_name = "large-v3" if args.large_v3 else "base"
    input_path = Path(args.media_file)
    
    # Determine which formats to generate
    # If no format flags specified, default to SRT only
    if not (args.srt or args.text or args.lrc):
        generate_srt = True
        generate_txt = False
        generate_lrc = False
    else:
        # Use specified flags
        generate_srt = args.srt
        generate_txt = args.text
        generate_lrc = args.lrc
    
    # Check if input is a file or directory
    if input_path.is_file():
        # Single file processing
        wav_to_subtitles(
            args.media_file,
            output_dir=args.output,
            generate_srt=generate_srt,
            generate_txt=generate_txt,
            generate_lrc=generate_lrc,
            model_name=model_name,
            language=args.lang
        )
    elif input_path.is_dir():
        # Directory processing
        print(f"Scanning directory: {args.media_file}")
        if args.recursive:
            print("(including subdirectories)")

        audio_files = find_audio_files(args.media_file, recursive=args.recursive)

        if not audio_files:
            print("No audio files found in the specified directory.")
            sys.exit(1)

        with_srt, without_srt = classify_media_files(audio_files, args.output)
        print_batch_classification(audio_files, with_srt, without_srt)

        files_to_process, skipped = resolve_files_to_process(
            audio_files,
            with_srt,
            without_srt,
            model_name,
            skip_existing=args.skip_existing,
            force=args.force,
        )

        if files_to_process is None:
            sys.exit(0)

        if not files_to_process:
            sys.exit(0)

        # Process each file
        print(f"\nStarting batch processing ({len(files_to_process)} file(s))...\n")
        successful = 0
        failed = 0

        for i, audio_file in enumerate(files_to_process, 1):
            print(f"[{i}/{len(files_to_process)}] Processing: {audio_file}")
            try:
                wav_to_subtitles(
                    audio_file,
                    output_dir=args.output,
                    generate_srt=generate_srt,
                    generate_txt=generate_txt,
                    generate_lrc=generate_lrc,
                    model_name=model_name,
                    language=args.lang
                )
                successful += 1
            except Exception as e:
                print(f"ERROR processing {audio_file}: {e}")
                failed += 1
            print()  # Empty line for readability

        # Summary
        print("Batch processing complete!")
        print(f"Successfully processed: {successful}")
        if skipped > 0:
            print(f"Skipped (existing SRT): {skipped}")
        if failed > 0:
            print(f"Failed: {failed}")
    else:
        print(f"Error: '{args.media_file}' is not a valid file or directory.")
        sys.exit(1)

if __name__ == '__main__':
    main()