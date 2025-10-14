# Whisper Speech to SRT

Convert audio/video files to SRT subtitles using OpenAI's Whisper model.

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process single audio file
python whisper_speech_to_srt.py audio.mp3

# Process entire folder
python whisper_speech_to_srt.py /path/to/folder

# Process folder including subfolders
python whisper_speech_to_srt.py -r /path/to/folder
```

### Options

| Flag | Description |
|------|-------------|
| `-t, --text` | Generate plain text file (without timestamps) |
| `-o, --output` | Specify output directory (default: same as input) |
| `--large-v3` | Use large-v3 model instead of base model |
| `-r, --recursive` | Process subfolders (for directory input only) |

### Advanced Examples

```bash
# Use large-v3 model for better accuracy
python whisper_speech_to_srt.py --large-v3 audio.mp3

# Generate both SRT and TXT files
python whisper_speech_to_srt.py -t audio.mp3

# Save outputs to specific directory
python whisper_speech_to_srt.py -o output_folder audio.mp3

# Process folder recursively with large-v3 model and text output
python whisper_speech_to_srt.py --large-v3 -t -r /path/to/folder
```

## Supported Formats

- Audio: `.wav`, `.m4a`, `.mp3`
- Video: `.mp4` (extracts audio automatically)

## Features

- **Single file or batch processing**: Process one file or entire folders
- **Recursive scanning**: Include subfolders with `-r` flag
- **Confirmation prompt**: Lists all files before processing folders
- **Progress tracking**: Shows current/total progress for batch operations
- **Error handling**: Continues processing remaining files if one fails
- **Multiple models**: Choose between base (fast) or large-v3 (accurate)
- **Flexible output**: Generate SRT subtitles and/or plain text transcripts

## Notes

- When processing folders, the script will list all found files and ask for confirmation
- By default, output files are saved in the same directory as input files
- Use `-o` flag to organize outputs in a separate directory
- The base model is faster but less accurate; large-v3 is slower but more accurate

