# Audio to MP3 Converter

This Python script converts various audio file formats (M4A, WAV, MP3, AAC, FLAC, OGG, WMA) to MP3 using the `pydub` library.

## Prerequisites

- Python 3.6 or higher
- FFmpeg installed on your system
- Required Python packages:
  - pydub

Install dependencies using pip:

```bash
pip install pydub
```

Ensure FFmpeg is installed:
- On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
- On macOS: `brew install ffmpeg`
- On Linux: `sudo apt-get install ffmpeg` (Ubuntu/Debian) or equivalent for your distribution

## Installation

1. Save the script as `convert_audio_to_mp3.py`
2. Ensure FFmpeg is in your system PATH
3. Install required Python packages as shown above

## Usage

Run the script from the command line, providing the path to the input audio file:

```bash
python convert_audio_to_mp3.py path/to/audio/file
```

The script will:
- Validate the input file
- Convert it to MP3
- Save the output in the same directory as the input file
- Display the processing time

### Supported Input Formats

- M4A
- WAV
- MP3
- AAC
- FLAC
- OGG
- WMA

### Examples

1. Convert an M4A file to MP3:
```bash
python convert_audio_to_mp3.py song.m4a
```
Output: `song.mp3` in the same directory

2. Convert a WAV file to MP3:
```bash
python convert_audio_to_mp3.py recording.wav
```
Output: `recording.mp3` in the same directory

3. Convert a file from a different directory:
```bash
python convert_audio_to_mp3.py /path/to/audio/podcast.flac
```
Output: `podcast.mp3` in `/path/to/audio/`

## Error Handling

The script includes error handling for:
- Non-existent input files
- Unsupported file formats
- Conversion errors (with FFmpeg debug output)

If an error occurs, the script will display an appropriate error message.

## Notes

- The output MP3 file will have the same base name as the input file
- Conversion time depends on file size and system performance
- Ensure sufficient disk space for the output file
- The script uses the `libmp3lame` codec for MP3 encoding