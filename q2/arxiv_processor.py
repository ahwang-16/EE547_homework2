import sys
import os
import re
import time
import json
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from stopwords import STOPWORDS

if len(sys.argv) != 4:
    print("Usage: python arxiv_processor.py <search_query> <max_results> <output_dir>", file=sys.stderr)
    sys.exit(1)

search_query = sys.argv[1]
try:
    max_results = int(sys.argv[2])
    if not (1 <= max_results <= 100):
        raise ValueError
except ValueError:
    print("Error: max_results must be an integer between 1 and 100", file=sys.stderr)
    sys.exit(1)

output_dir = sys.argv[3]
os.makedirs(output_dir, exist_ok=True)
log_file_path = os.path.join(output_dir, "processing.log")

def get_iso_utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def write_log(message):
    timestamp = get_iso_utc()
    log_line = f"[{timestamp}] {message}\n"
    with open(log_file_path, "a", encoding="utf-8") as lf:
        lf.write(log_line)

base_url = "http://export.arxiv.org/api/query"
params = {"search_query": search_query, "start": 0, "max_results": max_results}
query_url = f"{base_url}?{urllib.parse.urlencode(params)}"

write_log(f"Starting ArXiv query: {search_query}")

max_retries = 3
xml_data = None

for attempt in range(max_retries):
    try:
        req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            xml_data = response.read()
            break
    except urllib.error.HTTPError as e:
        if e.code == 429:
            write_log("HTTP 429 Rate limited. Retrying in 3 seconds...")
            time.sleep(3)
        else:
            write_log(f"Network error HTTP {e.code}")
            sys.exit(1)
    except Exception as e:
        write_log(f"Network error: {e}")
        sys.exit(1)

if not xml_data:
    write_log("Failed to fetch data after retries.")
    sys.exit(1)

ns = {'atom': 'http://www.w3.org/2005/Atom'}
try:
    root = ET.fromstring(xml_data)
except ET.ParseError as e:
    write_log(f"Fatal XML Parse Error: {e}")
    sys.exit(1)

entries = root.findall('atom:entry', ns)
write_log(f"Fetched {len(entries)} results from ArXiv API")

start_time = time.perf_counter()
papers = []

global_word_freq = {}
global_doc_freq = {}
global_uppercase_terms = set()
global_numeric_terms = set()
global_hyphenated_terms = set()
global_category_dist = {}
total_abstracts = 0
global_total_words = 0
longest_abstract = 0
shortest_abstract = float('inf')

for entry in entries:
    try:
        # Extract metadata
        id_node = entry.find('atom:id', ns)
        title_node = entry.find('atom:title', ns)
        summary_node = entry.find('atom:summary', ns)
        published_node = entry.find('atom:published', ns)
        updated_node = entry.find('atom:updated', ns)

        if any(x is None for x in [id_node, title_node, summary_node, published_node, updated_node]):
            write_log("Warning: Missing required fields, skipping paper.")
            continue

        arxiv_id = id_node.text.split('/')[-1]
        write_log(f"Processing paper: {arxiv_id}")

        title = title_node.text.strip().replace('\n', ' ')
        abstract = summary_node.text.strip()

        authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns) if a.find('atom:name', ns) is not None]
        categories = [c.get('term') for c in entry.findall('atom:category', ns) if c.get('term')]

        if not authors or not categories:
            write_log(f"Warning: Missing authors or categories for {arxiv_id}, skipping.")
            continue

        for cat in categories:
            global_category_dist[cat] = global_category_dist.get(cat, 0) + 1

        all_words_raw = re.findall(r'[^\W_]+', abstract.lower())
        total_words = len(all_words_raw)

        if total_words == 0:
            continue

        unique_words = len(set(all_words_raw))
        avg_word_length = sum(len(w) for w in all_words_raw) / total_words

        sentences = [s for s in re.split(r'\. |\! |\? ', abstract) if s.strip()]
        sentence_word_counts = [len(re.findall(r'[^\W_]+', s.lower())) for s in sentences]

        longest_sent = max(sentence_word_counts) if sentence_word_counts else 0
        shortest_sent = min(sentence_word_counts) if sentence_word_counts else 0

        valid_words = [w for w in all_words_raw if w not in STOPWORDS]
        local_word_freq = {}
        for w in valid_words:
            local_word_freq[w] = local_word_freq.get(w, 0) + 1

        top_20 = sorted([{"word": k, "count": v} for k, v in local_word_freq.items()],
                        key=lambda x: (-x['count'], x['word']))[:20]

        raw_tokens = re.findall(r'[^\W_]+(?:-[^\W_]+)*', abstract)
        for token in raw_tokens:
            if any(c.isupper() for c in token[1:]):
                global_uppercase_terms.add(token)
            if any(c.isdigit() for c in token):
                global_numeric_terms.add(token)
            if '-' in token:
                global_hyphenated_terms.add(token)

        total_abstracts += 1
        global_total_words += total_words
        longest_abstract = max(longest_abstract, total_words)
        shortest_abstract = min(shortest_abstract, total_words)

        for w, freq in local_word_freq.items():
            global_word_freq[w] = global_word_freq.get(w, 0) + freq

        for w in set(valid_words):
            global_doc_freq[w] = global_doc_freq.get(w, 0) + 1

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "categories": categories,
            "published": published_node.text,
            "updated": updated_node.text,
            "abstract_stats": {
                "total_words": total_words,
                "unique_words": unique_words,
                "total_sentences": len(sentences),
                "avg_words_per_sentence": total_words / len(sentences) if sentences else 0.0,
                "avg_word_length": avg_word_length,
                "longest_sentence_words": longest_sent,
                "shortest_sentence_words": shortest_sent,
                "top_20_words": top_20
            }
        })

    except Exception as e:
        write_log(f"Error parsing paper entry: {e}. Skipping.")
        continue

top_50_global = sorted(
    [{"word": w, "frequency": f, "documents": global_doc_freq[w]} for w, f in global_word_freq.items()],
    key=lambda x: (-x['frequency'], x['word'])
)[:50]

corpus_analysis = {
    "query": search_query,
    "papers_processed": len(papers),
    "processing_timestamp": get_iso_utc(),
    "corpus_stats": {
        "total_abstracts": total_abstracts,
        "total_words": global_total_words,
        "unique_words_global": len(global_word_freq),
        "avg_abstract_length": global_total_words / total_abstracts if total_abstracts else 0.0,
        "longest_abstract_words": longest_abstract if total_abstracts > 0 else 0,
        "shortest_abstract_words": shortest_abstract if total_abstracts > 0 else 0
    },
    "top_50_words": top_50_global,
    "technical_terms": {
        "uppercase_terms": sorted(list(global_uppercase_terms)),
        "numeric_terms": sorted(list(global_numeric_terms)),
        "hyphenated_terms": sorted(list(global_hyphenated_terms))
    },
    "category_distribution": global_category_dist
}

with open(os.path.join(output_dir, "papers.json"), "w", encoding="utf-8") as f:
    json.dump(papers, f, indent=2)

with open(os.path.join(output_dir, "corpus_analysis.json"), "w", encoding="utf-8") as f:
    json.dump(corpus_analysis, f, indent=2)

processing_time = time.perf_counter() - start_time
write_log(f"Completed processing: {len(papers)} papers in {processing_time:.2f} seconds")
