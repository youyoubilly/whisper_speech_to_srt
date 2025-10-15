#!/usr/local/bin/python3
import os
import argparse
from pathlib import Path
import re

def srt_timestamp_to_lrc(srt_time):
    """
    Convert SRT timestamp (HH:MM:SS,mmm) to LRC format ([MM:SS.xx]).
    
    Args:
        srt_time (str): Timestamp in SRT format (e.g., "00:01:23,456")
    
    Returns:
        str: Timestamp in LRC format (e.g., "[01:23.45]")
    """
    # Parse SRT timestamp: HH:MM:SS,mmm
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', srt_time.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp format: {srt_time}")
    
    hours, minutes, seconds, milliseconds = match.groups()
    
    # Convert to total minutes and seconds
    total_minutes = int(hours) * 60 + int(minutes)
    total_seconds = int(seconds)
    centiseconds = int(milliseconds) // 10  # Convert milliseconds to centiseconds
    
    # Format as LRC: [MM:SS.xx]
    return f"[{total_minutes:02d}:{total_seconds:02d}.{centiseconds:02d}]"

def srt_to_lrc(srt_file, lrc_file=None, output_dir=None):
    """
    Convert an SRT subtitle file to LRC (lyrics) format.
    
    Args:
        srt_file (str): Path to the input SRT file.
        lrc_file (str, optional): Path to the output LRC file. If None, derived from srt_file.
        output_dir (str, optional): Directory to save the output file. If None, uses same dir as input.
    """
    # Verify SRT file exists
    if not os.path.exists(srt_file):
        raise FileNotFoundError(f"Input file {srt_file} not found")
    
    # Validate file extension
    if Path(srt_file).suffix.lower() != '.srt':
        raise ValueError("Input file must have .srt extension")
    
    # Set output file path if not provided
    if lrc_file is None:
        srt_path = Path(srt_file)
        if output_dir:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            lrc_file = str(output_path / srt_path.with_suffix('.lrc').name)
        else:
            lrc_file = str(srt_path.with_suffix('.lrc'))
    
    print(f"Processing {srt_file}...")
    lrc_lines = []
    
    # Read SRT file
    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Look for sequence number
            if line.isdigit():
                i += 1
                # Look for timestamp line
                if i < len(lines) and '-->' in lines[i]:
                    timestamp_line = lines[i].strip()
                    # Extract start timestamp (before -->)
                    start_time = timestamp_line.split('-->')[0].strip()
                    
                    i += 1
                    # Collect subtitle text until empty line or end
                    subtitle_text = []
                    while i < len(lines) and lines[i].strip():
                        subtitle_text.append(lines[i].strip())
                        i += 1
                    
                    if subtitle_text:
                        # Convert timestamp and format as LRC
                        try:
                            lrc_timestamp = srt_timestamp_to_lrc(start_time)
                            text = ' '.join(subtitle_text)
                            lrc_lines.append(f"{lrc_timestamp}{text}")
                        except ValueError as e:
                            print(f"Warning: {e}")
                else:
                    i += 1
            else:
                i += 1
    
    # Extract filename without extension for title
    file_stem = Path(srt_file).stem
    
    # Write to LRC file with metadata headers
    with open(lrc_file, 'w', encoding='utf-8') as f:
        # Write LRC metadata headers
        f.write(f"[ti:{file_stem}]\n")
        f.write("[ar:]\n")
        f.write("[al:]\n")
        f.write("[by:Whisper STT]\n")
        f.write("[offset:0]\n")
        f.write("\n")
        
        # Write lyrics with timestamps
        for line in lrc_lines:
            f.write(f"{line}\n")
    
    print(f"LRC file saved to {lrc_file}")

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
        srt_to_lrc(str(path_obj))
    elif path_obj.is_dir():
        # Process all .srt files in directory
        srt_files = sorted(path_obj.glob('*.srt'))
        
        if not srt_files:
            print(f"No .srt files found in {path}")
            return
        
        # Create lrc subdirectory for output
        output_dir = path_obj / 'lrc'
        
        print(f"Found {len(srt_files)} SRT file(s) to process")
        print(f"Output directory: {output_dir}\n")
        
        for srt_file in srt_files:
            try:
                srt_to_lrc(str(srt_file), output_dir=str(output_dir))
            except Exception as e:
                print(f"Error processing {srt_file.name}: {e}")
        
        print(f"\nCompleted processing {len(srt_files)} file(s)")
    else:
        raise ValueError(f"{path} is neither a file nor a directory")

def main():
    """
    Parse command-line arguments and run the SRT to LRC conversion.
    """
    parser = argparse.ArgumentParser(
        description="Convert SRT subtitle file(s) to LRC (lyrics) format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.srt                    # Convert single file
  %(prog)s /path/to/srt/directory       # Convert all SRT files in directory
        """
    )
    parser.add_argument("path", help="Path to an SRT file or directory containing SRT files")
    args = parser.parse_args()
    
    try:
        process_path(args.path)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

