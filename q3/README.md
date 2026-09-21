# Problem 3: Multi-Container Text Processing Pipeline

This project implements a multi-container batch processing pipeline using Docker
Compose. The application processes web content through sequential stages, with
three distinct Python containers coordinating their execution via status markers
in a shared Docker volume. 

The pipeline extracts text from raw HTML, computes document-level statistics,
and performs a corpus-wide analysis including word frequencies, n-grams, and
Jaccard document similarity—all using only Python standard library modules.

## Architecture

The pipeline consists of three sequential services:
1. **Fetcher (`pipeline-fetcher`)**: Reads target URLs, downloads the raw HTML,
and saves the pages to the shared volume.
2. **Processor (`pipeline-processor`)**: Waits for the fetcher to complete,
extracts raw text/links/images from the HTML using regular expressions,
calculates document-level statistics (word, sentence, and paragraph counts), and
outputs processed JSON files.
3. **Analyzer (`pipeline-analyzer`)**: Waits for the processor to complete,
reads the processed text, and computes global corpus statistics, including the
top 100 words, top bigrams/trigrams, and Jaccard similarity between all document
pairs.

## Directory Structure

```text
q3/
├── docker-compose.yaml      # Docker Compose configuration
├── run_pipeline.sh          # Bash orchestration script
├── fetcher/
│   ├── Dockerfile
│   └── fetch.py             # Downloads HTML from URLs
├── processor/
│   ├── Dockerfile
│   └── process.py           # Extracts text and computes document stats
└── analyzer/
    ├── Dockerfile
        └── analyze.py           # Computes global stats and document similarity
