from openai import OpenAI
import os
import json


def parse_email(email_text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
Extract the following fields from this trip request email and return ONLY valid JSON:
- origin
- destination
- date
- passenger_count

Example Output:
{{
  "origin": "San Francisco",
  "destination": "Las Vegas",
  "date": "May 20th",
  "passenger_count": 4
}}

Email:
{email_text}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You extract structured JSON trip data from emails."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    return json.loads(content)

