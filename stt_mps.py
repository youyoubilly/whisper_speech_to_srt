#!/usr/bin/env python3
import os, sys, argparse, subprocess, time
from pathlib import Path

# -------------------------
# Utilities
# -------------------------
def transcriptions_to_srt(segments, srt_file):
    with open(srt_file, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start = seg['start']; end = seg['end']; text = seg['text'].strip()
            start_srt = f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{start%60:06.3f}".replace('.', ',')
            end_srt   = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{end%60:06.3f}".replace('.', ',')
            speaker = seg.get('speaker')
            line = f"{speaker}: {text}" if speaker else text
            f.write(f"{i}\n{start_srt} --> {end_srt}\n{line}\n\n")

def transcriptions_to_txt(segments, txt_file):
    with open(txt_file, 'w', encoding='utf-8') as f:
        for seg in segments:
            speaker = seg.get('speaker')
            text = seg['text'].strip()
            f.write(f"{speaker}: {text}\n" if speaker else f"{text}\n")

def transcriptions_to_lrc(segments, lrc_file, title=""):
    """
    Generate LRC (lyrics) file from transcription segments.
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
        for seg in segments:
            start_time = seg['start']
            # Convert to total minutes and seconds
            total_minutes = int(start_time // 60)
            total_seconds = int(start_time % 60)
            # Get centiseconds (hundredths of a second)
            centiseconds = int((start_time % 1) * 100)
            
            # Format as LRC: [MM:SS.xx]text
            speaker = seg.get('speaker')
            text = seg['text'].strip()
            line = f"{speaker}: {text}" if speaker else text
            lrc_timestamp = f"[{total_minutes:02d}:{total_seconds:02d}.{centiseconds:02d}]"
            f.write(f"{lrc_timestamp}{line}\n")

def find_audio_files(directory, recursive=False):
    supported = {'.wav', '.m4a', '.mp3', '.mp4', '.flac', '.aac', '.ogg'}
    p = Path(directory); found = []
    it = p.rglob("*") if recursive else p.glob("*")
    for item in it:
        if item.is_file() and item.suffix.lower() in supported:
            found.append(str(item))
    return sorted(found)

def convert_to_wav(input_file, wav_path):
    cmd = ['ffmpeg','-y','-i', input_file,'-ac','1','-ar','16000', wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def to_overlap(a0,a1,b0,b1):
    return max(0.0, min(a1,b1) - max(a0,b0))

# -------------------------
# OpenCC optional
# -------------------------
def get_opencc(profile):
    if profile in (None, "", "none"):
        return None
    try:
        from opencc import OpenCC
        return OpenCC(profile)
    except Exception as e:
        print(f"[WARN] OpenCC not available: {e}")
        return None

# -------------------------
# Diarization optional via WhisperX
# -------------------------
def diarize_segments(audio_path, max_speakers=0, hf_token_env="HF_TOKEN", device="mps"):
    try:
        import whisperx, os
        token = os.environ.get(hf_token_env, None)
        if not token:
            print("[WARN] HF token not set. Set HF_TOKEN to use --diarize.")
            return None
        pipe = whisperx.DiarizationPipeline(use_auth_token=token, device=device)
        diar = pipe(audio_path, num_speakers=max_speakers if max_speakers>0 else None)
        # diar is list of dicts: {'start','end','speaker'}
        # Normalize speaker names to Speaker 1..N in order of appearance
        speaker_map = {}
        next_id = 1
        norm = []
        for d in diar:
            spk = d['speaker']
            if spk not in speaker_map:
                speaker_map[spk] = f"Speaker {next_id}"
                next_id += 1
            norm.append({"start": float(d['start']), "end": float(d['end']), "speaker": speaker_map[spk]})
        norm.sort(key=lambda x: x['start'])
        return norm
    except ImportError:
        print("[WARN] whisperx not installed. Skip diarization.")
        return None
    except Exception as e:
        print(f"[WARN] Diarization error: {e}")
        return None

# -------------------------
# STT with faster-whisper
# -------------------------
def transcribe_file(
    media_file,
    output_dir=None,
    generate_txt=False,
    generate_lrc=True,
    model_name="large-v3",
    device="mps",
    compute_type="float16",
    language="auto",
    vad=True,
    beam_size=5,
    opencc_profile="none",
    diarize=False,
    max_speakers=0
):
    start_time = time.time()
    print(f"\n{'='*80}")
    print(f"[STEP 1/6] Checking input file...")
    print(f"  Input: {media_file}")

    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Input file {media_file} not found")

    ext = Path(media_file).suffix.lower()
    valid_audio = {'.wav', '.m4a', '.mp3', '.flac', '.aac', '.ogg'}
    temp_wav = None

    if output_dir is None:
        output_dir = Path(media_file).parent
    else:
        output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {output_dir}")

    print(f"\n[STEP 2/6] Preparing audio file...")
    if ext == '.mp4' or ext not in valid_audio:
        base = Path(media_file).stem
        temp_wav = str(output_dir / f"{base}_temp.wav")
        print(f"  Converting {media_file} to WAV...")
        convert_to_wav(media_file, temp_wav)
        audio_path = temp_wav
        print(f"  ✓ Conversion complete")
    else:
        audio_path = media_file
        print(f"  ✓ Audio file ready (format: {ext})")

    base_name = Path(media_file).stem
    srt_file = str(output_dir / f"{base_name}.srt")
    txt_file = str(output_dir / f"{base_name}.txt")
    lrc_file = str(output_dir / f"{base_name}.lrc")

    # Load model
    from faster_whisper import WhisperModel
    print(f"\n[STEP 3/6] Loading Whisper model...")
    print(f"  Model: {model_name}")
    print(f"  Device: {device}")
    print(f"  Compute type: {compute_type}")
    print(f"  This may take a while on first run (downloading model)...")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print(f"  ✓ Model loaded successfully")

    lang_code = None if language in (None, "", "auto") else language
    cc = get_opencc(opencc_profile)

    # Optional diarization
    dia_segments = None
    if diarize:
        print(f"\n[STEP 4/6] Running speaker diarization...")
        print(f"  Max speakers: {max_speakers if max_speakers > 0 else 'auto-detect'}")
        dia_segments = diarize_segments(audio_path, max_speakers=max_speakers, device=("cuda" if device=="cuda" else "mps"))
        if dia_segments:
            print(f"  ✓ Diarization complete ({len(set(d['speaker'] for d in dia_segments))} speakers detected)")
    else:
        print(f"\n[STEP 4/6] Skipping diarization...")

    print(f"\n[STEP 5/6] Transcribing audio...")
    print(f"  Language: {language}")
    print(f"  VAD enabled: {vad}")
    print(f"  Beam size: {beam_size}")
    print(f"  Processing... (this may take several minutes)")
    seg_iter, info = model.transcribe(
        audio_path,
        language=lang_code,
        vad_filter=vad,
        vad_parameters=dict(min_silence_duration_ms=300),
        beam_size=beam_size,
        word_timestamps=False,
        task="transcribe"
    )

    segments = []
    segment_count = 0
    for s in seg_iter:
        text = s.text
        if cc: text = cc.convert(text)
        seg = {"start": s.start, "end": s.end, "text": text}
        segments.append(seg)
        segment_count += 1
        if segment_count % 10 == 0:
            print(f"  Processing segments... ({segment_count} segments so far)")
    print(f"  ✓ Transcription complete ({len(segments)} segments)")

    # If diarized, assign speaker with max overlap
    if dia_segments:
        print(f"  Assigning speakers to segments...")
        labeled = []
        for seg in segments:
            best_spk, best_ov = None, 0.0
            for d in dia_segments:
                ov = to_overlap(seg["start"], seg["end"], d["start"], d["end"])
                if ov > best_ov:
                    best_ov = ov; best_spk = d["speaker"]
            seg["speaker"] = best_spk or "Speaker ?"
            labeled.append(seg)
        segments = labeled
        print(f"  ✓ Speaker labels assigned")

    print(f"\n[STEP 6/6] Writing output files...")
    print(f"  Writing SRT: {srt_file}")
    transcriptions_to_srt(segments, srt_file)
    if generate_txt:
        print(f"  Writing TXT: {txt_file}")
        transcriptions_to_txt(segments, txt_file)
    if generate_lrc:
        print(f"  Writing LRC: {lrc_file}")
        transcriptions_to_lrc(segments, lrc_file, title=base_name)
    print(f"  ✓ Output files written")

    if temp_wav and os.path.exists(temp_wav):
        print(f"  Cleaning up temporary files...")
        os.remove(temp_wav)

    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"✓ COMPLETED in {elapsed:.2f}s")
    print(f"  SRT: {srt_file}")
    if generate_txt:
        print(f"  TXT: {txt_file}")
    if generate_lrc:
        print(f"  LRC: {lrc_file}")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(description="Batch STT to SRT/TXT/LRC with faster-whisper on Apple Silicon. Optional diarization.")
    parser.add_argument('media_path', help='Path to input file or directory')
    parser.add_argument('-t','--text', action='store_true', help='Also generate plain text output')
    parser.add_argument('-l','--lrc', action='store_true', default=True, help='Generate LRC lyrics file (enabled by default, use --no-lrc to disable)')
    parser.add_argument('--no-lrc', action='store_false', dest='lrc', help='Disable LRC lyrics file generation')
    parser.add_argument('-o','--output', nargs='?', const='output', default=None, help='Output directory (default: alongside input; use -o for ./output)')
    parser.add_argument('--model', default='/Users/billywang/Downloads/hf', help='Whisper model name or local path (default: /Users/billywang/Downloads/hf)')
    parser.add_argument('--device', default='cpu', help='Device: cpu (faster-whisper does not support mps)')
    parser.add_argument('--compute-type', default='auto', help='auto | float32 | int8 | int16 (default: auto - float32 for cpu)')
    parser.add_argument('--language', default='yue', help='Language code: yue (Cantonese) | zh | en | auto')
    parser.add_argument('--no-vad', action='store_true', help='Disable VAD')
    parser.add_argument('--beam-size', type=int, default=5, help='Beam size')
    parser.add_argument('-r','--recursive', action='store_true', help='If input is a directory, recurse into subfolders')
    parser.add_argument('--opencc', default='none', help='OpenCC profile: none | s2t | s2hk')
    parser.add_argument('--diarize', action='store_true', help='Enable speaker diarization via WhisperX + pyannote (needs HF_TOKEN)')
    parser.add_argument('--speakers', type=int, default=0, help='Force speaker count (0 = auto)')
    parser.add_argument('--offline', action='store_true', help='Force offline mode (no internet connection)')

    args = parser.parse_args()
    
    # Auto-detect compute type based on device
    if args.compute_type == 'auto':
        args.compute_type = 'float32' if args.device == 'cpu' else 'float16'
    
    # Set offline mode if requested
    if args.offline:
        os.environ['HF_HUB_OFFLINE'] = '1'
    input_path = Path(args.media_path)

    if input_path.is_file():
        transcribe_file(
            str(input_path),
            output_dir=args.output,
            generate_txt=args.text,
            generate_lrc=args.lrc,
            model_name=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            vad=not args.no_vad,
            beam_size=args.beam_size,
            opencc_profile=args.opencc,
            diarize=args.diarize,
            max_speakers=args.speakers
        )
    elif input_path.is_dir():
        files = find_audio_files(str(input_path), recursive=args.recursive)
        if not files:
            print("No audio files found.")
            sys.exit(1)
        print(f"Found {len(files)} file(s).")
        for i, fpath in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {fpath}")
            try:
                transcribe_file(
                    fpath,
                    output_dir=args.output,
                    generate_txt=args.text,
                    generate_lrc=args.lrc,
                    model_name=args.model,
                    device=args.device,
                    compute_type=args.compute_type,
                    language=args.language,
                    vad=not args.no_vad,
                    beam_size=args.beam_size,
                    opencc_profile=args.opencc,
                    diarize=args.diarize,
                    max_speakers=args.speakers
                )
            except Exception as e:
                print(f"[ERROR] {fpath}: {e}")
    else:
        print("Invalid path.")
        sys.exit(1)

if __name__ == '__main__':
    main()
