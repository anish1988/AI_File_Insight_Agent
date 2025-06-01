# src/utils/file_utils.py

import streamlit as st
import os
import tempfile
import chardet
import math

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import re
import logging
from typing import List, Dict, Tuple, Union



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
SUPPORTED_LOG_TYPES = ["apache", "nginx", "laravel", "php", "asterisk", "mysql"]

# src/streamlit_app/app.py



def launch_ui():
    st.set_page_config(page_title="AI Log Analyzer", layout="wide")
    st.title("🔍 AI-Powered Error Log Detector")
    st.write("Upload a log file (e.g., Apache, NGINX, PHP, Laravel, Asterisk) to begin analysis.")

    uploaded_file = st.file_uploader("📁 Choose a log file", type=["log", "txt", "conf", "json", "out"])

    if uploaded_file is not None:
        # Create a temp file to store the uploaded content
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"File uploaded successfully: {uploaded_file.name}")
        return file_path

    # Prevent the rest of the pipeline from running until a file is uploaded
    st.stop()

def detect_log_type(file_path: str) -> str:
    """
    Detect log type based on file name heuristics and first few lines of content.
    """
    filename = os.path.basename(file_path).lower()
    for log_type in SUPPORTED_LOG_TYPES:
        if log_type in filename:
            return log_type

    with open(file_path, 'rb') as f:
        raw = f.read(1024)
        encoding = chardet.detect(raw)['encoding']
    
    with open(file_path, 'r', encoding=encoding or 'utf-8', errors='ignore') as f:
        head = f.read(1000).lower()
        for log_type in SUPPORTED_LOG_TYPES:
            if log_type in head:
                return log_type

    return "unknown"


def read_log_file(file_path: str) -> str:
    """
    Reads a log file with encoding detection.
    """
    with open(file_path, 'rb') as f:
        raw = f.read()
        encoding = chardet.detect(raw)['encoding']

    return raw.decode(encoding or 'utf-8', errors='ignore')




def chunk_large_file(content: str, max_chunk_size: int = 5000) -> list[str]:
    """
    Splits the log content into manageable chunks.

    Parameters:
    - content (str): The entire log file content as a string.
    - max_chunk_size (int): Maximum size (in characters) of each chunk. Default is 5000.

    Returns:
    - list[str]: A list of chunked log segments.

    Raises:
    - ValueError: If content is empty or not a string.
    """
    if not isinstance(content, str):
        raise ValueError("Log content must be a string.")

    if not content.strip():
        raise ValueError("Log content is empty.")

    total_length = len(content)
    if total_length <= max_chunk_size:
        return [content.strip()]  # Return single cleaned chunk

    num_chunks = math.ceil(total_length / max_chunk_size)
    chunks = [
        content[i * max_chunk_size:(i + 1) * max_chunk_size].strip()
        for i in range(num_chunks)
    ]

    # Filter out empty chunks just in case
    return [chunk for chunk in chunks if chunk]






def get_error_suggestions(chunks: List[str], mode: str = "pattern_discovery") -> List[str]:
    """
    You are an expert in log analysis and parsing.

    Your task is to:
    1. Analyze the provided log chunk(s).
    2. Detect the **log type** (such as Laravel, Apache, NGINX, Asterisk, MySQL, Docker, etc.).
    3. Based on the identified log type, generate a **single regex pattern** that matches all or most lines in the chunk.
    4. The regex must extract **named groups** using the `(?P<name>...)` syntax for important fields like:
    - timestamp
    - log_level
    - service/module (if applicable)
    - message
    - exception type (optional)
    - stacktrace (if multiline or nested, indicate how to handle it)

    🔸 Example Output Format:
    {
    "log_type": "Laravel",
    "regex_pattern": "(?P<timestamp>\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\]) (?P<log_level>[a-zA-Z\\.]+): (?P<message>.*?)\\s*\\{.*"
    }

    ❗️Constraints:
    - Your output must be JSON with keys `log_type` and `regex_pattern`.
    - The `regex_pattern` must be valid Python regex and support parsing with `re.match()` or `re.compile()`.
    - Ensure all capture groups are named and cover as many fields as possible from the logs.
    - If a stack trace or multi-line section is detected, mention if further processing is required (e.g., using a `\n` separator).

    🧪 Input Logs:
    {log_chunk}
    """

    if not isinstance(chunks, list) or not all(isinstance(c, str) for c in chunks):
        raise ValueError("Chunks must be a list of strings.")
    
    if not chunks:
        raise ValueError("Chunks list is empty.")

    if mode not in ["pattern_discovery", "error_suggestion"]:
        raise ValueError("Invalid mode. Use 'pattern_discovery' or 'error_suggestion'.")

    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", max_tokens=3024)
        patterns = []

        for idx, chunk in enumerate(chunks):
            prompt = build_prompt(chunk, mode)
            logger.info(f"Sending chunk {idx+1}/{len(chunks)} to LLM...")

            response = llm([HumanMessage(content=prompt)])
            patterns.append(response.content.strip())

        return patterns

    except Exception as e:
        logger.exception("LLM call failed")
        raise RuntimeError(f"LLM analysis failed: {e}")


def build_prompt(chunk: str, mode: str) -> str:
    """
    Constructs the prompt for the LLM based on the selected mode.

    Parameters:
    - chunk (str): The chunk of log content.
    - mode (str): The mode of prompt generation.

    Returns:
    - str: Prompt to send to LLM.
    """
    if mode == "pattern_discovery":
        return (
            "You are an expert in analyzing log files.\n"
            "Your task is to identify the log format and return a regex pattern "
            "that can parse the following log entries:\n\n"
            f"{chunk}\n\n"
            "Return only the regex pattern without explanation."
        )

    elif mode == "error_suggestion":
        return (
            "You are a developer assistant. Given the following log entries:\n\n"
            f"{chunk}\n\n"
            "Identify key errors and suggest possible resolutions or insights."
        )

LOG_PATTERNS = {
    "laravel": r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',
    "apache": r'\[\w+ \w+ \d{2} \d{2}:\d{2}:\d{2}.\d+ \d{4}\]',
    "nginx": r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}',
    "asterisk": r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',
    "syslog": r'^\w{3} \d{1,2} \d{2}:\d{2}:\d{2}'
}

# Function to try extracting JSON from log using pattern
def extract_json_logs(log_text: str, regex_pattern: str) -> List[Dict[str, str]]:
    structured_logs = []
    try:
        regex = re.compile(regex_pattern)
        for line in log_text.splitlines():
            if not line.strip():
                continue
            match = regex.match(line)
            if match:
                entry = match.groupdict()
                if entry:
                    structured_logs.append(entry)
        return structured_logs
    except Exception as e:
        logger.warning(f"Regex compilation or matching failed: {e}")
        return []

 # Function to split logs generically
def split_log_entries(log_text: str) -> Tuple[str, List[str]]:
    print("Starting to split log entries...")
    logger.info("Starting to split log entries...")
    log_type, pattern = detect_log_format(log_text)
    if not pattern:
        raise ValueError("Unknown log format")
    entries = re.split(f'(?={pattern})', log_text)
    return log_type, [e.strip() for e in entries if e.strip()]



# Function to detect log type
def detect_log_format(log_text: str) -> Tuple[Union[str, None], Union[str, None]]:
    for name, pattern in LOG_PATTERNS.items():
        if re.search(pattern, log_text):
            return name, pattern
    return None, None


# Main normalization logic
def normalize_log_file_content(log_text: str) -> List[Union[Dict[str, str], str]]:
    log_type, pattern = detect_log_format(log_text)
    print(f"Detected log type: {log_type}")
    print(f"Pattern used for detection: {pattern}")
    st.info(f"Detected log type: {log_type}")
    st.info(f"Pattern used for detection: {pattern}")

    if not pattern:
        logger.error("No pattern matched the log content.")
        raise ValueError("Unsupported or unknown log format.")

    logger.info(f"Detected log type: {log_type}")

    # Try JSON conversion
    structured = extract_json_logs(log_text, pattern)
    print(f"Structured logs after JSON extraction: {structured}")
    st.info(f"Structured logs after JSON extraction: {structured}")
    logger.info(f"Structured logs after JSON extraction: {structured}")
    if structured and isinstance(structured, list) and all(isinstance(entry, dict) for entry in structured):
        logger.info(f"Parsed {len(structured)} structured entries.")
        st.info(f"Parsed {len(structured)} structured entries.")
        print(f"Parsed {len(structured)} structured entries.")
        # Display structured logs in Streamlit
        st.subheader("📜 Normalized Log Entries")
        st.json(structured[:5], expanded=False)
        
    if structured:
        logger.info(f"Parsed {len(structured)} structured entries.")
        return structured

    # Fallback: return split raw entries if JSON conversion fails
    _, entries = split_log_entries(log_text)
    logger.warning("Falling back to raw entry splitting (non-JSON).")
    return entries


def normalize_logs(chunks: List[str], regex_patterns: List[str]) -> List[Dict[str, str]]:
    """
    Normalize log entries into structured JSON format using regex patterns.

    Parameters:
    - chunks (List[str]): List of log text chunks.
    - regex_patterns (List[str]): Regex patterns corresponding to each chunk.

    Returns:
    - List[Dict[str, str]]: List of parsed log entries as structured JSON.

    Raises:
    - ValueError: For invalid inputs or mismatches.
    - RuntimeError: If no logs are successfully parsed.
    """
    # Validate inputs
    print(f"Length Chunks: {len(chunks)}")
    print(f"Length Regex Patterns: {len(regex_patterns)}")
    print(f"Type of regex patterns:", type(regex_patterns))
    print(f"print of regres: {regex_patterns}")

    # Validate inputs
    logger.debug(f"Number of Chunks: {len(chunks)}")
    logger.debug(f"Number of Regex Patterns: {len(regex_patterns)}")


    if not chunks or not isinstance(chunks, list) or not all(isinstance(c, str) for c in chunks):
        raise ValueError("Chunks must be a non-empty list of strings.")

    if not regex_patterns or not isinstance(regex_patterns, list) or not all(isinstance(p, str) for p in regex_patterns):
        raise ValueError("Regex patterns must be a non-empty list of strings.")
    
   # if len(chunks) != len(regex_patterns) and len(regex_patterns) != 0:
    #    raise ValueError("The number of chunks must match the number of regex patterns.")

    if "(?<" in regex_patterns:  # quick check for JS-style groups
        regex_patterns = convert_js_named_groups_to_python(regex_patterns)
    
    print(f"Converted regex patterns: {regex_patterns}")
    structured_logs = []

    for idx, (chunk, pattern) in enumerate(zip(chunks, regex_patterns)):
        logger.info(f"Normalizing chunk {idx+1}/{len(chunks)} with pattern.")
        logger.debug(f"\n🔍 Normalizing chunk {idx+1}/{len(chunks)}")
        logger.debug(f"Regex Pattern: {pattern}")

        try:
            fixed_pattern = sanitize_and_validate_regex(pattern)
            regex = re.compile(fixed_pattern)
        except re.error as e:
            logger.warning(f"Invalid regex at index {idx}: {e}")
            continue  # Skip invalid regex

        for line_no, line in enumerate(chunk.splitlines(), start=1):
            if not line.strip():
                logger.debug(f"Line {line_no}: Skipping empty line.")
                continue

            match = regex.match(line)
            if match:
                entry = match.groupdict()
                logger.debug(f"✅ Line {line_no}: Match found -> {entry}")
                if entry:
                    structured_logs.append(entry)
                else:
                    logger.debug(f"⚠️ Line {line_no}: Match returned empty groupdict.")
            else:
                logger.debug(f"❌ Line {line_no}: No match for line: {line}")

    if not structured_logs:
        logger.error("❌ No logs were successfully normalized. Check your patterns and log format.")
        raise RuntimeError("No logs were successfully normalized. Please check patterns or log format.")

    logger.info(f"✅ Total structured logs normalized: {len(structured_logs)}")
    return structured_logs






def convert_js_named_groups_to_python(pattern: str) -> str:
    """
    Converts JS-style named groups (?<name>...) to Python-style (?P<name>...).
    Returns the converted pattern.
    """
    # Replace JS-style named groups with Python-style
    converted = re.sub(r'\(\?<([a-zA-Z_][a-zA-Z0-9_]*)>', r'(?P<\1>', pattern)
    
    # Validate regex
    try:
        re.compile(converted)
    except re.error as e:
        raise ValueError(f"Converted regex is still invalid: {e}")
    
    return converted



#logger = logging.getLogger(__name__)


def export_suggestions(logs: List[Dict[str, str]], output_path: str) -> None:
    """
    Export the normalized logs to a JSON file.

    Parameters:
    - logs (List[Dict[str, str]]): List of structured log entries.
    - output_path (str): File path where JSON should be saved.

    Raises:
    - ValueError: If logs are empty or improperly formatted.
    - OSError: If the output directory cannot be created.
    - IOError: If writing the file fails.
    """

    # Validation
    if not logs or not isinstance(logs, list) or not all(isinstance(entry, dict) for entry in logs):
        raise ValueError("Logs must be a non-empty list of dictionaries.")

    if not output_path or not isinstance(output_path, str) or not output_path.endswith(".json"):
        raise ValueError("Output path must be a valid JSON file path.")

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    except Exception as e:
        raise OSError(f"Failed to create directory for output: {e}")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)
        logger.info(f"Exported structured logs to: {output_path}")
    except Exception as e:
        raise IOError(f"Failed to write JSON file: {e}")





def sanitize_and_validate_regex(raw_pattern: str) -> str:
    """
    Converts JS-style named groups to Python-style, and validates the pattern.
    Logs clear errors if conversion or compilation fails.
    
    Parameters:
    - raw_pattern: str - The regex pattern to sanitize and validate

    Returns:
    - str: A valid Python-compatible regex pattern
    """
    if not isinstance(raw_pattern, str):
        raise ValueError("Regex pattern must be a string.")

    # Step 1: Convert JS-style named groups (?<name>) -> (?P<name>)
    try:
        converted = re.sub(r"\(\?<([a-zA-Z_][a-zA-Z0-9_]*)>", r"(?P<\1>", raw_pattern)
    except Exception as e:
        logger.error(f"Regex conversion failed: {e}")
        raise ValueError(f"Failed to convert regex named groups: {e}")

    # Step 2: Validate regex compilation
    try:
        re.compile(converted)
    except re.error as e:
        logger.error(f"Regex compile error: {e}")
        raise ValueError(f"Invalid Python regex after conversion: {e}")

    return converted
