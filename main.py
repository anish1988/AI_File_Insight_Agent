import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client
from langchain.callbacks.manager import CallbackManager
from summarizer import summarize_logs,summarize_log_entries  # Import the summarization function
from upload_convert_file import load_file, convert_content_binary_json
from export_log import export_pdf, export_excel
from log_type import detect_log_type,extract_unique_entries,categorize_error
from log_format_detector import analyze_log_format
from file_utils import detect_log_type, read_log_file,launch_ui,chunk_large_file,get_error_suggestions,normalize_logs,export_suggestions,normalize_log_file_content


# Load environment variables from .env file

load_dotenv()


# initialize the tracer
if os.getenv("LANGCHAIN_TRACING_V2","false").lower() == "true":
    tracer = LangChainTracer()
    # Create a callback manager with the tracer
    callback_manager = CallbackManager([tracer])



# main function to run the Streamlit app
def main():
    
       # Step 1: Launch Streamlit UI to upload a log file
       file_path = launch_ui()

       # Step 2: Detect log type and read content
       log_type = detect_log_type(file_path)
       content = read_log_file(file_path)

       print(f"Detected log type: {log_type}")

       # Step 3: Chunk large file if needed
       chunks = chunk_large_file(content)
       #print(f"Number of chunks created: {len(chunks)}")
       #print(f"First chunk content: {chunks[0][:100]}...")  # Display first 100 characters of the first chunk
       # Display chunks in Streamlit DataFrame

       if chunks:
           df_chunks = pd.DataFrame({'Chunk Number': range(1, len(chunks)+1), 'Content': chunks})
           st.subheader("🔍 Log Chunks Preview")
           st.dataframe(df_chunks, use_container_width=True)
       else:
           st.error("No valid log chunks found. Please check the file content.")
           


       # Step 4: Send chunks to LLM for log analysis and pattern discovery
       if not chunks:
           raise ValueError("No valid log chunks found. Please check the file content.")
       
       if len(chunks) <= 5:
           selected_chunks = chunks
           #print(f"Using all {len(chunks)} chunks for analysis.")
       else:
           selected_chunks = [chunks[0]]
       #print(f"Selected {len(selected_chunks)} chunks for analysis.")
       #print("Type of selected_chunks:", type(selected_chunks))
       #print("Sample content:", selected_chunks[:1])
       regex_patterns = get_error_suggestions(selected_chunks, mode="pattern_discovery")

       print(f"Discovered regex patterns: {regex_patterns}")
         # Display regex patterns in Streamlit
       st.subheader("🔍 Discovered Regex Patterns")

       if regex_patterns:
           st.json(regex_patterns, expanded=False)
       else:
           st.error("No regex patterns were discovered. Please check the log content or try a different file.")
       

       # Step 5: Normalize binary or plain logs to JSON using discovered patterns
       #normalized_logs = normalize_logs(content, regex_patterns)
       normalized_logs = normalize_log_file_content(content)

       print(f"Number of normalized log entries: {len(normalized_logs)}")
       # Display normalized logs in Streamlit
       st.subheader("📜 Normalized Log Entries")


       if normalized_logs:
          st.json(normalized_logs[:5], expanded=False)
       else:
          st.error("No normalized log entries found. Please check the regex patterns or log content.")
       

       for idx, error_entry in enumerate(normalized_logs, start=1):
           print(f"Processing error #{idx}: {error_entry}")
           # Display error entry in Streamlit
           #st.subheader("🔍 Error Entry")
           # Display the error entry 
           #st.info(f"Error Entry: {error_entry}")
              # Send to LLM for summarization
           summaries = summarize_log_entries(error_entry) 
           print(f"Summaries: {summaries}")
          
           df = pd.DataFrame({
                            "log": error_entry,
                            "Message": summaries[0]["message"],
                            "summary": summaries[0]["summary"],
                            "fix_suggestion": summaries[0]["fix_suggestion"],
                            "code_fix": summaries[0]["code_fix"],
                            "code_location": summaries[0]["code_location"],
                            "resources": [", ".join(summaries[0]["resources"])]
                        })
           st.success("✅ Summary complete!")
           st.dataframe(df) 
          
       sys.exit(0)
            #send_to_llm(error_entry)
           

       # Step 6: Export the structured logs
       export_suggestions(normalized_logs, output_path="data/cleaned/structured_logs.json")

       # Step 7: Display summary in Streamlit
       st.subheader("✅ Log Summary")
       st.success(f"{len(normalized_logs)} structured log entries have been generated.")

        # Optional: Show first few entries
       st.json(normalized_logs[:5], expanded=False)

       # Optional: Offer download
       with open("data/cleaned/structured_logs.json", "rb") as f:
        st.download_button("📥 Download Structured Logs", f, file_name="structured_logs.json", mime="application/json")


            
            

# call the main function to run the app
# 

if __name__ == "__main__":
    main()
    # Run the Streamlit app
    # asyncio.run(main())          