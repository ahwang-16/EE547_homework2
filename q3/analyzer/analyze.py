import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from collections import Counter

def jaccard_similarity(doc1_words, doc2_words):
    set1 = set(doc1_words)
    set2 = set(doc2_words)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0.0

def get_iso_utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    print(f"[{get_iso_utc()}] Analyzer starting", flush=True)

    status_file = "/shared/status/process_complete.json"
    processed_dir = "/shared/processed"
    analysis_dir = "/shared/analysis"
    os.makedirs(analysis_dir, exist_ok=True)

    while not os.path.exists(status_file):
        print(f"Waiting for {status_file}...", flush=True)
        time.sleep(2)

    print(f"[{get_iso_utc()}] Process complete marker found. Analyzing data...", flush=True)

    files = sorted([f for f in os.listdir(processed_dir) if f.endswith('.json')])

    docs_words = {}
    total_sentences = 0
    global_word_counter = Counter()
    bigram_counter = Counter()
    trigram_counter = Counter()

    for filename in files:
        with open(os.path.join(processed_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)

        text = data.get("text", "")
        words = re.findall(r'[a-zA-Z0-9]+', text.lower())
        docs_words[filename] = words

        total_sentences += data["statistics"]["sentence_count"]
        global_word_counter.update(words)

        for i in range(len(words) - 1):
            bigram_counter[" ".join(words[i:i+2])] += 1
        for i in range(len(words) - 2):
            trigram_counter[" ".join(words[i:i+3])] += 1

    total_words = sum(global_word_counter.values())
    unique_words = len(global_word_counter)

    top_100 = []
    for word, count in global_word_counter.most_common(100):
        freq = count / total_words if total_words > 0 else 0.0
        top_100.append({"word": word, "count": count, "frequency": round(freq, 6)})

    similarities = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            f1, f2 = files[i], files[j]
            sim = jaccard_similarity(docs_words[f1], docs_words[f2])
            similarities.append({"doc1": f1, "doc2": f2, "similarity": round(sim, 6)})

    top_bigrams = [{"bigram": b, "count": c} for b, c in bigram_counter.most_common(20)]
    top_trigrams = [{"trigram": t, "count": c} for t, c in trigram_counter.most_common(20)]

    avg_sentence_length = total_words / total_sentences if total_sentences > 0 else 0.0
    total_chars = sum(len(w) * count for w, count in global_word_counter.items())
    avg_word_length = total_chars / total_words if total_words > 0 else 0.0

    report = {
        "processing_timestamp": get_iso_utc(),
        "documents_processed": len(files),
        "total_words": total_words,
        "unique_words": unique_words,
        "top_100_words": top_100,
        "document_similarity": similarities,
        "top_bigrams": top_bigrams,
        "top_trigrams": top_trigrams,
        "readability": {
            "avg_sentence_length": round(avg_sentence_length, 4),
            "avg_word_length": round(avg_word_length, 4)
        }
    }

    with open(os.path.join(analysis_dir, "final_report.json"), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[{get_iso_utc()}] Analyzer complete", flush=True)

if __name__ == "__main__":
    main()
