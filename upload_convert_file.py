import re
from typing import List, Dict, Union
import streamlit as st
import json
import sys


LOG_PATTERNS = {
    "apache": r"\[(.*?)\] \[([a-zA-Z]+)\] \[client (.*?)\] (.*?)$",
    "php": r"\[.*?\] PHP (.*?) in (.*?) on line (\d+)",
    "laravel": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (local\.ERROR|production\.ERROR): (.*?)(\{.*?\})",
    "asterisk": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (ERROR|WARNING): (.*?)$",
    #"etc": r"\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*?)$",  # Generic pattern
    "Mysql" : r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) (?P<thread_id>\d+) \[(?P<level>\w+)] \[(?P<code>MY-\d+)] \[(?P<source>\w+)] (?P<message>.+)"
        
}

def load_file(uploaded_file):
    """
    Load the content of the uploaded file based on its type.
    """
    file_type = uploaded_file.type.split("/")[1].upper()
    #print(f"File type: {file_type}")
    if file_type == "CSV":
        try:
            df = pd.read_csv(uploaded_file)
            return df, file_type
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            return None, None
    elif file_type == "TXT" or file_type == "X-LOG":
        content = uploaded_file.read()
        return content, file_type
    else:
        return None, None



def convert_content_binary_json(content: Union[str, bytes], log_type=None) -> List[Dict[str, Union[str, dict]]]:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    print(f"Content type: {type(content)}")
    print(f"Content length: {len(content)}")

    # Split based on log timestamp pattern
    log_chunks = re.split(r"(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\])", content)
    entries = []

    for chunk in log_chunks:
        if not chunk.strip():
            continue  # Skip empty parts

        # Extract timestamp
        ts_match = re.search(r"\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", chunk)
        env_match = re.search(r"\] (?P<env>\w+)\.(?P<level>\w+):", chunk)
        msg_match = re.search(r": (?P<msg>.+?)\n\{", chunk, re.DOTALL)

        json_start = chunk.find("{")
        json_data = chunk[json_start:] if json_start != -1 else ""

        try:
            exception_json = json.loads(json_data)
        except Exception:
            exception_json = json_data.strip()

        entry = {
            "timestamp": ts_match.group("timestamp") if ts_match else "",
            "environment": env_match.group("env") if env_match else "",
            "log_level": env_match.group("level") if env_match else "",
            "message": msg_match.group("msg").strip() if msg_match else "",
            "exception": exception_json
        }

        print("Parsed Entry:", entry)  # Remove in production
        entries.append(entry)

    return entries



