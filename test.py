from langsmith import traceable
from langsmith import Client
import os

##LANGSMITH_TRACING=true
#LANGCHAIN_TRACING_V2=true
#LANGSMITH_ENDPOINT=https://api.smith.langchain.com
#LANGSMITH_API_KEY=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
#LANGSMITH_PROJECT=AI_File_Insight_Agent
#GOOGLE_API_KEY=AIzaSyAHKslPTAmVCohERhQUlqLkNgrH9FeQpmw
#OPENAI_API_KEY=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

from dotenv import load_dotenv
load_dotenv()


# Print each LangSmith-related environment variable
print("LANGCHAIN_TRACING_V2:", os.getenv("LANGCHAIN_TRACING_V2"))
print("LANGCHAIN_API_KEY:", os.getenv("LANGSMITH_API_KEY"))
print("LANGCHAIN_ENDPOINT:", os.getenv("LANGSMITH_ENDPOINT"))

raw_url = os.getenv("LANGSMITH_ENDPOINT", "")
clean_url = raw_url.replace("\\x3a", ":").replace("%3a", ":")

client = Client(
    api_url=clean_url,
    api_key=os.getenv("LANGSMITH_API_KEY")
)

@traceable(name="Example Run")
def add(x, y):
    return x + y

add(1, 2)
