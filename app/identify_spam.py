import json
from pathlib import Path
from typing import Optional, List
import openai
from pydantic import BaseModel

class SpamAuthor(BaseModel):
    author_id: str
    reason: str
    evidence: str

class ThreadSpam(BaseModel):
    list: List[SpamAuthor]

class IdentifySpam:
    system_message = {
        "role": "system",
        "content": (
            "You are a content moderator for a popular social media site. "
            "You are tasked with identifying scam comments. "
            "The following is a list of comments that you have been asked to review. "
            "Return a JSON list of objects, each with 'author_id' and 'reason' fields, for users you are very certain are spamming. "
            "Most scam comments are in threads with other scam comments. They tend to talk about their personal experience with invest and how some guru helped them. "
            "You should never classify a comment as spam if it is not in a thread with other spam comments. "
            "Remember we are going to ban these users so we want to be very sure they are scamming."
        ),
    }

    def __init__(self):
        pass

    def generate_prompt(self, thread_dict):
        # thread_dict: dict with 'author_id', 'text', 'replies' (list of dicts)
        return [
            self.system_message,
            {"role": "user", "content": f"Comment Thread: {json.dumps(thread_dict)}"}
        ]

    def analyze_thread(self, thread_dict, max_tokens=256) -> List[SpamAuthor]:
        messages = self.generate_prompt(thread_dict)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
            response_format=ThreadSpam
        )
        response_data = response.choices[0].message.content
        thread_spam = ThreadSpam.parse_obj(response_data)
        # Validate and parse with Pydantic
        return thread_spam.list
