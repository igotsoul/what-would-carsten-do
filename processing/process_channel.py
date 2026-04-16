#!/usr/bin/env python3
"""
YouTube Knowledge Base — Channel Processing Pipeline

Downloads transcripts from a YouTube channel, cleans them, processes each
through Claude to create Knowledge Cards, and builds the index.

Usage:
    # Process all new videos from a channel
    python process_channel.py --channel "@CarstenLützen" --prefix CL

    # Process a single video
    python process_channel.py --video "https://youtube.com/watch?v=abc123" --channel "@CarstenLützen" --prefix CL

    # Only download and clean transcripts (no Claude processing)
    python process_channel.py --channel "@CarstenLützen" --prefix CL --download-only

    # Only rebuild the index from existing knowledge cards
    python process_channel.py --rebuild-index
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Persistent dependency loading ──────────────────────────────────────────
# The .pylibs folder lives on the mounted drive and survives VM resets.
# No pip install needed at runtime.
_PYLIBS = Path(__file__).resolve().parent / ".pylibs"
if _PYLIBS.is_dir() and str(_PYLIBS) not in sys.path:
    sys.path.insert(0, str(_PYLIBS))

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT_TRANSCRIPT_API = True
except ImportError:
    HAS_YT_TRANSCRIPT_API = False

# ─── Configuration ───────────────────────────────────────────────────────────

# Base path — adjust if your KB is elsewhere
KB_PATH = Path(__file__).resolve().parent.parent
VIDEOS_DIR = KB_PATH / "videos"
TOPICS_DIR = KB_PATH / "topics"
PROCESSING_DIR = KB_PATH / "processing"
INDEX_FILE = KB_PATH / "index.json"
CHANNELS_FILE = KB_PATH / "channels.json"

PROMPT_TEMPLATE_FILE = PROCESSING_DIR / "prompt_template.md"
TRANSCRIPTS_DIR = PROCESSING_DIR / "transcripts"
SKIP_LOG_FILE = PROCESSING_DIR / "skipped_videos.json"

# Global verbosity flag (set by --quiet)
QUIET = False

def log(msg: str):
    """Print only when not in quiet mode."""
    if not QUIET:
        print(msg)


def get_skipped_ids() -> set:
    """Return set of video IDs that failed transcript download (to avoid retrying)."""
    if not SKIP_LOG_FILE.exists():
        return set()
    try:
        data = json.loads(SKIP_LOG_FILE.read_text())
        return {v["id"] for v in data.get("skipped", [])}
    except (json.JSONDecodeError, KeyError):
        return set()


def log_skipped_video(video_id: str, title: str, reason: str):
    """Add a video to the skip log so it won't be retried."""
    data = {"skipped": []}
    if SKIP_LOG_FILE.exists():
        try:
            data = json.loads(SKIP_LOG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    data["skipped"].append({
        "id": video_id,
        "title": title,
        "reason": reason,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    SKIP_LOG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ─── Phase 1: Download & Clean ──────────────────────────────────────────────

def get_channel_videos(channel: str) -> list[dict]:
    """List all videos from a YouTube channel using yt-dlp."""
    log(f"📡 Fetching video list from {channel}...")
    cmd = [
        "yt-dlp", "--flat-playlist",
        "--print", "%(id)s\t%(title)s\t%(duration_string)s",
        f"https://www.youtube.com/{channel}/videos"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        log(f"  ❌ Error fetching channel: {result.stderr[:200]}")
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            videos.append({
                "id": parts[0],
                "title": parts[1],
                "duration": parts[2]
            })
        elif len(parts) == 2:
            videos.append({"id": parts[0], "title": parts[1], "duration": "unknown"})
    log(f"  ✅ Found {len(videos)} videos")
    return videos


def get_processed_ids() -> set:
    """Return set of video IDs already processed — from index AND on-disk files.

    The index is only written at the end of a successful batch. If a previous
    run was interrupted after writing some files but before rebuilding the index,
    those video IDs would be missing from the index and get reprocessed as
    duplicates. Scanning disk files as well makes the dedup check authoritative.
    """
    ids = set()

    # Fast path: read from index
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text())
            for v in index.get("videos", []):
                if v.get("id"):
                    ids.add(v["id"])
        except (json.JSONDecodeError, KeyError):
            pass

    # Safety net: scan actual files on disk (catches videos written before
    # the index was last updated — e.g. after a timeout or crash mid-batch)
    for card_file in VIDEOS_DIR.glob("**/*.md"):
        fm = extract_frontmatter(card_file)
        if fm and fm.get("video_id"):
            ids.add(fm["video_id"])

    return ids


def fetch_transcript_via_api(video_id: str, lang: str = "en") -> tuple[str | None, str]:
    """Fetch transcript using youtube-transcript-api (less rate-limit prone).

    Tries the requested language first, then falls back to any available
    auto-generated transcript (YouTube often tags auto-captions in the
    channel's detected language even when the speaker uses another language).

    Returns:
        (clean_text, reason) where reason is "success", "rate_limited", or "no_transcript"
    """
    if not HAS_YT_TRANSCRIPT_API:
        return None, "no_api"

    def _is_ip_blocked(err: Exception) -> bool:
        """Detect YouTube IP blocking / rate limiting errors."""
        err_str = str(err).lower()
        return any(phrase in err_str for phrase in [
            "429", "too many requests", "blocking requests from your ip",
            "requestblocked", "ipblocked", "ip has been blocked"
        ])

    try:
        ytt_api = YouTubeTranscriptApi()
        was_ip_blocked = False

        # First try the requested language directly
        try:
            transcript = ytt_api.fetch(video_id, languages=[lang])
            text = " ".join(snippet.text.strip() for snippet in transcript.snippets
                            if snippet.text.strip())
            if text:
                return text, "success"
        except Exception as e:
            if _is_ip_blocked(e):
                was_ip_blocked = True
            # Otherwise fall through to auto-detect

        # Fallback: list all available transcripts and pick the first available one
        try:
            transcript_list = ytt_api.list(video_id=video_id)
        except Exception as e:
            if _is_ip_blocked(e):
                return None, "rate_limited"
            return None, "no_transcript"

        available_langs = [t.language_code for t in transcript_list]
        if available_langs:
            log(f"     Available transcript languages: {', '.join(available_langs)}")

        for t in transcript_list:
            try:
                transcript = ytt_api.fetch(video_id, languages=[t.language_code])
                text = " ".join(snippet.text.strip() for snippet in transcript.snippets
                                if snippet.text.strip())
                if text:
                    log(f"     Found transcript in '{t.language_code}' ({t.language})")
                    return text, "success"
            except Exception as e:
                if _is_ip_blocked(e):
                    was_ip_blocked = True
                    log(f"     IP blocked when fetching '{t.language_code}' transcript")
                continue

        # If we found languages but couldn't fetch any due to IP blocking,
        # report as rate_limited (NOT no_transcript) so yt-dlp gets a chance
        if was_ip_blocked:
            return None, "rate_limited"

        return None, "no_transcript"
    except Exception as e:
        if _is_ip_blocked(e):
            return None, "rate_limited"
        err_str = str(e).lower()
        if "no transcript" in err_str or "disabled" in err_str or "not found" in err_str:
            return None, "no_transcript"
        # Unknown error — log and treat as no_transcript
        log(f"  ⚠️  youtube-transcript-api error: {e}")
        return None, "no_transcript"


def download_transcript_ytdlp(video_id: str, lang: str = "en", max_retries: int = 2) -> tuple[Path | None, str]:
    """Fallback: download subtitles via yt-dlp.

    Tries the requested language first. If that fails (not rate-limited), tries
    a second attempt without --sub-lang to grab whatever language is available.
    This handles the common case where YouTube tags auto-captions in the channel's
    detected language (e.g., Danish) even though the speaker uses another language.

    Returns:
        (path, reason) where reason is "success", "rate_limited", or "no_transcript"
    """
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TRANSCRIPTS_DIR / f"{video_id}"

    was_rate_limited = False

    # max_retries=0 means single attempt (no retries), max_retries=2 means up to 3 attempts
    total_attempts = max_retries + 1

    for attempt_type in ["specific_lang", "any_lang"]:
        cmd = [
            "yt-dlp",
            "--write-auto-sub", "--write-sub",
            "--skip-download",
            "--output", str(output_path) + ".%(ext)s",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        if attempt_type == "specific_lang":
            cmd.insert(-1, "--sub-lang")
            cmd.insert(-1, lang)

        for attempt in range(total_attempts):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            except FileNotFoundError:
                log(f"  ⚠️  yt-dlp not installed — skipping fallback")
                return None, "no_transcript"
            except subprocess.TimeoutExpired:
                log(f"  ⏳ yt-dlp timed out (60s)")
                was_rate_limited = True
                break

            # Find any downloaded subtitle file
            candidates = glob.glob(str(output_path) + ".*.vtt") + glob.glob(str(output_path) + ".*.srt")
            if candidates:
                found = Path(candidates[0])
                found_lang = found.stem.split(".")[-1] if "." in found.stem else "unknown"
                if found_lang != lang:
                    log(f"     Found subtitles in '{found_lang}' via yt-dlp")
                return found, "success"

            # Check if rate limited (429) — retry with backoff if retries remain
            if "429" in result.stderr or "Too Many Requests" in result.stderr:
                was_rate_limited = True
                if attempt < total_attempts - 1:
                    wait_time = 30 * (attempt + 1)
                    log(f"  ⏳ yt-dlp rate limited (429) — waiting {wait_time}s before retry ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

            # Not rate limited — no point retrying this attempt type
            break

        # If rate limited on specific lang, don't bother trying any_lang either
        if was_rate_limited:
            break

    if was_rate_limited:
        return None, "rate_limited"
    return None, "no_transcript"


def get_transcript(video_id: str, lang: str = "en") -> tuple[str | None, str]:
    """Get transcript text for a video. Tries youtube-transcript-api first, yt-dlp as fallback.

    Returns:
        (clean_text, reason) where reason is "success", "rate_limited", or "no_transcript"
    """
    api_was_ip_blocked = False

    # Primary: youtube-transcript-api (different endpoint, less rate limiting)
    if HAS_YT_TRANSCRIPT_API:
        log(f"     Trying youtube-transcript-api...")
        text, reason = fetch_transcript_via_api(video_id, lang)
        if text:
            return text, "success"
        if reason == "rate_limited":
            api_was_ip_blocked = True
            log(f"     API rate limited/IP blocked — trying yt-dlp fallback (no retries)...")
        elif reason == "no_transcript":
            # API confirmed no transcripts exist in ANY language — skip yt-dlp
            return None, "no_transcript"

    # Fallback: yt-dlp (tries requested lang first, then any available lang)
    # If API was already IP-blocked, use max_retries=0 (single attempt, no sleep)
    ytdlp_retries = 0 if api_was_ip_blocked else 2
    log(f"     Trying yt-dlp...")
    vtt_path, reason = download_transcript_ytdlp(video_id, lang, max_retries=ytdlp_retries)
    if vtt_path:
        text = clean_vtt(vtt_path)
        try:
            vtt_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        return text, "success"

    # If the API already confirmed transcripts exist (but couldn't fetch due to IP block),
    # treat any yt-dlp failure as rate_limited too — don't permanently skip the video
    if api_was_ip_blocked:
        return None, "rate_limited"
    return None, reason


def clean_vtt(vtt_path: Path) -> str:
    """Convert VTT subtitle file to clean plain text."""
    content = vtt_path.read_text(errors="replace")
    lines = content.split("\n")
    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        if (not line or line == "WEBVTT" or "-->" in line
                or line.startswith("Kind:") or line.startswith("Language:")
                or line.startswith("NOTE")):
            continue
        # Remove HTML-like tags and VTT positioning
        clean = re.sub(r"<[^>]+>", "", line)
        clean = re.sub(r"align:start position:\d+%", "", clean).strip()
        if clean and clean not in seen:
            seen.add(clean)
            text_lines.append(clean)

    return " ".join(text_lines)


# ─── Phase 2: Claude Processing ─────────────────────────────────────────────

def build_claude_prompt(video_meta: dict, transcript: str, channel: str,
                        channel_id: str, prefix: str) -> str:
    """Build the full prompt for Claude to process a transcript."""
    template = PROMPT_TEMPLATE_FILE.read_text()
    today = datetime.now().strftime("%Y-%m-%d")

    meta_block = f"""## Video Metadata
- **video_id:** {video_meta['id']}
- **title:** {video_meta['title']}
- **channel:** {channel}
- **channel_id:** {channel_id}
- **url:** https://www.youtube.com/watch?v={video_meta['id']}
- **duration:** {video_meta.get('duration', 'unknown')}
- **processed_date:** {today}
- **language:** en

## Transcript

{transcript}
"""
    output_instructions = """

## CRITICAL OUTPUT INSTRUCTIONS

Output ONLY the markdown knowledge card — nothing else. No preamble, no explanation,
no "here is the card", no code fences, no commentary. Start directly with the YAML
frontmatter (---) and end with the last line of the card. Your entire response must be
a valid markdown file that can be saved as-is.

DO NOT wrap the output in ```markdown``` code fences.
DO NOT add any text before the opening --- or after the card content.
"""
    return template + output_instructions + "\n\n---\n\n" + meta_block


def process_with_claude(prompt: str) -> str | None:
    """Send a prompt to Claude via CLI and return the response."""
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "sonnet"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            log(f"  ❌ Claude error: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        log("  ❌ Claude timed out (120s)")
        return None
    except FileNotFoundError:
        log("  ❌ Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
        return None


def clean_claude_output(text: str) -> str:
    """Remove conversational overhead from Claude's output."""
    # Strip markdown code fences if Claude wrapped the output
    text = re.sub(r"^```(?:markdown)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)

    # If there's preamble before the first ---, remove it
    match = re.search(r"^---\s*$", text, re.MULTILINE)
    if match and match.start() > 0:
        text = text[match.start():]

    # Remove trailing conversational text after the card
    # Look for common patterns like "---\n\nLet me know" or "---\n\nThis card"
    lines = text.rstrip().split("\n")
    # Find the last meaningful content line (not empty, not a conversational sign-off)
    while lines and (not lines[-1].strip() or
                     any(p in lines[-1].lower() for p in
                         ["let me know", "here is", "ready to save", "write permission",
                          "shall i", "would you like", "i hope this"])):
        lines.pop()

    return "\n".join(lines) + "\n"


def sanitize_filename(title: str) -> str:
    """Convert a video title to a safe filename."""
    # Remove non-alphanumeric chars except hyphens and spaces
    clean = re.sub(r"[^\w\s-]", "", title.lower())
    # Replace spaces with hyphens, collapse multiple hyphens
    clean = re.sub(r"[\s]+", "-", clean.strip())
    clean = re.sub(r"-+", "-", clean)
    return clean[:60]  # Limit length


# ─── Phase 3: Index Building ────────────────────────────────────────────────

def extract_frontmatter(md_path: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    content = md_path.read_text()
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().strip('"')
            value = value.strip().strip('"')
            # Handle arrays
            if value.startswith("["):
                try:
                    value = json.loads(value.replace("'", '"'))
                except json.JSONDecodeError:
                    pass
            frontmatter[key] = value
    return frontmatter


def extract_one_liner(md_path: Path) -> str:
    """Extract the Summary section as a one-liner."""
    content = md_path.read_text()
    match = re.search(r"## Summary\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if match:
        summary = match.group(1).strip()
        # Truncate to ~200 chars
        if len(summary) > 200:
            summary = summary[:197] + "..."
        return summary
    return ""


def rebuild_index():
    """Rebuild index.json and index_compact.tsv from all existing knowledge cards.

    Deduplicates by video_id (keeps the newest file if duplicates exist).
    Produces two files:
      - index.json         — full index (for detailed lookups after matching)
      - index_compact.tsv  — lightweight lookup index (for skill's first-pass matching)
    """
    log("📋 Rebuilding index...")
    raw_videos = []

    for channel_dir in sorted(VIDEOS_DIR.iterdir()):
        if not channel_dir.is_dir():
            continue
        for card_file in sorted(channel_dir.glob("*.md")):
            fm = extract_frontmatter(card_file)
            if not fm:
                continue
            one_liner = extract_one_liner(card_file)
            raw_videos.append({
                "id": fm.get("video_id", ""),
                "file": str(card_file.relative_to(KB_PATH)),
                "title": fm.get("title", ""),
                "channel": fm.get("channel", ""),
                "duration": fm.get("duration", ""),
                "tags": fm.get("tags", []),
                "topics": fm.get("topics", []),
                "category": fm.get("category", ""),
                "one_liner": one_liner
            })

    # Deduplicate by video_id — keep the last occurrence (highest CL number)
    seen = {}
    for v in raw_videos:
        vid = v["id"]
        if vid:
            seen[vid] = v  # Later entries overwrite earlier ones
    videos = list(seen.values())
    dupes_removed = len(raw_videos) - len(videos)
    if dupes_removed > 0:
        log(f"  🧹 Removed {dupes_removed} duplicate entries")

    # Load or create channels list
    channels = []
    if CHANNELS_FILE.exists():
        try:
            channels = json.loads(CHANNELS_FILE.read_text()).get("channels", [])
        except json.JSONDecodeError:
            pass

    # ── Write full index.json (compact formatting, no pretty-print) ──
    index = {
        "version": "2.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "total_videos": len(videos),
        "channels": channels,
        "videos": videos
    }
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    # ── Write compact TSV lookup index ──
    # Format: id<TAB>title<TAB>tags (comma-separated)<TAB>category<TAB>file
    # This is what the skill reads first (~80-90% smaller than full JSON)
    compact_path = KB_PATH / "index_compact.tsv"
    lines = ["id\ttitle\ttags\tcategory\tfile"]
    for v in videos:
        tags = v.get("tags", [])
        if isinstance(tags, list):
            tag_str = ",".join(tags[:7])  # Cap at 7 most specific tags
        else:
            tag_str = str(tags)
        category = v.get("category", "")
        lines.append(f"{v['id']}\t{v['title']}\t{tag_str}\t{category}\t{v['file']}")
    compact_path.write_text("\n".join(lines) + "\n")

    log(f"  ✅ Index rebuilt: {len(videos)} videos (JSON + compact TSV)")
    log(f"     index.json:       {INDEX_FILE.stat().st_size:>8,} bytes")
    log(f"     index_compact.tsv: {compact_path.stat().st_size:>7,} bytes")


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def process_video(video_meta: dict, channel_name: str, channel_id: str,
                  prefix: str, channel_dir: Path, counter: int,
                  lang: str = "en") -> str:
    """Full pipeline for a single video: download → clean → process → save.

    Returns: "success", "rate_limited", "no_transcript", or "failed"
    """
    vid_id = video_meta["id"]
    title = video_meta["title"]
    log(f"\n🎬 [{counter}] Processing: {title}")

    # Step 1: Get transcript (youtube-transcript-api → yt-dlp fallback)
    log(f"  📥 Fetching transcript...")
    clean_text, reason = get_transcript(vid_id, lang)
    if not clean_text:
        if reason == "rate_limited":
            log(f"  ⏳ Rate limited — will retry in next run (NOT adding to skip-log)")
            return "rate_limited"
        else:
            log(f"  ⚠️  No transcript available — skipping and logging permanently")
            log_skipped_video(vid_id, title, "no_transcript")
            return "no_transcript"

    # Step 2: Check transcript quality
    word_count = len(clean_text.split())
    log(f"     {word_count} words in transcript")

    if word_count < 20:
        log(f"  ⚠️  Transcript too short — skipping and logging")
        log_skipped_video(vid_id, title, "transcript_too_short")
        return "failed"

    # Step 3: Process with Claude
    log(f"  🤖 Processing with Claude...")
    prompt = build_claude_prompt(video_meta, clean_text, channel_name,
                                 channel_id, prefix)
    knowledge_card = process_with_claude(prompt)
    if not knowledge_card:
        log(f"  ❌ Claude processing failed — skipping")
        return "failed"

    # Step 4: Clean up Claude output and save knowledge card
    knowledge_card = clean_claude_output(knowledge_card)
    if len(knowledge_card.strip()) < 50:
        log(f"  ⚠️  Claude output too short after cleanup — skipping")
        return "failed"
    safe_title = sanitize_filename(title)
    filename = f"{prefix}_{counter:03d}_{safe_title}.md"
    output_path = channel_dir / filename

    output_path.write_text(knowledge_card)
    log(f"  ✅ Saved: {output_path.name}")

    return "success"


def main():
    parser = argparse.ArgumentParser(description="YouTube Knowledge Base Processor")
    parser.add_argument("--channel", help="YouTube channel handle (e.g., @CarstenLützen)")
    parser.add_argument("--channel-name", help="Display name (e.g., 'Carsten Lützen')")
    parser.add_argument("--prefix", help="File prefix (e.g., CL)")
    parser.add_argument("--slug", help="Folder name for this channel (e.g., 'carsten-lutzen')")
    parser.add_argument("--video", help="Process a single video URL instead of full channel")
    parser.add_argument("--lang", default="en", help="Subtitle language (default: en)")
    parser.add_argument("--download-only", action="store_true", help="Only download, don't process")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild index from existing cards")
    parser.add_argument("--limit", type=int, default=0, help="Max videos to process (0 = all)")
    parser.add_argument("--start-counter", type=int, default=1, help="Starting counter for filenames")
    parser.add_argument("--quiet", action="store_true", help="Minimal output (for scheduled tasks)")
    args = parser.parse_args()

    # Set global verbosity
    global QUIET
    QUIET = args.quiet

    if args.rebuild_index:
        rebuild_index()
        return

    if not args.channel:
        print("❌ --channel is required (e.g., --channel '@CarstenLützen')")
        sys.exit(1)

    channel_name = args.channel_name or args.channel.lstrip("@")
    prefix = args.prefix or args.channel.lstrip("@")[:2].upper()
    # Channel slug for directory name
    if args.slug:
        channel_slug = args.slug
    else:
        import unicodedata
        raw_slug = args.channel.lstrip("@").lower()
        raw_slug = unicodedata.normalize("NFKD", raw_slug).encode("ascii", "ignore").decode("ascii")
        channel_slug = re.sub(r"[^a-z0-9]+", "-", raw_slug).strip("-")

    # Ensure directories exist
    channel_dir = VIDEOS_DIR / channel_slug
    channel_dir.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Get list of already-processed video IDs
    processed_ids = get_processed_ids()
    log(f"📊 Already processed: {len(processed_ids)} videos")

    # Get videos to process
    if args.video:
        # Single video mode
        vid_match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]+)", args.video)
        if not vid_match:
            print(f"❌ Could not extract video ID from: {args.video}")
            sys.exit(1)
        vid_id = vid_match.group(1)
        videos = [{"id": vid_id, "title": "Unknown", "duration": "unknown"}]
    else:
        # Full channel mode
        videos = get_channel_videos(args.channel)

    # Filter out already-processed AND previously-skipped videos
    skipped_ids = get_skipped_ids()
    log(f"⏭️  Previously skipped (no transcript): {len(skipped_ids)} videos")
    new_videos = [v for v in videos if v["id"] not in processed_ids and v["id"] not in skipped_ids]
    log(f"🆕 New videos to process: {len(new_videos)}")

    if args.limit > 0:
        new_videos = new_videos[:args.limit]
        log(f"   (limited to {args.limit})")

    if not new_videos:
        log("✨ Nothing new to process!")
        return

    # Process each video
    success_count = 0
    fail_count = 0
    rate_limit_count = 0
    consecutive_429 = 0
    MAX_CONSECUTIVE_429 = 3  # Abort batch after this many consecutive rate limits
    counter = args.start_counter

    # Find the highest existing counter in the channel dir
    existing_files = list(channel_dir.glob(f"{prefix}_*.md"))
    if existing_files:
        existing_counters = []
        for f in existing_files:
            match = re.match(rf"{prefix}_(\d+)_", f.name)
            if match:
                existing_counters.append(int(match.group(1)))
        if existing_counters:
            counter = max(existing_counters) + 1

    for video in new_videos:
        if args.download_only:
            log(f"\n📥 Downloading: {video['title']}")
            clean_text, reason = get_transcript(video["id"], args.lang)
            if clean_text:
                clean_path = TRANSCRIPTS_DIR / f"{video['id']}_clean.txt"
                clean_path.write_text(clean_text)
                log(f"  ✅ Saved clean transcript: {clean_path.name} ({len(clean_text.split())} words)")
                success_count += 1
                consecutive_429 = 0
            elif reason == "rate_limited":
                log(f"  ⏳ Rate limited — will retry next run")
                rate_limit_count += 1
                consecutive_429 += 1
            else:
                log(f"  ⚠️  No transcript available")
                fail_count += 1
                consecutive_429 = 0
            # Check for consecutive 429 abort
            if consecutive_429 >= MAX_CONSECUTIVE_429:
                log(f"\n🛑 {MAX_CONSECUTIVE_429} consecutive rate limits — aborting batch. Videos will be retried next run.")
                break
            continue

        result = process_video(video, channel_name, args.channel, prefix,
                               channel_dir, counter, args.lang)
        if result == "success":
            success_count += 1
            counter += 1
            consecutive_429 = 0
        elif result == "rate_limited":
            rate_limit_count += 1
            consecutive_429 += 1
        else:
            fail_count += 1
            consecutive_429 = 0

        # Abort batch if YouTube keeps rate limiting
        if consecutive_429 >= MAX_CONSECUTIVE_429:
            log(f"\n🛑 {MAX_CONSECUTIVE_429} consecutive rate limits — aborting batch. Videos will be retried next run.")
            break

        # Delay between videos to avoid YouTube rate limiting (429)
        time.sleep(15)

    # Rebuild index after processing
    if not args.download_only and success_count > 0:
        rebuild_index()

    # Summary always prints (even in --quiet mode)
    print(f"\n{'='*50}")
    print(f"✅ Processed: {success_count}")
    print(f"⏳ Rate limited (will retry): {rate_limit_count}")
    print(f"❌ Failed/Skipped: {fail_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
