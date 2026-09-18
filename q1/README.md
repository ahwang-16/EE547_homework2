# Problem 1: Docker Basics – HTTP Data Fetcher


This project contains a Python application packaged within a Docker container. It reads a list of URLs from an input file, performs HTTP GET requests, and computes statistics about the responses. The script is built entirely using **Python standard library modules** (no third-party packages).

## Files Included
* `fetch_and_process.py`: The core Python script that handles the HTTP requests, word counting, and data logging.
* `Dockerfile`: The configuration file to build the Docker image using `python:3.11-slim`.
* `test_urls.txt`: The input list of URLs to be processed.
* `README.md`: This documentation file.

## Prerequisites
* **Docker** must be installed and running on your machine.

## How to Build the Image
Open your terminal, navigate to the directory containing the `Dockerfile`, and run the following command:

```bash
docker build -t http-fetcher:latest .
