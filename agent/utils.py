import time
import re
from groq import RateLimitError, BadRequestError

def call_llm_with_retry(client, model, messages, tools=None, tool_choice=None, retries=5,max_tokens=800):
    for attempt in range(retries):
        try:
            kwargs = {"messages": messages, "model": model,"max_tokens":800}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            print(f"[DEBUG] full error: {e}")
            wait_match = re.search(r"try again in ([\d.]+)s", str(e))
            wait_time = float(wait_match.group(1)) + 0.5 if wait_match else 5
            print(f"[rate limit] waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        except BadRequestError as e:
            print(f"[retry {attempt+1}/{retries}] generation glitch: {e}")
            time.sleep(1)
    raise RuntimeError("LLM kept failing after retries")