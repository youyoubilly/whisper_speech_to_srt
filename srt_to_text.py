#!/usr/local/bin/python3
import os
import argparse
from pathlib import Path

def srt_to_text(srt_file, txt_file=None):
    """
    Convert an SRT subtitle file to a plain text file with subtitle content only.
    
    Args:
        srt_file (str): Path to the input SRT file.
        txt_file (str, optional): Path to the output text file. If None, derived from srt_file.
    """
    # Verify SRT file exists
    if not os.path.exists(srt_file):
        raise FileNotFoundError(f"Input file {srt_file} not found")
    
    # Validate file extension
    if Path(srt_file).suffix.lower() != '.srt':
        raise ValueError("Input file must have .srt extension")
    
    # Set output file path if not provided
    if txt_file is None:
        txt_file = str(Path(srt_file).with_suffix('.txt'))
    
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

def main():
    """
    Parse command-line arguments and run the SRT to text conversion.
    """
    parser = argparse.ArgumentParser(description="Convert an SRT subtitle file to plain text.")
    parser.add_argument("srt_file", help="Path to the input SRT file")
    args = parser.parse_args()
    
    srt_to_text(args.srt_file)

if __name__ == "__main__":
    main()