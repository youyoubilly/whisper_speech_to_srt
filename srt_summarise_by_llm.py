#!/usr/bin/env python3
"""
Usage:
  python srt_to_summary.py path/to/file.srt

Output:
  path/to/file.summary.md
"""

import sys
import os
from pathlib import Path
import pysrt
from openai import OpenAI
import httpx

# ---------------- CONFIG ----------------
MODEL_NAME = "openai/gpt-oss-20b"
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
TEMPERATURE = 0.3
MAX_CHARS = 12000   # safety limit for very large SRTs
# ---------------------------------------


def read_srt_text(srt_path: Path) -> str:
    subs = pysrt.open(str(srt_path), encoding="utf-8")

    lines = []
    for sub in subs:
        text = sub.text.replace("\n", " ").strip()
        if text:
            lines.append(text)

    full_text = "\n".join(lines)

    # prevent sending extremely large payloads
    if len(full_text) > MAX_CHARS:
        full_text = full_text[:MAX_CHARS] + "\n\n[TRUNCATED]"

    return full_text


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


def summarize(text: str) -> str:
    try:
        # Create HTTP client that bypasses proxy for localhost
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

        prompt = f"""
Summarize the following transcript into a clean Markdown document.

Requirements:
- Start with a clear title
- Use sections with headings
- Bullet points where appropriate
- Focus on key ideas and conclusions
- Do NOT mention timestamps or subtitles
- Do NOT mention that this comes from an SRT file

Transcript:
{text}
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise technical summarizer."},
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
        return result
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
        raise  # Re-raise the exception to be handled by main()


def main():
    if len(sys.argv) != 2:
        print("Usage: python srt_to_summary.py path/to/file.srt")
        sys.exit(1)

    srt_path = Path(sys.argv[1])

    if not srt_path.exists() or srt_path.suffix.lower() != ".srt":
        print("Error: input must be an existing .srt file")
        sys.exit(1)

    print(f"📄 Reading: {srt_path}")
    text = read_srt_text(srt_path)
    
    if not text.strip():
        print("⚠️  Warning: No text found in SRT file")
        sys.exit(1)

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

    print("🧠 Summarizing with openai/gpt-oss-20b...")
    try:
        summary_md = summarize(text)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during summarization: {e}")
        print("\n💡 Reminder:")
        print("   If the API connection failed, please check:")
        print("   1. LM Studio is running")
        print(f"   2. The model ({MODEL_NAME}) is loaded and server is started")
        print(f"   3. The API is accessible at: {LM_STUDIO_BASE_URL}")
        sys.exit(1)

    output_path = srt_path.with_suffix(".summary.md")
    output_path.write_text(summary_md, encoding="utf-8")

    print(f"✅ Summary written to: {output_path}")


if __name__ == "__main__":
    main()
