# Problem 2: ArXiv Paper Metadata Processor

This project is a containerized Python application that queries the ArXiv API, fetches academic paper metadata, and performs detailed text analysis on paper abstracts. Built entirely with Python standard library modules, it extracts technical terms, calculates word and sentence statistics, filters stopwords, and outputs structured JSON data.

## Files Included
* `arxiv_processor.py`: The main application script that handles API requests, XML parsing, rate-limiting, and text processing.
* `stopwords.py`: A provided module containing a set of common English stopwords used to filter text during analysis.
* `Dockerfile`: The configuration file to build the Docker image using `python:3.11-slim`.
* `README.md`: This documentation file.

## Prerequisites
* **Docker** must be installed and running on your system.

## How to Build the Image
Open your terminal, navigate to the directory containing the project files, and run the following command to build the Docker image:

```bash
docker build -t arxiv-processor:latest .
