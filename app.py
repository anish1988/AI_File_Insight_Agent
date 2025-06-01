import streamlit as st
import pandas as pd
import re
import json
import asyncio
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from fpdf import FPDF
from io import BytesIO
from diskcache import Cache

# Setup persistent cache
cache = Cache("./.cache")

# Define regex patterns for different log types
LOG_PATTERNS = {
    "apache": r"\[(.*?)\] \[([a-zA-Z]+)\] \[client (.*?)\] (.*?)$",
    "php": r"\[.*?\] PHP (.*?) in (.*?) on line (\d+)",
    "laravel": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (local\.ERROR|production\.ERROR): (.*?)(\{.*?\})",
    "asterisk": r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] (ERROR|WARNING): (.*?)$"
}

# Rule-based categorization
def categorize_error(log):
    if "SQL" in log or "database" in log.lower():
        return "Database Error"
    elif "timeout" in log.lower():
        return "Timeout Error"
    elif "undefined" in log.lower():
        return "Code/Logic Error"
    elif "permission" in log.lower():
        return "Permission Error"
    else:
        return "General Error"

# Detect log type
def detect_log_type(content):
    for log_type, pattern in LOG_PATTERNS.items():
        if re.search(pattern, content.decode(errors="ignore")):
            return log_type
    return "unknown"

# Extract unique entries using regex
def extract_unique_entries(content, log_type):
    decoded = content.decode(errors="ignore")
    pattern = LOG_PATTERNS.get(log_type)
    if not pattern:
        return []

    entries = re.findall(pattern, decoded)
    unique_entries = list({str(entry) for entry in entries})
    return unique_entries

# Async summarization
async def summarize_logs(log_entries):
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    prompt = ChatPromptTemplate.from_template("Summarize this log entry:\n{log}")

    tasks = []
    for entry in log_entries:
        cached = cache.get(entry)
        if cached:
            tasks.append(asyncio.sleep(0, result=cached))  # simulate coroutine
        else:
            chain = prompt | llm
            tasks.append(chain.ainvoke({"log": entry}))

    results = await asyncio.gather(*tasks)

    for i, entry in enumerate(log_entries):
        cache[entry] = results[i].content if hasattr(results[i], "content") else results[i]

    return [r.content if hasattr(r, "content") else r for r in results]

# Export to Excel
def export_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# Export to PDF
def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for i, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{i+1}. {row['log']}\nSummary: {row['summary']}\nCategory: {row['category']}\n", border=1)
    
    output = BytesIO()
    pdf.output(output)
    return output.getvalue()

# --- Streamlit UI ---
st.title("🧠 AI Log Analyzer")

uploaded_file = st.file_uploader("Upload a binary log file", type=["log", "txt", "bin"])

if uploaded_file:
    content = uploaded_file.read()
    log_type = detect_log_type(content)

    st.info(f"Detected log type: **{log_type}**")

    log_entries = extract_unique_entries(content, log_type)
    if not log_entries:
        st.warning("No log entries matched.")
    else:
        with st.spinner("Summarizing logs..."):
            summaries = asyncio.run(summarize_logs(log_entries))

        df = pd.DataFrame({
            "log": log_entries,
            "summary": summaries,
            "category": [categorize_error(log) for log in log_entries]
        })

        st.success("✅ Summary complete!")

        st.dataframe(df)

        col1, col2 = st.columns(2)
        with col1:
            excel = export_excel(df)
            st.download_button("📥 Download Excel", excel, file_name="log_summary.xlsx")
        with col2:
            pdf = export_pdf(df)
            st.download_button("📥 Download PDF", pdf, file_name="log_summary.pdf")
