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
    "You are an AI log analysis assistant. Analyze the following log entry or log entry message  and write a concise summary:\n\n{{log_entries}}"
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
async def summarize_logs(log_entries):
    print(f"Log entries: {log_entries}")
    llm = ChatOpenAI(model="gpt-3", temperature=0)
    prompt = ChatPromptTemplate.from_template("You are an AI log analysis assistant. Analyze the following single log entry or log entry message and Write a concise summary of the each of the node  following::\n\n{{log_entries}}")
    chain: Runnable = prompt | llm
    summaries = []
    for entry in log_entries:
        # Extract only message parts
        messages = entry["message"]
        #log_text = "\n".join(
        #[f"{entry['timestamp']} - {entry['level']} - {entry['code']} - {entry['message']}" for entry in log_entries]
        
       # )
        print(f"Messages to be print : {messages}")
        cached = cache.get(messages)
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
        if "log_text" in result and "summary" in result:
            cache[result["log_text"]] = result
    
    return results