import streamlit as st
import pandas as pd
import os
import re
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
from summarizer import summarize_logs  # Import the summarization function
from upload_convert_file import load_file, convert_content_binary_json
from export_log import export_pdf, export_excel
from log_type import detect_log_type,extract_unique_entries,categorize_error

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
            log_type = detect_log_type(content)
            st.info(f"Detected log type: **{log_type}**")

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
                st.subheader("📄 Json Data Preview")
                st.text_area("File Content", log_entries, height=300)
                st.subheader("📊 Log File Preview")
                df = pd.DataFrame(log_entries)
                st.dataframe(df.head(10), use_container_width=True)
                print(f"Log entries111: {log_entries}")
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
