# rule_filter.py

import json
import os
import re
from openai import OpenAI

def extract_json_from_text(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return []


def apply_nl_rule(rule: str, aircrafts: list, extra_context: str = "") -> list:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
You are an AI assistant that filters aircrafts based on user rules and context.

Aircraft data:
{json.dumps(aircrafts, indent=2)}

Context (weather, routing, etc.):
{extra_context}

Apply the rule: "{rule}"
Return only a JSON list of aircrafts that match the rule.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    return extract_json_from_text(content)
