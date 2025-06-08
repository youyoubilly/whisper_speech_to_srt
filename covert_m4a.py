import sys
import os
from pydub import AudioSegment
import time

def convert_m4a(input_file, output_format="mp3"):
    start_time = time.time()
    
    # Validate input file
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist")
        return
    
    if not input_file.lower().endswith('.m4a'):
        print("Error: Input file must be an M4A file")
        return
    
    try:
        # Load M4A file with explicit codec
        audio = AudioSegment.from_file(input_file, format="m4a", codec="aac")
        
        # Prepare output file path
        output_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.{output_format}")
        
        # Export to specified format with appropriate codec
        if output_format == "mp3":
            audio.export(output_file, format="mp3", codec="libmp3lame")
        else:  # wav
            audio.export(output_file, format="wav")
            
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
        print("Usage: python convert_m4a.py [path-to-m4a-file] [-wav]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_format = "mp3"
    
    # Check for -wav flag
    if len(sys.argv) > 2 and sys.argv[2].lower() == "-wav":
        output_format = "wav"
    
    convert_m4a(input_file, output_format)

if __name__ == "__main__":
    main()