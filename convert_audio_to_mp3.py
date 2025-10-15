import sys
import os
from pydub import AudioSegment
import time

def convert_to_mp3(input_file):
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
        
        # Prepare output file path
        output_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.mp3")
        
        # Export to MP3
        audio.export(output_file, format="mp3", codec="libmp3lame")
        
        print(f"Successfully converted to {output_file}")
        
        # Calculate and print processing time
        end_time = time.time()
        print(f"Processing time: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
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
        print("Usage: python convert_audio_to_mp3.py [path-to-audio-file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    convert_to_mp3(input_file)

if __name__ == "__main__":
    main()