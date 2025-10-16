import sys
import os
from pydub import AudioSegment
import time

def split_audio_channels(input_file):
    start_time = time.time()
    
    # Validate input file
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist")
        return
    
    # Supported input formats
    supported_formats = {'.m4a', '.wav', '.mp3', '.aac', '.flac', '.ogg', '.wma'}
    file_ext = os.path.splitext(input_file)[1].lower()
    
    if file_ext not in supported_formats:
        print(f"Error: Unsupported input format. Supported formats: {', '.join(supported_formats)}")
        return
    
    try:
        # First, try to auto-detect format by letting ffmpeg handle it
        try:
            audio = AudioSegment.from_file(input_file)
            print(f"Auto-detected format successfully")
        except Exception as auto_detect_error:
            print(f"Auto-detection failed, trying with file extension hint...")
            # Fallback: Load audio file with appropriate format based on extension
            format_map = {
                '.m4a': 'm4a',
                '.wav': 'wav',
                '.mp3': 'mp3',
                '.aac': 'adts',
                '.flac': 'flac',
                '.ogg': 'ogg',
                '.wma': 'wma'
            }
            
            audio_format = format_map.get(file_ext, file_ext[1:])
            audio = AudioSegment.from_file(input_file, format=audio_format)
        
        # Check channel count
        channel_count = audio.channels
        print(f"Audio channels detected: {channel_count}")
        
        if channel_count == 1:
            print("Warning: Audio file is mono (single channel). Skipping processing.")
            print("This script only processes stereo or multi-channel audio files.")
            return
        
        # Split into separate channels
        print(f"Splitting audio into {channel_count} separate channels...")
        channels = audio.split_to_mono()
        
        # Prepare output file paths
        output_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Export left channel (first channel)
        left_output = os.path.join(output_dir, f"{base_name}_L.mp3")
        channels[0].export(left_output, format="mp3", codec="libmp3lame")
        print(f"Left channel saved to: {left_output}")
        
        # Export right channel (second channel)
        right_output = os.path.join(output_dir, f"{base_name}_R.mp3")
        channels[1].export(right_output, format="mp3", codec="libmp3lame")
        print(f"Right channel saved to: {right_output}")
        
        # If there are more than 2 channels, inform the user
        if channel_count > 2:
            print(f"Note: Audio has {channel_count} channels. Only left (channel 1) and right (channel 2) were exported.")
        
        print("Successfully split audio channels!")
        
        # Calculate and print processing time
        end_time = time.time()
        print(f"Processing time: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during channel splitting: {str(e)}")
        # Run ffmpeg directly for debugging
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-i", input_file, "-f", "null", "-"],
            capture_output=True, text=True
        )
        print("ffmpeg stderr:", result.stderr)

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python split_audio_channels.py [path-to-audio-file]")
        print("\nThis script splits stereo audio files into separate left and right channel MP3 files.")
        print("Output files will be named: <filename>_L.mp3 and <filename>_R.mp3")
        sys.exit(1)
    
    input_file = sys.argv[1]
    split_audio_channels(input_file)

if __name__ == "__main__":
    main()

