#!/usr/bin/env python3
"""
Interactive script to rename SRT files with better names based on content.

Usage:
  python srt_rename.py path/to/file.srt

The script will:
1. Read the SRT file content
2. Use LLM to suggest 5 filename options in format: yyyymmdd-<topic>
3. Display them interactively
4. Allow you to choose one or enter a custom name
5. Rename the file
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pysrt
from openai import OpenAI
import httpx
import re

# ---------------- CONFIG ----------------
MODEL_NAME = "openai/gpt-oss-20b"
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
TEMPERATURE = 0.3
MAX_CHARS = 2000  # Use first part for topic extraction
# ---------------------------------------


def read_srt_text(srt_path: Path, max_chars: int = MAX_CHARS) -> str:
    """Read SRT file and extract text content."""
    try:
        subs = pysrt.open(str(srt_path), encoding="utf-8")
        lines = []
        for sub in subs:
            text = sub.text.replace("\n", " ").strip()
            if text:
                lines.append(text)
        
        full_text = "\n".join(lines)
        
        # Return first part for topic extraction
        if len(full_text) > max_chars:
            return full_text[:max_chars] + "..."
        return full_text
    except Exception as e:
        print(f"Error reading SRT file: {e}")
        sys.exit(1)


def extract_date_from_filename(filename: str) -> str:
    """Try to extract date from filename, return yyyymmdd format."""
    # Try to find all 8-digit sequences and validate them as dates
    # This avoids matching phone numbers by validating the date
    
    # Find all potential 8-digit date patterns
    all_matches = re.finditer(r'(\d{4})(\d{2})(\d{2})', filename)
    
    for match in all_matches:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        
        # Validate it's a reasonable date (prioritize recent dates)
        if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            return f"{match.group(1)}{match.group(2)}{match.group(3)}"
        # Also accept dates from 1990-1999
        elif 1990 <= year <= 1999 and 1 <= month <= 12 and 1 <= day <= 31:
            return f"{match.group(1)}{match.group(2)}{match.group(3)}"
    
    # Try patterns with separators
    patterns = [
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}"),  # yyyy-mm-dd
        (r'(\d{4})/(\d{2})/(\d{2})', lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}"),  # yyyy/mm/dd
        (r'(\d{2})(\d{2})(\d{4})', lambda m: f"{m.group(3)}{m.group(1)}{m.group(2)}"),  # mmddyyyy
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                date_str = formatter(match)
                if len(date_str) == 8 and date_str.isdigit():
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    if 1990 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return date_str
            except:
                continue
    
    # If no date found, return None
    return None


def get_file_date(srt_path: Path) -> str:
    """Get date from filename or file creation time."""
    date_str = extract_date_from_filename(srt_path.name)
    if date_str:
        return date_str
    
    # Use file creation time (birthtime on macOS, ctime on other systems)
    stat_info = srt_path.stat()
    
    # Try to get birthtime (creation time) - available on macOS and some Linux systems
    if hasattr(stat_info, 'st_birthtime'):
        creation_time = stat_info.st_birthtime
    else:
        # Fallback to ctime (change time) which is closest to creation time on Linux
        # Note: ctime is actually metadata change time, not creation time, but it's the best we can do
        creation_time = stat_info.st_ctime
    
    return datetime.fromtimestamp(creation_time).strftime("%Y%m%d")


def check_api_available() -> bool:
    """Check if LM Studio API is available."""
    try:
        # Save original proxy env vars
        original_http_proxy = os.environ.pop('HTTP_PROXY', None)
        original_https_proxy = os.environ.pop('HTTPS_PROXY', None)
        original_all_proxy = os.environ.pop('ALL_PROXY', None)
        original_no_proxy = os.environ.get('NO_PROXY', '')
        
        # Set NO_PROXY to bypass proxy for localhost
        os.environ['NO_PROXY'] = '127.0.0.1,localhost'
        # Also clear proxy env vars for httpx
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        http_client = httpx.Client(timeout=5.0)
        
        # Try to connect to the models endpoint
        response = http_client.get(f"{LM_STUDIO_BASE_URL}/models")
        http_client.close()
        
        # Restore proxy env vars
        if original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        if original_all_proxy:
            os.environ['ALL_PROXY'] = original_all_proxy
        if original_no_proxy:
            os.environ['NO_PROXY'] = original_no_proxy
        else:
            os.environ.pop('NO_PROXY', None)
        
        return response.status_code == 200
    except Exception:
        # Restore proxy env vars
        if 'original_http_proxy' in locals() and original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if 'original_https_proxy' in locals() and original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        if 'original_all_proxy' in locals() and original_all_proxy:
            os.environ['ALL_PROXY'] = original_all_proxy
        if 'original_no_proxy' in locals():
            if original_no_proxy:
                os.environ['NO_PROXY'] = original_no_proxy
            else:
                os.environ.pop('NO_PROXY', None)
        return False


def suggest_filenames(text: str, date_str: str) -> list[str]:
    """Use LLM to suggest 5 filename options."""
    try:
        # Save original proxy env vars
        original_http_proxy = os.environ.pop('HTTP_PROXY', None)
        original_https_proxy = os.environ.pop('HTTPS_PROXY', None)
        original_all_proxy = os.environ.pop('ALL_PROXY', None)
        original_no_proxy = os.environ.get('NO_PROXY', '')
        
        # Set NO_PROXY to bypass proxy for localhost
        os.environ['NO_PROXY'] = '127.0.0.1,localhost'
        # Also clear proxy env vars for httpx
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        http_client = httpx.Client(timeout=30.0)
        
        client = OpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key="lm-studio",  # dummy key
            http_client=http_client
        )

        prompt = f"""Based on the following transcript excerpt, suggest 5 different filename options in the format: {date_str}-<topic>

Requirements:
- Each filename should be in format: {date_str}-<topic>
- The topic should be a concise summary of the main subject (20-40 characters max)
- Use lowercase letters, numbers, and hyphens only (no spaces, no special characters)
- Make topics descriptive but brief
- Topics should be different from each other
- Return ONLY the 5 filenames, one per line, no numbering, no explanations

Transcript excerpt:
{text}

Return format (example):
{date_str}-doctor-appointment-discussion
{date_str}-medical-checkup-followup
{date_str}-hospital-visit-inquiry
{date_str}-healthcare-appointment-questions
{date_str}-doctor-visit-conversation
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that suggests concise, descriptive filenames."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            timeout=30.0
        )

        result = response.choices[0].message.content.strip()
        http_client.close()
        
        # Restore proxy env vars
        if original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        if original_all_proxy:
            os.environ['ALL_PROXY'] = original_all_proxy
        if original_no_proxy:
            os.environ['NO_PROXY'] = original_no_proxy
        else:
            os.environ.pop('NO_PROXY', None)
        
        # Parse the suggestions
        suggestions = []
        for line in result.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Extract filename if LLM added extra text
                if date_str in line:
                    # Extract the part after date
                    parts = line.split(date_str + '-', 1)
                    if len(parts) > 1:
                        topic = parts[1].split()[0]  # Take first word/topic
                        suggestions.append(f"{date_str}-{topic}")
                    else:
                        suggestions.append(line)
                elif line.startswith(date_str):
                    suggestions.append(line)
        
        # Ensure we have exactly 5 suggestions
        while len(suggestions) < 5:
            suggestions.append(f"{date_str}-topic-{len(suggestions) + 1}")
        
        return suggestions[:5]
        
    except Exception as e:
        if 'http_client' in locals():
            http_client.close()
        # Restore proxy env vars
        if 'original_http_proxy' in locals() and original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if 'original_https_proxy' in locals() and original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        if 'original_all_proxy' in locals() and original_all_proxy:
            os.environ['ALL_PROXY'] = original_all_proxy
        if 'original_no_proxy' in locals():
            if original_no_proxy:
                os.environ['NO_PROXY'] = original_no_proxy
            else:
                os.environ.pop('NO_PROXY', None)
        raise


def sanitize_filename(name: str) -> str:
    """Sanitize filename to be filesystem-safe."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '-', name)
    name = re.sub(r'\s+', '-', name)  # Replace spaces with hyphens
    name = name.strip('.-')  # Remove leading/trailing dots and hyphens
    return name


def interactive_rename(srt_path: Path, suggestions: list[str]) -> str:
    """Interactive menu to select or enter filename."""
    print("\n" + "="*60)
    print("📝 Suggested Filenames:")
    print("="*60)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}.srt")
    
    print(f"\n  0. Enter custom filename")
    print(f"  q. Quit without renaming")
    print("="*60)
    
    while True:
        choice = input("\nSelect an option (1-5, 0, or q): ").strip().lower()
        
        if choice == 'q':
            print("Cancelled. File not renamed.")
            return None
        
        if choice == '0':
            custom_name = input(f"Enter custom filename (without .srt extension): ").strip()
            if custom_name:
                # Ensure it starts with date
                if not custom_name.startswith(suggestions[0].split('-')[0]):
                    date_prefix = suggestions[0].split('-')[0]
                    custom_name = f"{date_prefix}-{custom_name}"
                custom_name = sanitize_filename(custom_name)
                return f"{custom_name}.srt"
            else:
                print("Invalid input. Please try again.")
                continue
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suggestions):
                return f"{suggestions[idx]}.srt"
            else:
                print("Invalid choice. Please select 1-5, 0, or q.")
        except ValueError:
            print("Invalid input. Please enter a number, 0, or q.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python srt_rename.py path/to/file.srt")
        sys.exit(1)

    srt_path = Path(sys.argv[1])

    if not srt_path.exists() or srt_path.suffix.lower() != ".srt":
        print("Error: input must be an existing .srt file")
        sys.exit(1)

    print(f"📄 Reading: {srt_path}")
    
    # Check if LM Studio API is available
    print("🔍 Checking if LM Studio API is available...")
    if not check_api_available():
        print(f"\n❌ Error: LM Studio API is not available at {LM_STUDIO_BASE_URL}")
        print("\n💡 Reminder:")
        print("   Please make sure LM Studio is running and the model is loaded.")
        print(f"   The API should be accessible at: {LM_STUDIO_BASE_URL}")
        print(f"\n   Steps to fix:")
        print(f"   1. Open LM Studio")
        print(f"   2. Load the model: {MODEL_NAME}")
        print(f"   3. Start the local server (check the port matches: {LM_STUDIO_BASE_URL})")
        print(f"   4. Run this script again")
        sys.exit(1)

    # Read SRT content
    text = read_srt_text(srt_path)
    
    if not text.strip():
        print("⚠️  Warning: No text found in SRT file")
        sys.exit(1)

    # Get date for filename
    date_str = get_file_date(srt_path)
    print(f"📅 Using date: {date_str}")

    # Get filename suggestions from LLM
    print("🧠 Generating filename suggestions...")
    try:
        suggestions = suggest_filenames(text, date_str)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error generating suggestions: {e}")
        print("\n💡 Reminder:")
        print("   If the API connection failed, please check:")
        print("   1. LM Studio is running")
        print(f"   2. The model ({MODEL_NAME}) is loaded and server is started")
        print(f"   3. The API is accessible at: {LM_STUDIO_BASE_URL}")
        sys.exit(1)

    # Interactive selection
    new_filename = interactive_rename(srt_path, suggestions)
    
    if new_filename is None:
        sys.exit(0)

    # Rename the file
    new_path = srt_path.parent / new_filename
    
    if new_path.exists():
        print(f"\n⚠️  Warning: {new_filename} already exists!")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Cancelled. File not renamed.")
            sys.exit(0)
    
    try:
        srt_path.rename(new_path)
        print(f"\n✅ File renamed successfully!")
        print(f"   Old: {srt_path.name}")
        print(f"   New: {new_filename}")
    except Exception as e:
        print(f"\n❌ Error renaming file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
