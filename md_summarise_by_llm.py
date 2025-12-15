#!/usr/bin/env python3
"""
Usage:
  python md_summarise_by_llm.py path/to/file.md

Output:
  path/to/file.summary.md
"""

import sys
import os
import atexit
from pathlib import Path
from openai import OpenAI
import httpx

# ---------------- CONFIG ----------------
MODEL_NAME = "openai/gpt-oss-20b"
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
TEMPERATURE = 0.3
MAX_CHARS_SAFE = 8000   # Safe character limit to avoid hitting token limits
TEMP_FILE_PREFIX = "._temp_"  # Prefix for temporary files
MAX_DEPTH = 3  # Maximum recursion depth (default: 3 levels)
# ---------------------------------------

# Global list to track temporary files for cleanup
_temp_files = []


# Custom exceptions
class TokenLimitExceeded(Exception):
    """Raised when the text exceeds the LLM token limit."""
    pass


class MaxDepthExceeded(Exception):
    """Raised when maximum recursion depth is reached."""
    pass


def read_md_text(md_path: Path, max_chars: int = None) -> str:
    """Read markdown file and extract text content."""
    if max_chars is None:
        max_chars = MAX_CHARS_SAFE * 2  # Allow larger initial read
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read markdown file: {e}")
    
    # Prevent sending extremely large payloads
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[TRUNCATED]"
    
    return full_text


def split_md_file(md_path: Path) -> tuple[Path, Path]:
    """Split a markdown file into two parts by line count.
    
    Returns:
        tuple[Path, Path]: Paths to the two temporary markdown files
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise RuntimeError(f"Failed to read markdown file for splitting: {e}")
    
    if len(lines) < 2:
        raise ValueError("Cannot split markdown file with less than 2 lines")
    
    # Split in half (first half gets extra one if odd number)
    mid_point = (len(lines) + 1) // 2
    first_half = lines[:mid_point]
    second_half = lines[mid_point:]
    
    # Create temporary file paths
    base_name = md_path.stem
    parent_dir = md_path.parent
    temp_file1 = parent_dir / f"{TEMP_FILE_PREFIX}{base_name}_part1.md"
    temp_file2 = parent_dir / f"{TEMP_FILE_PREFIX}{base_name}_part2.md"
    
    # Write first half
    try:
        with open(temp_file1, 'w', encoding='utf-8') as f:
            f.writelines(first_half)
    except Exception as e:
        raise RuntimeError(f"Failed to write temporary file: {e}")
    
    # Write second half
    try:
        with open(temp_file2, 'w', encoding='utf-8') as f:
            f.writelines(second_half)
    except Exception as e:
        raise RuntimeError(f"Failed to write temporary file: {e}")
    
    # Track temporary files for cleanup
    _temp_files.append(temp_file1)
    _temp_files.append(temp_file2)
    
    return temp_file1, temp_file2


def cleanup_temp_files():
    """Remove all tracked temporary files."""
    for temp_file in _temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except Exception as e:
            print(f"⚠️  Warning: Could not delete temporary file {temp_file}: {e}")


# Register cleanup function to run on exit
atexit.register(cleanup_temp_files)


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


def combine_summaries(summary1: str, summary2: str) -> str:
    """Combine two summaries into one coherent markdown document using LLM."""
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

        prompt = f"""
Combine the following two summary documents into one coherent Markdown document.

Requirements:
- Merge the two summaries into a single, well-structured document
- Start with a clear title (use the most appropriate one or create a new unified title)
- Use sections with headings
- Bullet points where appropriate
- Remove duplicate information
- Ensure continuity and flow between the two parts
- Maintain focus on key ideas and conclusions
- Do NOT mention that this comes from multiple parts or that it was combined

First Summary:
{summary1}

Second Summary:
{summary2}

Return the combined summary as a single Markdown document.
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise technical summarizer that combines multiple summaries into coherent documents."},
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
        raise


def summarize_recursive(text: str, md_path: Path, depth: int = 0) -> str:
    """Recursively summarize text, splitting if too long.
    
    Args:
        text: The text content to summarize
        md_path: Path to the original markdown file (for splitting if needed)
        depth: Current recursion depth
        
    Returns:
        Summarized markdown text
        
    Raises:
        MaxDepthExceeded: If maximum recursion depth is reached
        TokenLimitExceeded: If text is too long and depth limit reached
    """
    # Check depth limit
    if depth >= MAX_DEPTH:
        raise MaxDepthExceeded(
            f"Maximum recursion depth ({MAX_DEPTH}) reached. "
            f"The markdown file is too long even after {MAX_DEPTH} levels of splitting. "
            f"Please manually split the file or increase MAX_DEPTH."
        )
    
    # Check if text is too long
    should_split = len(text) > MAX_CHARS_SAFE
    
    if should_split:
        print(f"📊 Text too long ({len(text)} chars), splitting into 2 parts (depth {depth + 1}/{MAX_DEPTH})...")
        
        # Split the markdown file
        try:
            temp_file1, temp_file2 = split_md_file(md_path)
            print(f"   ✓ Split into: {temp_file1.name} and {temp_file2.name}")
        except Exception as e:
            raise RuntimeError(f"Failed to split markdown file: {e}")
        
        # Read text from split files
        try:
            text1 = read_md_text(temp_file1, max_chars=None)  # Read full content
            text2 = read_md_text(temp_file2, max_chars=None)
        except Exception as e:
            raise RuntimeError(f"Failed to read split markdown files: {e}")
        
        # Recursively summarize each part
        print(f"   🧠 Processing part 1/2 (depth {depth + 1}/{MAX_DEPTH})...")
        try:
            summary1 = summarize_recursive(text1, temp_file1, depth + 1)
        except Exception as e:
            # Clean up temp files before re-raising
            cleanup_temp_files()
            raise
        
        print(f"   🧠 Processing part 2/2 (depth {depth + 1}/{MAX_DEPTH})...")
        try:
            summary2 = summarize_recursive(text2, temp_file2, depth + 1)
        except Exception as e:
            # Clean up temp files before re-raising
            cleanup_temp_files()
            raise
        
        # Combine the summaries
        print(f"   🔗 Combining summaries (depth {depth + 1}/{MAX_DEPTH})...")
        try:
            combined = combine_summaries(summary1, summary2)
        except Exception as e:
            cleanup_temp_files()
            raise RuntimeError(f"Failed to combine summaries: {e}")
        
        # Clean up temporary markdown files (but keep summaries if they were saved)
        try:
            if temp_file1.exists():
                temp_file1.unlink()
            if temp_file2.exists():
                temp_file2.unlink()
            # Remove from tracking list
            if temp_file1 in _temp_files:
                _temp_files.remove(temp_file1)
            if temp_file2 in _temp_files:
                _temp_files.remove(temp_file2)
        except Exception as e:
            print(f"⚠️  Warning: Could not delete temporary files: {e}")
        
        return combined
    
    # Text is within safe limit, try to summarize
    try:
        return summarize(text)
    except TokenLimitExceeded:
        # If we hit token limit and haven't reached max depth, force splitting
        if depth < MAX_DEPTH:
            print(f"⚠️  Token limit exceeded (text length: {len(text)}), forcing split (depth {depth + 1}/{MAX_DEPTH})...")
            # Force splitting by going through the splitting path
            # Split the markdown file
            try:
                temp_file1, temp_file2 = split_md_file(md_path)
                print(f"   ✓ Split into: {temp_file1.name} and {temp_file2.name}")
            except Exception as e:
                raise RuntimeError(f"Failed to split markdown file: {e}")
            
            # Read text from split files
            try:
                text1 = read_md_text(temp_file1, max_chars=None)
                text2 = read_md_text(temp_file2, max_chars=None)
            except Exception as e:
                raise RuntimeError(f"Failed to read split markdown files: {e}")
            
            # Recursively summarize each part
            print(f"   🧠 Processing part 1/2 (depth {depth + 1}/{MAX_DEPTH})...")
            try:
                summary1 = summarize_recursive(text1, temp_file1, depth + 1)
            except Exception as e:
                cleanup_temp_files()
                raise
            
            print(f"   🧠 Processing part 2/2 (depth {depth + 1}/{MAX_DEPTH})...")
            try:
                summary2 = summarize_recursive(text2, temp_file2, depth + 1)
            except Exception as e:
                cleanup_temp_files()
                raise
            
            # Combine the summaries
            print(f"   🔗 Combining summaries (depth {depth + 1}/{MAX_DEPTH})...")
            try:
                combined = combine_summaries(summary1, summary2)
            except Exception as e:
                cleanup_temp_files()
                raise RuntimeError(f"Failed to combine summaries: {e}")
            
            # Clean up temporary markdown files
            try:
                if temp_file1.exists():
                    temp_file1.unlink()
                if temp_file2.exists():
                    temp_file2.unlink()
                if temp_file1 in _temp_files:
                    _temp_files.remove(temp_file1)
                if temp_file2 in _temp_files:
                    _temp_files.remove(temp_file2)
            except Exception as e:
                print(f"⚠️  Warning: Could not delete temporary files: {e}")
            
            return combined
        else:
            raise MaxDepthExceeded(
                f"Maximum recursion depth ({MAX_DEPTH}) reached. "
                f"The text segment is still too long. Please manually split the file or increase MAX_DEPTH."
            )


def generate_tags(summary: str) -> list[str]:
    """Generate top 5 relevant tags for a summary using LLM."""
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

        prompt = f"""
Analyze the following summary document and generate exactly 5 relevant tags that best describe its main topics and themes.

Requirements:
- Generate exactly 5 tags
- Tags should be concise (1-3 words each)
- Tags should be lowercase
- Use commas to separate tags
- Focus on the main topics, themes, and subject matter
- Do NOT include generic words like "summary", "discussion", "document"
- Return ONLY the tags separated by commas, no numbering, no explanations

Summary:
{summary}

Return format example: tag1, tag2, tag3, tag4, tag5
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant tags for documents."},
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
        
        # Parse tags from response
        tags = [tag.strip() for tag in result.split(',')]
        tags = [tag for tag in tags if tag]  # Remove empty tags
        
        # Ensure we have exactly 5 tags (pad or trim if needed)
        if len(tags) > 5:
            tags = tags[:5]
        elif len(tags) < 5:
            # If we have fewer than 5, try to extract more from the summary
            # For now, just pad with generic tags if needed
            while len(tags) < 5:
                tags.append("general")
        
        return tags[:5]
        
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
        # Return default tags if generation fails
        print(f"⚠️  Warning: Could not generate tags: {e}")
        return ["general", "summary", "document", "content", "notes"]


def format_summary_with_tags(summary: str, tags: list[str]) -> str:
    """Format summary with frontmatter tags.
    
    Format:
    ---
    tag: tag1, tag2, tag3, tag4, tag5
    ---
    # <Title>
    <main body>
    """
    tags_str = ", ".join(tags)
    
    # Check if summary already has frontmatter
    if summary.strip().startswith('---'):
        # Extract existing frontmatter and content
        parts = summary.split('---', 2)
        if len(parts) >= 3:
            # Has frontmatter, replace or merge it
            existing_frontmatter = parts[1].strip()
            content = parts[2].strip()
            # Check if tag already exists in frontmatter
            if 'tag:' in existing_frontmatter:
                # Replace existing tag line
                lines = existing_frontmatter.split('\n')
                new_lines = []
                for line in lines:
                    if line.strip().startswith('tag:'):
                        new_lines.append(f"tag: {tags_str}")
                    else:
                        new_lines.append(line)
                new_frontmatter = '\n'.join(new_lines)
                return f"---\n{new_frontmatter}\n---\n\n{content}"
            else:
                # Add tag to existing frontmatter
                return f"---\n{existing_frontmatter}\ntag: {tags_str}\n---\n\n{content}"
    
    # No frontmatter, add it before the content
    frontmatter = f"---\ntag: {tags_str}\n---\n\n"
    return frontmatter + summary


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
Summarize the following document into a clean Markdown document.

Requirements:
- Start with a clear title
- Use sections with headings
- Bullet points where appropriate
- Focus on key ideas and conclusions
- Preserve important details and structure
- Maintain the document's main themes and topics

Document:
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
        
        # Check if this is a token limit error
        error_str = str(e).lower()
        if '400' in error_str or 'token' in error_str or 'context length' in error_str or 'context_length' in error_str:
            raise TokenLimitExceeded(f"Text exceeds LLM token limit: {e}")
        
        raise  # Re-raise other exceptions


def main():
    if len(sys.argv) != 2:
        print("Usage: python md_summarise_by_llm.py path/to/file.md")
        sys.exit(1)

    md_path = Path(sys.argv[1])

    if not md_path.exists() or md_path.suffix.lower() != ".md":
        print("Error: input must be an existing .md file")
        sys.exit(1)

    print(f"📄 Reading: {md_path}")
    text = read_md_text(md_path, max_chars=None)  # Read full content for recursive processing
    
    if not text.strip():
        print("⚠️  Warning: No text found in markdown file")
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
        summary_md = summarize_recursive(text, md_path)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        cleanup_temp_files()
        sys.exit(1)
    except MaxDepthExceeded as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Suggestion:")
        print("   The markdown file is extremely long. Consider:")
        print("   1. Manually splitting the file into smaller parts")
        print("   2. Increasing MAX_DEPTH in the script (if your system can handle it)")
        print("   3. Using a model with a larger context window")
        cleanup_temp_files()
        sys.exit(1)
    except TokenLimitExceeded as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 This should not happen - the recursive splitting should handle this.")
        print("   Please report this issue.")
        cleanup_temp_files()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during summarization: {e}")
        print("\n💡 Reminder:")
        print("   If the API connection failed, please check:")
        print("   1. LM Studio is running")
        print(f"   2. The model ({MODEL_NAME}) is loaded and server is started")
        print(f"   3. The API is accessible at: {LM_STUDIO_BASE_URL}")
        cleanup_temp_files()
        sys.exit(1)

    # Generate tags for the summary
    print("🏷️  Generating tags...")
    try:
        tags = generate_tags(summary_md)
        print(f"   ✓ Generated tags: {', '.join(tags)}")
    except Exception as e:
        print(f"⚠️  Warning: Could not generate tags: {e}")
        tags = ["general", "summary", "document", "content", "notes"]
    
    # Format summary with tags
    formatted_summary = format_summary_with_tags(summary_md, tags)
    
    output_path = md_path.with_suffix(".summary.md")
    output_path.write_text(formatted_summary, encoding="utf-8")

    print(f"✅ Summary written to: {output_path}")
    
    # Final cleanup
    cleanup_temp_files()


if __name__ == "__main__":
    main()

