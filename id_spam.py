import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Optional

import openai
import requests
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from youtube_comments import CommentThread


class IdSpamConfig(BaseModel):
    video_url: Optional[str] = None
    youtube_api_key: str = None
    max_samples: int = 100


class IdentifySpam:
    # read comments.json
    commnets = json.loads(Path("comments.json").read_text(), indent=4)

    example_spam_thread = {
        "author_id": "UCk9cKkw28WknylZNuKtNCFQ",
        "text": "I feel incredibly fortunate for having made wise financial choices that have had a life-altering impact. As a single father residing in Toronto, Canada, I successfully purchased my second home in September. If everything continues to progress positively, my aspiration is to retire next year at the age of 50.",
        "replies": [
            {
                "author_id": "UCk9cKkw28WknylZNuKtNCFQ",
                "text": "&quot;I have experienced significant returns since I started engaging in financial transactions with Louise Amanda Mussell. Her approach to financial management is truly outstanding, offering remarkable insights and tactics that have greatly contributed to my success.&quot;",
            },
            {
                "author_id": "UCWHFp_u5BGNHV8QNERdTxmw",
                "text": "Congratulations on your achievements! It&#39;s great to see you doing so well. I understand that I am currently facing financial difficulties at the age of 45, and I am interested in receiving some helpful tips to improve my situation. Owning your own house is a significant goal for you, and it&#39;s a wonderful aspiration.",
            },
            {
                "author_id": "UCk9cKkw28WknylZNuKtNCFQ",
                "text": "I apologize for the delayed response. I successfully organized my finances by adopting the principles of the FIRE (Financial Independence, Retire Early) movement. With the guidance of an investment professional, I ventured into stocks, cryptocurrencies, and real estate investments, which played a significant role in my financial success.&quot;",
            },
            {
                "author_id": "UCWHFp_u5BGNHV8QNERdTxmw",
                "text": "I appreciate your kind response. I&#39;m interested in connecting with a financial consultant similar to the one who assisted you in achieving your financial goals.&quot;",
            },
            {
                "author_id": "UC_h8A9cCZ0n7wEZX6dgtuvw",
                "text": "I will be forever grateful to MRS. Louise Amanda Mussell for the profound transformation she brought to my life. Through her guidance, I was able to overcome significant financial debt with just a small investment. I am immensely thankful and will continue to share her  name with the world, as she has truly saved me.",
            },
            {"author_id": "UCZpajTn91kfoD3rJeOABVbw", "text": "91.000 I I 😮7"},
            {
                "author_id": "UC_h8A9kS4800JkaX6dgtuvw",
                "text": "go away bots",
            },
        ],
    }
    example_real_thread = {
        "author_id": "UClvWus5raDbU3IqR51HdNZw",
        "text": "&quot;I don&#39;t feel they&#39;re making the relevant products&quot; as 97% of SP100 companies use their products lol.",
        "replies": [
            {
                "author_id": "UCJdPT3_JtX1WhRzkVU3Il4g",
                "text": "what is that? mainframe?",
            },
            {
                "author_id": "UClvWus5raDbU3IqR51HdNZw",
                "text": "@Allen Lee 47 out of 50 SP50 companies use IBM hybrid cloud. Additionally lots of companies use their consulting. Ie ORCL for example, which JC mentions",
            },
            {
                "author_id": "UCZrw69IACLewNSX-m7u0tpw",
                "text": "I wouldn&#39;t be surprised if AVGO buys IBM after they are finished with Vmware.",
            },
        ],
    }

    system_message = {
        "role": "system",
        "content": """You are a content moderator for a popular social media site. 
        You are tasked with identifying scam comments. 
        The following is a list of comments that you have been asked to review. 
        return a list containing spam users' author_id. Please be very conservative with your spam detection.
        Most scam comments are in threads with other scam comments. 
        Remeber we are going to ban theses users so we want to be very sure they are scamming""",
    }

    def __init__(self) -> None:
        example_inputs = "\n|".join(
            [
                f"Comment Thread: {thread}"
                for thread in [
                    self.example_spam_thread,
                    self.example_real_thread,
                ]
            ]
        )
        example_response = json.dumps(
            [self.example_spam_thread["author_id"]]
            + [reply["author_id"] for reply in self.example_spam_thread["replies"][:-2]]
        )
        self.example_interaction = [
            self.system_message,
            {
                "role": "user",
                "content": example_inputs,
            },
            {
                "role": "assistant",
                "content": example_response,
            },
        ]

    def generate_prompt(self, comments: list[CommentThread]) -> str:
        return self.example_interaction + [
            {
                "role": "user",
                "content": "\n|".join(
                    [f"Comment Thread: {thread.model_dump()}" for thread in comments]
                ),
            }
        ]

    def analyze_comments(
        self, comments: list[CommentThread], max_tokens: int = 1000
    ) -> tuple[list[str], dict[str, int]]:
        dynamic_max_tokens = len(self.example_interaction[2]["content"]) * (
            len(comments) / 2
        )
        messages = self.generate_prompt(comments)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
            # max_tokens=int(dynamic_max_tokens)
            # if dynamic_max_tokens < max_tokens
            # else max_tokens,
        )
        response_text = json.loads(response.choices[0]["message"]["content"])
        return response_text, dict(response.usage)


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=j4yXw7NBzbY&t=878s"
    data = {"video_url": video_url, "batch_size": 5, "total_results": 25}
    response = requests.post(
        "http://127.0.0.1:8000/id_spam",
        json=jsonable_encoder(data),
        headers={"api_key": os.getenv("API_KEY")},
    )
    spam_users, comments = response.json()
    spam_users = [user_id for user_id_list in spam_users for user_id in user_id_list]
    print(response.json())
    comment_dict = defaultdict(list)
    for comment in comments:
        comment_dict[comment["author_id"]].append(comment["text"])
        for reply in comment["replies"]:
            comment_dict[reply["author_id"]].append(reply["text"])
    filtered_dict = {
        key: value for key, value in comment_dict.items() if key in spam_users
    }
    print("done")
