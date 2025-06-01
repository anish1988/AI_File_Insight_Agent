# ai_file_agent/summarizer.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
#from langchain_google_genai.google_generativeai import ChatGoogleGenerativeAI
import os
import sys 
import asyncio
import re
import json
from dotenv import load_dotenv
from diskcache import Cache


load_dotenv()

# Setup persistent cache
cache = Cache("./.cache")

# Prepare prompt and LLM globally once
prompt = ChatPromptTemplate.from_template(
        """You are an AI log analysis assistant. 

        Analyze the following log message and provide a **concise and human-readable summary** of the issue, including any **deprecated features, warnings, or errors** mentioned. 

        If it's already self-explanatory, return a clear one-line explanation without repeating the exact original message.

        Log message:
        {{message}}"""
        )

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

chain: Runnable = prompt | llm


def summarize_logs_1(log_entries):
    summaries = []

    for entry in log_entries:
        log_text = entry.get("message", "No message provided.")
        
        try:
            response = chain.invoke({"log_data": log_text})
            summaries.append({
                "log_text": log_text,
                "summary": response.content
            })
        except Exception as e:
            summaries.append({
                "log_text": log_text,
                "error": f"Error processing log entry: {str(e)}"
            })

    return summaries

# Async summarization
async def summarize_logs_2(log_entries):
    print(f"Log entries: {log_entries}")
    llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    prompt = ChatPromptTemplate.from_template(
        """You are an AI log analysis assistant. 

        Analyze the following log message and provide a **concise and human-readable summary** of the issue, including any **deprecated features, warnings, or errors** mentioned. 

        If it's already self-explanatory, return a clear one-line explanation without repeating the exact original message.

        Log message:
        {{message}}"""
        ) 
    chain: Runnable = prompt | llm
    summaries = []
    for entry in log_entries:
        # Extract only message parts
        messages = entry["message"]
        #log_text = "\n".join(
        #[f"{entry['timestamp']} - {entry['level']} - {entry['code']} - {entry['message']}" for entry in log_entries]
        
       # )
        print(f"Messages to be print : {messages}")
        cache_key = json.dumps(messages, sort_keys=True)  # Convert dict to JSON string
        cached = cache.get(cache_key)
        if cached:
            summaries.append(asyncio.sleep(0, result=cached))  # simulate coroutine
        else:
            #chain = prompt | llm
            try:
                response = chain.invoke({"log": messages})
                print(f"Response: {response}")
                summaries.append({
                    "log_text": messages,
                    "summary": response.content
                })
            except Exception as e:
                summaries.append({
                    "log_text": messages,
                    "error": f"Error processing log entry: {str(e)}"
                })

    results = await asyncio.gather(*summaries)

   # for i, entry in enumerate(log_entries):
    #    cache[entry] = results[i].content if hasattr(results[i], "content") else results[i]

    #return [r.content if hasattr(r, "content") else r for r in results]
    # Cache the results
    for result in results:
            cache_key = json.dumps(result["log_text"], sort_keys=True)  # Convert dict to JSON string
            cache[cache_key] = result
            cache[result["log_text"]] = result
    
    return results


# ai_file_agent/summarizer.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
#from langchain_google_genai.google_generativeai import ChatGoogleGenerativeAI
import os
import sys 
import asyncio
import re
import json
from dotenv import load_dotenv
from diskcache import Cache


load_dotenv()

# Setup persistent cache
cache = Cache("./.cache")

# Prepare prompt and LLM globally once
prompt = ChatPromptTemplate.from_template(
    "You are an AI log analysis assistant. Analyze the following log message and provide a **concise and human-readable summary** of the issue, including any **deprecated features, warnings, or errors** mentioned. If it's already self-explanatory, return a clear one-line explanation without repeating the exact original message.\n\nLog message:\n\n{{message}}"
)

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

chain: Runnable = prompt | llm

async def summarize_logs(log_entries):
    summaries = []

    async def run_chain(entry):
        message = entry["message"]
        cache_key = json.dumps(entry["message"], sort_keys=True)

        cached = cache.get(cache_key)
        
        if cached:
            print(f"Sending to LLM cache: {message}")
            return {"message": message, "summary": cached}

        try:
            print(f"Sending to LLM: {message}")
            result = await chain.ainvoke({"message": message})
            summary = result.content
            cache[cache_key] = summary
            return {"message": message, "summary": summary}
        except Exception as e:
            return {"message": message, "error": str(e)}

    # Create tasks to run chain on each message one-by-one
    tasks = [run_chain(entry) for entry in log_entries]
    summaries = await asyncio.gather(*tasks)

    return summaries



##################################################################################################################################################################

# ai_file_agent/summarizer.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
#from langchain_google_genai.google_generativeai import ChatGoogleGenerativeAI
import os
import sys 
import asyncio
import re
import json
from dotenv import load_dotenv
from diskcache import Cache


load_dotenv()

# Setup persistent cache
cache = Cache("./.cache")

# Prepare prompt and LLM globally once
prompt = ChatPromptTemplate.from_template(
    """You are an expert log analysis assistant helping developers debug backend applications.
    
You will be given a log entry in JSON format that contains:
- A `message`: a short description of the error or issue.
- An `exception`: the detailed stack trace or exception message, if available.

Your job is to:
1. Analyze the `message` and `exception` together.
2. Summarize the **root cause** of the issue in clear, developer-friendly terms.
3. Suggest **a likely fix** or next step if one is obvious.
4. Avoid simply repeating the input — rephrase and clarify.

If `message` is vague or empty, fall back to `exception` for insight.  
Always return a concise explanation in **1–3 lines**, without boilerplate or disclaimers.

Respond with:
- Root cause of the error
- Why it happens
- How to fix it (if known)

Here is the log Entry:
{{message}}
"""
)


llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

chain: Runnable = prompt | llm

async def summarize_logs(log_entries):
    summaries = []

    async def run_chain(entry):
        #message = log_entries#entry["message"]
        message = json.dumps({
                    "message": entry.get("message", ""),
                    "exception": entry.get("exception", "")
                }, indent=2)
        cache_key = json.dumps(log_entries, sort_keys=True)

        cached = cache.get(cache_key)
        
        if cached:
            print(f"Sending to LLM cache: {message[0]}")
            return {"message": message[0], "summary": cached}

        try:
            print(f"Sending to LLM: {message[0]}")
            result = await chain.ainvoke({"message": message[0]})
            summary = result.content
            cache[cache_key] = summary
            return {"message": message[0], "summary": summary}
        except Exception as e:
            return {"message": message, "error": str(e)}

    # Create tasks to run chain on each message one-by-one
    tasks = [run_chain(entry) for entry in log_entries]
    summaries = await asyncio.gather(*tasks)

    return summaries



