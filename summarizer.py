# ai_file_agent/summarizer.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from openai import OpenAI
import os
import asyncio
import json
import time
import logging
import sys
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Prompt template to analyze log messages and exceptions
#
# prompt = ChatPromptTemplate.from_template(
LOG_PROMPT_TEMPLATE = """
  You are an expert log analysis assistant and debugging assistant helping developers debug backend applications.
     Analyze the following log entry and provide detailed insights.
    
You will be given a log entry in JSON/array/list format that contains:

- An `exception`: the detailed stack trace or exception message, if available.

Here is the log Entry:
{{log_entry}}

Your job is to:
1. Analyze the `message` and `exception` together.
2. Summarize the **root cause** of the issue in clear, developer-friendly terms.
3. Suggest **a likely fix** or next step if one is obvious.
4. Avoid simply repeating the input — rephrase and clarify.

If `message` is vague or empty, fall back to `exception` for insight.  
Always return a concise explanation in **1–3 lines**, without boilerplate or disclaimers.

Return the response in JSON format with the following fields:

1. "message": Clean summary of the log error.
2. "summary": Root cause analysis (what went wrong and why).
3. "fix_suggestion": A likely fix or next step the developer can take.
4. "code_fix": Example of code changes needed, with reasoning.
5. "code_location": Suggest where the developer should look in the codebase.
6. "resources": A list of 5 relevant online resources (URLs or titles) that may help resolve this.

IMPORTANT:
- Do NOT repeat the full log entry.
- Focus on rephrasing and explaining the actual error.
- Include developer-friendly and technically useful language.
- Always return a valid JSON object, or retry if generation fails.


"""
#)

# Initialize OpenAI chat model
#llm = ChatOpenAI(
  #  model="gpt-3.5-turbo",
   # temperature=0,
    #api_key=os.getenv("OPENAI_API_KEY")
#)

# Replace this with your actual OpenAI or compatible LLM client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create the chain to send prompt to LLM
#chain: Runnable = prompt | llm


#@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))

def call_llm(prompt: str) -> dict:
    """
    Call the LLM with retry and JSON output validation.
    """
    try:
        logger.debug("Calling LLM with prompt...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        result_text = response.choices[0].message.content.strip()
        # Strip Markdown JSON block if present
        if result_text.startswith("```json"):
            result_text = result_text.removeprefix("```json").strip()
        if result_text.endswith("```"):
            result_text = result_text.removesuffix("```").strip()
        logger.debug(f"Raw LLM response: {result_text}")
        print("type of result_text:", type(result_text))
        print(f"LLM response content New:\n{result_text}\n")
        #sys.exit(0)
        json_result = json.loads(result_text)
        print(f"LLM Json response content:\n{json_result}\n")
        print("type of result_text:", type(json_result))
        #sys.exit(0)
        if not isinstance(json_result, dict):
            raise ValueError("Invalid JSON response structure.")
        return json_result
    except Exception as e:
        logger.error(f"LLM call or JSON decode failed: {e}")
        raise

def summarize_log_entries(entries: List[Union[str, dict]]) -> List[dict]:
    """
    Summarize a single log entries using the LLM and return structured results.
    """
    summaries = []
    print(f"Total log entries to summarize: {entries}")
    
    try:
            logger.info(f"🔍 Summarizing log entry{entries}")
            log_text = json.dumps(entries) if isinstance(entries, dict) else str(entries)
            print(f"Log entry  content:\n{log_text}\n")
            #sys.exit(0)
            prompt = LOG_PROMPT_TEMPLATE.format(log_entry=log_text)

            summary = call_llm(prompt)
            print(f"LLM summary content:\n{summary}\n")
            print("type of summary:", type(summary))
            #sys.exit(0)
            if not summary.get("message") or not summary.get("summary"):
                logger.warning(f"⚠️ Entry {entries}: LLM did not return expected fields. Retrying...")
            

            summaries.append(summary)

    except Exception as e:
            logger.error(f"❌ Failed to summarize entry {entries}: {e}")
            summaries.append({
                "message": f"Failed to analyze log entry {entries}",
                "summary": str(e),
                "fix_suggestion": None,
                "code_fix": None,
                "code_location": None,
                "resources": []
            })

    logger.info(f"✅ Total summarized entries: {len(summaries)}")
    print(f"Summaries: {summaries}")
    return summaries

# Main summarization function
async def summarize_logs(log_entries):
    async def run_chain(entry):
        # Format log entry into JSON structure
        message = json.dumps({
            "message": entry.get("message", ""),
            "exception": entry.get("exception", "")
        }, indent=2)

        try:
            print(f"Sending to LLM:\n{message}")
            result = await chain.ainvoke({"message": message})
            summary = result.content
            return {"message": message, "summary": summary}
        except Exception as e:
            return {"message": message, "error": str(e)}

    # Run analysis concurrently
    tasks = [run_chain(entry) for entry in log_entries]
    return await asyncio.gather(*tasks)
