from langsmith import traceable
from langsmith import Client
import os

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
