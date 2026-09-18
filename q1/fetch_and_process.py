import sys
import time
import json
import os
import re
import datetime
import urllib.error
import urllib.request

if len(sys.argv) != 3:
    print("Error: You must provide exactly two arguments")
    print("Usage: python fetch_and_process.py <input_file> <output_dir>")
    sys.exit(1)

input_file = sys.argv[1]
output_dir = sys.argv[2]

os.makedirs(output_dir, exist_ok=True)

def get_iso_utc():
    dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

try:
    with open(input_file, "r") as file:
        urls = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"Error: could not find the file at {input_file}")
    sys.exit(1)

total_urls = len(urls)
successful_requests = 0
failed_requests = 0
total_bytes = 0
status_distribution = {}
successful_time_sum = 0.0

responses_data = []
errors_log_lines = []

processing_start = get_iso_utc()

for url in urls:
    status_code = None
    content_length = None
    word_count = None
    error_msg = None

    timestamp = get_iso_utc()
    start_time = time.perf_counter()

    try:
        try:
            response = urllib.request.urlopen(url, timeout=10)
        except urllib.error.HTTPError as e:
            response = e

        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        status_code = response.status
        body = response.read()
        content_length = len(body)

        content_type = response.headers.get("Content-Type", "").lower()
        if "text" in content_type:
            text_content = body.decode("utf-8", errors="ignore")
            word_count = len(re.findall(r'[a-zA-Z0-9]+', text_content))

        status_str = str(status_code)
        status_distribution[status_str] = status_distribution.get(status_str, 0) + 1
        total_bytes += content_length

        if 200 <= status_code < 300:
            successful_requests += 1
            successful_time_sum += response_time_ms
        else:
            failed_requests += 1

    except Exception as e:
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        error_msg = str(e)
        failed_requests += 1

        errors_log_lines.append(f"[{timestamp}] {url}: {error_msg}\n")

    responses_data.append({
        "url": url,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "content_length": content_length,
        "word_count": word_count,
        "timestamp": timestamp,
        "error": error_msg
    })

processing_end = get_iso_utc()

if successful_requests > 0:
    avg_response_time = successful_time_sum / successful_requests
else:
    avg_response_time = 0.0

summary_data = {
    "total_urls": total_urls,
    "successful_requests": successful_requests,
    "failed_requests": failed_requests,
    "average_response_time_ms": avg_response_time,
    "total_bytes_downloaded": total_bytes,
    "status_code_distribution": status_distribution,
    "processing_start": processing_start,
    "processing_end": processing_end
}

# File 1: responses.json
with open(os.path.join(output_dir, "responses.json"), "w") as f:
    json.dump(responses_data, f, indent=2)

# File 2: summary.json
with open(os.path.join(output_dir, "summary.json"), "w") as f:
    json.dump(summary_data, f, indent=2)

# File 3: errors.log
with open(os.path.join(output_dir, "errors.log"), "w") as f:
    f.writelines(errors_log_lines)

print(f"Processing complete! Check the '{output_dir}' directory for outputs.")
