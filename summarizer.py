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
import uuid
import traceback
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")

# Suppress watchdog debug logs by setting its level to WARNING or ERROR
logging.getLogger("watchdog").setLevel(logging.WARNING)
logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)

# Prompt template to analyze log messages and exceptions
#
# prompt = ChatPromptTemplate.from_template(
LOG_PROMPT_TEMPLATE = """
You are a highly skilled log analysis assistant helping developers troubleshoot and debug backend systems.

You will be given a single log entry (in plain text, JSON, or list format), which may come from any type of backend system including but not limited to:
- MySQL, Apache, NGINX, PHP, Python, Java, Node.js, Laravel, Asterisk, etc.

The log may include warnings, errors, exceptions, deprecation notices, stack traces, or performance issues.

---

🔍 Analyze the log content carefully and perform the following tasks:

1. **Understand the log context**: Use both `message` and `exception` (if present) to infer what went wrong.
2. **Identify the technology or system** involved (e.g. MySQL, PHP, etc.) based on log content , log text or keywords.
3. **Summarize the root cause** in developer-friendly language — rephrase the error clearly.
4. **Suggest a likely fix or mitigation step** that is relevant to the identified system.
5. **Provide a code/config fix example**, if applicable.
6. **Point the developer to where to look** (e.g., a config file, function, database setting).
7. **List 5 reliable and system-specific online resources or docs** that can help solve this problem.

---



📌 **Important Notes**:
- Treat every log entry as a **unique and independent** problem, regardless of similarity to previous logs.
- Do **not** reuse or repeat explanations given for earlier entries.
- Avoid generic or unrelated error explanations.
- Focus on accuracy and relevance to the given log entry.
- If the log is a deprecation warning, do **not** treat it as an exception or crash.
- If the technology is not explicitly stated, infer carefully but do not assume unrelated error types.


---


Return your response as a **well-formatted JSON object** with these exact fields:

{{
  "message": "<Brief, human-readable summary of the log error>",
  "summary": "<Concise root cause explanation>",
  "fix_suggestion": "<Clear, actionable advice for resolving the issue>",
  "code_fix": "<Example code/config adjustment with reasoning, if applicable>",
  "code_location": "<Where to apply or investigate the fix in the code/configuration>",
  "resources": ["<URL or resource title>", "..."]
}}

📌 **Additional Notes**:

- Tailor the solution based on the detected **tech stack** (MySQL, PHP, etc.).
- Do **not assume** Java or NullPointerException unless clearly indicated.
- Do **not invent** error types that don’t match the input.
- Keep explanations concise but technically helpful (2–4 lines max).

---

Log Entry:
{log_entry}
"""

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
       # print("type of result_text:", type(result_text))
       # print(f"LLM response content New:\n{result_text}\n")
        #sys.exit(0)
        json_result = json.loads(result_text)
      #  print(f"LLM Json response content:\n{json_result}\n")
      #  print("type of result_text:", type(json_result))
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
            log_entry = {
                "message": log_text,
                "exception": None,
                "request_id": str(uuid.uuid4())  # Ensure uniqueness
            }
            print(f"Log entry  content:\n{log_entry}\n")
            #sys.exit(0)
            prompt = LOG_PROMPT_TEMPLATE.format(log_entry=log_text)
            #prompt = LOG_PROMPT_TEMPLATE.format(log_entry=json.dumps(log_entry, indent=2))
            print(f"LLM prompt content:\n{prompt}\n")
            #sys.exit(0)
            summary = call_llm(prompt)
            print(f"LLM summary content:\n{summary}\n")
           # print("type of summary:", type(summary))
            #sys.exit(0)
          #  if not summary.get("message") or not summary.get("summary"):
           #     logger.warning(f"⚠️ Entry {entries}: LLM did not return expected fields. Retrying...")
            

           # summaries.append(summary)
            if isinstance(summary, dict) and summary.get("message") and summary.get("summary"):
                summaries.append(summary)
            else:
                raise ValueError(f"Unexpected LLM output format: {summary}")

    except Exception as e:
            #logger.error(f"❌ Failed to summarize entry {entries}: {e}")
            logger.error(f"❌ Failed to summarize entry {entries}: {e}\n{traceback.format_exc()}")
            summaries.append({
                "message": f"Failed to analyze log entry {entries}",
                "summary": str(e),
                "fix_suggestion": None,
                "code_fix": None,
                "code_location": None,
                "resources": []
            })

    logger.info(f"✅ Total summarized entries: {len(summaries)}")
    #print(f"Summaries: {summaries}")
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
