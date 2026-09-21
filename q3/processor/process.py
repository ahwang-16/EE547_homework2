import json
import os
import re
import sys
import time
from datetime import datetime, timezone

def strip_html(html_content):
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    links = re.findall(r'href=[\'"]?([^\'" >]+)', html_content, flags=re.IGNORECASE)
    images = re.findall(r'src=[\'"]?([^\'" >]+)', html_content, flags=re.IGNORECASE)

    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text).strip()

    return text, links, images

def get_iso_utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    print(f"[{get_iso_utc()}] Processor starting", flush=True)

    status_file = "/shared/status/fetch_complete.json"
    raw_dir = "/shared/raw"
    processed_dir = "/shared/processed"
    os.makedirs(processed_dir, exist_ok=True)

    while not os.path.exists(status_file):
        print(f"Waiting for {status_file}...", flush=True)
        time.sleep(2)

    print(f"[{get_iso_utc()}] Fetch complete marker found. Processing HTML...", flush=True)

    processed_count = 0

    for filename in os.listdir(raw_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(raw_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        paragraphs = len(re.findall(r'<p\b[^>]*>', html_content, flags=re.IGNORECASE))

        text, links, images = strip_html(html_content)

        words = re.findall(r'[a-zA-Z0-9]+', text.lower())
        word_count = len(words)

        sentences = [s for s in re.split(r'\. |\! |\? ', text) if s.strip()]
        sentence_count = len(sentences)

        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0.0

        out_data = {
            "source_file": filename,
            "text": text,
            "statistics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraphs,
                "avg_word_length": avg_word_length
            },
            "links": links,
            "images": images,
            "processed_at": get_iso_utc()
        }

        out_name = filename.replace('.html', '.json')
        with open(os.path.join(processed_dir, out_name), 'w', encoding='utf-8') as f:
            json.dump(out_data, f, indent=2)

        processed_count += 1

    process_status = {
        "timestamp": get_iso_utc(),
        "files_processed": processed_count
    }
    with open("/shared/status/process_complete.json", 'w') as f:
        json.dump(process_status, f, indent=2)

    print(f"[{get_iso_utc()}] Processor complete", flush=True)

if __name__ == "__main__":
    main()
