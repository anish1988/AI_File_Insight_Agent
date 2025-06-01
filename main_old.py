import streamlit as st
import pandas as pd
import os
import re
import asyncio
import sys
import json
from typing import List, Dict
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
from summarizer import summarize_logs  # Import the summarization function
from upload_convert_file import load_file, convert_content_binary_json
from export_log import export_pdf, export_excel
from log_type import detect_log_type,extract_unique_entries,categorize_error
from log_format_detector import analyze_log_format

# Load environment variables from .env file

load_dotenv()

# initialize the tracer

if os.getenv("LANGCHAIN_TRACING_V2","false").lower() == "true":
    tracer = LangChainTracer()
    # Create a callback manager with the tracer
    callback_manager = CallbackManager([tracer])

# Your actual logic goes here
async def run_async_logic(log_entries):
    summaries = await summarize_logs(log_entries)
    return summaries
def main():
    st.set_page_config( 
        page_title="GeminiLens: AI File Insight Agent",
        page_icon=":guardsman:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("GeminiLens: AI File Insight Agent")
    st.write(
        "This is a simple file insight agent that uses the Gemini API to analyze files and provide insights.Upload a `.txt`, `.log`, or `.csv` file to preview its contents."
    )

    uploaded_file = st.file_uploader(
        "Upload a file", type=["txt", "log", "csv"], label_visibility="collapsed"
    )

    if uploaded_file is not None:
        content,file_type = load_file(uploaded_file)
        if content:
            st.subheader("🔍 File Preview (First 500 characters)")
            st.code(content[:5000], language="text")
            #log_type = detect_log_type(content)
            print(f"File content: {content}")
            log_type = analyze_log_format(content)
            st.info(f"Detected log type: **{log_type}**")
            print(f"Type of content: {type(content)}")
            #sys.exit(0)
            print(f"Log type resily: {log_type}")
            # If `log_type` is bytes, decode it to string
            if isinstance(log_type, bytes):
                log_type = log_type.decode('utf-8')

            # Now parse the JSON string to a Python dict
           # if isinstance(log_type, str):
              #  log_type = log_type.strip()
                # Optional: fix escape chars if needed
              #  log_type = log_type.replace("\\", "\\\\")
               # log_type = json.loads(log_type)
         #   print(log_type.get("name", "unknown"))    
            # Escape backslashes BEFORE loading JSON
         #   log_type = log_type.strip()
            print("RAW log_type string:\n", log_type)
            #sys.exit(0)
            # Optional: Try escaping backslashes if regex is in the string
          #  try:
           #     log_type = json.loads(log_type)
           # except json.JSONDecodeError as e:
            #    print("Initial JSON decode failed, trying to escape and reload")
             #   log_type = log_type.replace('\\', '\\\\')
              #  log_type = json.loads(log_type)
            #print("RAW log_type string:\n", log_type)
            #log_type = json.loads(log_type)
            df = pd.DataFrame([{
                "Log Type": log_type["log_type"],
                "Expression": log_type["regex_pattern"],
                "Explanation": log_type["explanation"],
                #"Detailed Regex": log_type["detailed_regex_pattern"]
            }])
            st.dataframe(df)
            print(f"Log type: {log_type['log_type']}")
            #sys.exit(0)
            if file_type == "CSV":
                try:
                    uploaded_file.seek(0)  # Reset the file pointer to the beginning
                    df.csv = pd.read_csv(uploaded_file)
                    st.subheader("📊 CSV File Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}")
            elif file_type == "TXT" or file_type == "X-LOG":
                st.subheader("📜 Text File Preview")
                st.text_area("File Content", content, height=300)
                st.subheader("🧠 AI Insights")
                st.write(
                            "This is where the AI insights will be displayed after processing the file."
                        )
                #log_entries = extract_unique_entries(content, log_type)
                log_entries = convert_content_binary_json(content, log_type)
                print(json.dumps(log_entries, indent=2))
                st.subheader("📄 Json Data Preview")
                st.text_area("File Content", log_entries, height=300)
                st.subheader("📊 Log File Preview")
                df = pd.DataFrame(log_entries)
                st.dataframe(df.head(10), use_container_width=True)
                print(f"Log entries111: {log_entries}")
                #sys.exit(0)
                if not log_entries:
                    st.warning("No log entries matched.")
                else:
                    with st.spinner("Summarizing logs..."):
                        # Extract only message parts
                        #messages = [entry["message"] for entry in log_entries]
                        #summaries =  await summarize_logs(log_entries)#await summarize_logs(log_entries)
                        summaries = asyncio.run(run_async_logic(log_entries))
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
        else:
            st.error("Error reading the file. Please check the file format and try 11 again.")
    else:
        st.info("Please upload a file to get started.")

if __name__ == "__main__":
    #asyncio.run(main())
    main()
# This is a simple file insight agent that uses the Gemini API to analyze files and provide insights.
# The code uses Streamlit for the web interface and pandas for data manipulation.
# The agent can handle .txt, .log, and .csv files.
# The code includes a file uploader, file preview, and a placeholder for AI insights.
# The AI insights section is currently a placeholder and can be implemented with the desired AI processing logic.
# The code also includes error handling for file reading and unsupported file types.
# The agent is designed to be user-friendly and provides a simple interface for users to upload files and view insights.
# The code is structured to be easily extendable for future enhancements and additional features.

#            if log_entries:    
#               st.subheader("📊 Log Entries" ) 
#               st.json(log_entries[:10])  # Display first 10 entries for brevity
#            if log_type:
#               st.subheader("📂 Log Type Details")
#              st.json(log_type)
#            if log_entries:
#               st.subheader("🔍 Log Analysis")
#               summaries = asyncio.run(summarize_logs(log_entries))
#               st.json(summaries[:10])  # Display first 10 summaries for brevity
#            if log_entries:
#               st.subheader("📊 Unique Entries"
# #               unique_entries = extract_unique_entries(log_entries)
#              unique_entries = extract_unique_entries(log_entries)
# #               st.json(unique_entries[:10])  # Display first 10 unique entries for brevity
#              st.json(unique_entries)  # Display all unique entries
#          if log_entries:
# #             st.subheader("📂 Categorized Errors"
# #             categorized_errors = categorize_error(log_entries)
#             categorized_errors = categorize_error(log_entries)
#             st.json(categorized_errors)  # Display categorized errors
 """           if log_entries:
                st.subheader("📊 Log Entries")
                st.json(log_entries[:10])
            if log_type:
                st.subheader("📂 Log Type Details")
                st.json(log_type)
            if log_entries:
                st.subheader("🔍 Log Analysis")
                summaries = asyncio.run(summarize_logs(log_entries))
                st.json(summaries[:10])
            if log_entries:
                st.subheader("📊 Unique Entries")
                unique_entries = extract_unique_entries(log_entries)
                st.json(unique_entries)
            if log_entries:
                st.subheader("📂 Categorized Errors")
                categorized_errors = categorize_error(log_entries)
                st.json(categorized_errors)
            if log_entries:
                st.subheader("📥 Export Options")
                if st.button("Export to PDF"):
                    export_pdf(log_entries, file_type)
                    st.success("PDF exported successfully!")
                if st.button("Export to Excel"):
                    export_excel(log_entries, file_type)
                    st.success("Excel exported successfully!")
        else:
            st.error("Error reading the file. Please check the file format and try again.")
    else:
        st.info("Please upload a file to get started.")
"""