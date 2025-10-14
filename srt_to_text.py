#!/usr/local/bin/python3
import os
import argparse
from pathlib import Path

def srt_to_text(srt_file, txt_file=None, output_dir=None):
    """
    Convert an SRT subtitle file to a plain text file with subtitle content only.
    
    Args:
        srt_file (str): Path to the input SRT file.
        txt_file (str, optional): Path to the output text file. If None, derived from srt_file.
        output_dir (str, optional): Directory to save the output file. If None, uses same dir as input.
    """
    # Verify SRT file exists
    if not os.path.exists(srt_file):
        raise FileNotFoundError(f"Input file {srt_file} not found")
    
    # Validate file extension
    if Path(srt_file).suffix.lower() != '.srt':
        raise ValueError("Input file must have .srt extension")
    
    # Set output file path if not provided
    if txt_file is None:
        srt_path = Path(srt_file)
        if output_dir:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            txt_file = str(output_path / srt_path.with_suffix('.txt').name)
        else:
            txt_file = str(srt_path.with_suffix('.txt'))
    
    print(f"Processing {srt_file}...")
    subtitles = []
    
    # Read SRT file
    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Skip sequence number
            if line.isdigit():
                i += 1
                # Skip timestamp line
                if i < len(lines) and '-->' in lines[i]:
                    i += 1
                    # Collect subtitle text until empty line or end
                    subtitle_text = []
                    while i < len(lines) and lines[i].strip():
                        subtitle_text.append(lines[i].strip())
                        i += 1
                    if subtitle_text:
                        subtitles.append(' '.join(subtitle_text))
                else:
                    i += 1
            else:
                i += 1
    
    # Write to text file
    with open(txt_file, 'w', encoding='utf-8') as f:
        for subtitle in subtitles:
            f.write(f"{subtitle}\n")
    
    print(f"Subtitles saved to {txt_file}")

def process_path(path):
    """
    Process either a single SRT file or all SRT files in a directory.
    
    Args:
        path (str): Path to an SRT file or directory containing SRT files.
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"Path {path} not found")
    
    if path_obj.is_file():
        # Process single file
        srt_to_text(str(path_obj))
    elif path_obj.is_dir():
        # Process all .srt files in directory
        srt_files = sorted(path_obj.glob('*.srt'))
        
        if not srt_files:
            print(f"No .srt files found in {path}")
            return
        
        # Create txt subdirectory for output
        output_dir = path_obj / 'txt'
        
        print(f"Found {len(srt_files)} SRT file(s) to process")
        print(f"Output directory: {output_dir}\n")
        
        for srt_file in srt_files:
            try:
                srt_to_text(str(srt_file), output_dir=str(output_dir))
            except Exception as e:
                print(f"Error processing {srt_file.name}: {e}")
        
        print(f"\nCompleted processing {len(srt_files)} file(s)")
    else:
        raise ValueError(f"{path} is neither a file nor a directory")

def main():
    """
    Parse command-line arguments and run the SRT to text conversion.
    """
    parser = argparse.ArgumentParser(description="Convert SRT subtitle file(s) to plain text.")
    parser.add_argument("path", help="Path to an SRT file or directory containing SRT files")
    args = parser.parse_args()
    
    process_path(args.path)

if __name__ == "__main__":
    main()