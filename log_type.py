import re
# Define regex patterns for different log types
LOG_PATTERNS = {
    "apache": r"\[(.*?)\] \[([a-zA-Z]+)\] \[client (.*?)\] (.*?)$",
    "php": r"\[.*?\] PHP (.*?) in (.*?) on line (\d+)",
    "laravel": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (local\.ERROR|production\.ERROR): (.*?)(\{.*?\})",
    "asterisk": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (ERROR|WARNING): (.*?)$",
    #"etc": r"\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*?)$",  # Generic pattern
    "Mysql" : r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) '
        r'(?P<thread_id>\d+) '
        r'\[(?P<level>\w+)] '
        r'\[(?P<code>MY-\d+)] '
        r'\[(?P<source>\w+)] '
        r'(?P<message>.+)'
}

# Rule-based categorization
def categorize_error(log):
    print(f"Categorizing log: {log}")
    return "erriror"  # Placeholder for actual categorization logic;

# Detect log type
def detect_log_type(content):
    for log_type, pattern in LOG_PATTERNS.items():
        if re.search(pattern, content.decode("utf-8",errors="ignore")):
            return log_type
    return "unknown"

# Extract unique entries using regex
def extract_unique_entries(content, log_type):
    decoded = content.decode("utf-8",errors="ignore")
    pattern = LOG_PATTERNS.get(log_type)
    if not pattern:
        return []

    #entries = re.findall(pattern, decoded)
    #unique_entries = list({str(entry) for entry in entries})
    #return unique_entries
    results = []
    for match in pattern.finditer(content):
        results.append( match.groupdict())
    
    return results
