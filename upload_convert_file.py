import re
from typing import List, Dict
import streamlit as st


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

def convert_content_binary_json(content: str,log_type) -> List[Dict[str, dict]]:
    pattern_type = LOG_PATTERNS.get(log_type)
    print(f"Pattern type: {pattern_type}")
    pattern = re.compile(pattern_type)
    print(f"Pattern: {pattern}")
   # log_text = "\n".join(
    #    [f"{content['timestamp']} - {content['level']} - {content['code']} - {content['message']}"
    print(f"Content: {content}")
    # Decode the content if it's in bytes
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    print(f"Decoded content: {content}")
    results = []
    for match in pattern.finditer(content):
        results.append( match.groupdict())
    
    return results
