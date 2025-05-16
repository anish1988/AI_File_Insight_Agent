import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
# Load environment variables from .env file

load_dotenv()

# initialize the tracer

if os.getenv("LANGCHAIN_TRACING_V2","false").lower() == "true":
    tracer = LangChainTracer()
    # Create a callback manager with the tracer
    callback_manager = CallbackManager([tracer])


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

            if file_type == "CSV":
                try:
                    uploaded_file.seek(0)  # Reset the file pointer to the beginning
                    df.csv = pd.read_csv(uploaded_file)

                    st.subheader("📊 CSV File Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}")
            elif file_type == "TXT" or file_type == "X-LOG":
                st.subheader("📄 Text File Preview")
                st.text_area("File Content", content, height=300)
                st.subheader("🧠 AI Insights")
                st.write(
                    "This is where the AI insights will be displayed after processing the file."
                )
                # Add your AI processing logic here
                # For example, you can call a function to analyze the content and display the results
                # insights = analyze_file_content(content)
                # st.write(insights)
            else:
                st.error("Unsupported file type. Please upload a .txt, .log, or .csv file.")
        else:
            st.error("Error reading the file. Please check the file format and try 11 again.")
    else:
        st.info("Please upload a file to get started.")
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
        content = uploaded_file.read().decode("utf-8")
        return content, file_type
    else:
        return None, None
if __name__ == "__main__":
    main()
# This is a simple file insight agent that uses the Gemini API to analyze files and provide insights.
# The code uses Streamlit for the web interface and pandas for data manipulation.
# The agent can handle .txt, .log, and .csv files.
# The code includes a file uploader, file preview, and a placeholder for AI insights.
# The AI insights section is currently a placeholder and can be implemented with the desired AI processing logic.
# The code also includes error handling for file reading and unsupported file types.
# The agent is designed to be user-friendly and provides a simple interface for users to upload files and view insights.
# The code is structured to be easily extendable for future enhancements and additional features.
