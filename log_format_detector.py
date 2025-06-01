from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Set your API key in environment or directly
#os.environ["OPENAI_API_KEY"] = "your-openai-key"
# Load environment variables from .env file

load_dotenv()
# Define prompt
log_type_prompt = ChatPromptTemplate.from_template("""
You are a log format classification assistant.
Given the content of a log file, analyze and determine:

1. What system it belongs to (e.g., Apache, NGINX, Laravel, MySQL, Asterisk, Python, NodeJS, etc.).
2. A regex pattern to extract individual log entries from the given content.
3. A short explanation for your choice.

Content:

{log_content}
                                                   

Respond strictly in JSON format:
{{
  "log_type": "...",
  "regex_pattern": "...",
  "explanation": "..."
}}
                                                   
""")

# Function to analyze log type and regex
def analyze_log_format(log_content: str):
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
)
    chain = log_type_prompt | llm

    try:
        response = chain.invoke({"log_content": log_content})
        return response.content  # JSON-like string
    except Exception as e:
        return {"error": str(e)}
