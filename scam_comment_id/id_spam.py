import json
from pathlib import Path
from typing import Optional

import openai
from pydantic import BaseModel

from scam_comment_id.youtube_comments import CommentThread
from easyllm.clients import huggingface


class IdSpamConfig(BaseModel):
    video_url: Optional[str] = None
    youtube_api_key: str = None
    max_samples: int = 100


class IdentifySpam:
    # read comments.json
    commnets = json.loads(Path("comments.json").read_text())

    example_spam_thread = {
        "spam_key": [False] * 6 + [True] * 2,
        "thread": {
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
                {
                    "author_id": "UCZpajTn91kfoD3rJeOABVbw",
                    "text": "91.000 I I 😮7",
                },
                {
                    "author_id": "UC_h8A9kS4800JkaX6dgtuvw",
                    "text": "go away bots",
                },
            ],
        },
    }
    example_real_thread = {
        "spam_key": [False] * 4,
        "thread": {
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
        },
    }

    example_author_included_thread = {
        "spam_key": [False] * 6,
        "thread": {
            "author_id": "UCpHmN_PEbYEYzoIJqCHeQsg",
            "text": "Joseph’s verbal communication is top notch. No prompt no pauses no “ums”",
            "replies": [
                {
                    "author_id": "UC2kXE-XesSMRJi6gBRL28oQ",
                    "text": "he edits them out",
                },
                {
                    "author_id": "UCEK6isS61sN3bxGlxUtxMww",
                    "text": "@AlexSuperTrampthere really aren’t that many cuts man",
                },
                {
                    "author_id": "UCpHmN_PEbYEYzoIJqCHeQsg",
                    "text": "@AlexSuperTramp you are wrong",
                },
                {
                    "author_id": "UC2kXE-XesSMRJi6gBRL28oQ",
                    "text": "I am not wrong",
                },
                {
                    "author_id": "UCfCT7SSFEWyG4th9ZmaGYqQ",
                    "text": "That&#39;s what recording over 400 youtube videos does! When I first started I would say &quot;uhm&quot; &quot;like&quot; &quot;ahh&quot; a lot more. I do more cuts in videos now due to chopping out segments or reducing length to make it flow better. (this video for example I cut out a small section that I thought was a bit repetitive)",
                },
            ],
        },
    }

    example_real_comment = {
        "spam_key": [False],
        "thread": {
            "author_id": "UCZX0ln_wUph8KXqK6zqoIpA",
            "text": "In my opinion none of the streaming/media stocks are the place to be. Not even Netflix. It’s a tough business where it’s hard to make money and competition is fierce. Netflix is overvalued. It’s foolish to think they will have good growth to meet their valuation.<br>To be honest, Joseph is too much of a gut feeling investor. He believed in Disney at $160. Now he does something similar with Netflix. But the truth is, Netflix is priced to perfection. The downside risk is quite big.",
            "replies": [],
        },
    }

    system_message = {
        "role": "system",
        "content": """You are a content moderator for a popular social media site. 
        You are tasked with identifying scam comments. 
        The following is a list of comments that you have been asked to review. 
        return a list containing spam users' author_id. Please be very conservative with your spam detection.
        Most scam comments are in threads with other scam comments. They tend to talk abou ther personal experience with invest and how some guru helped them. You should never classify a comment as spam if it is not in a thread with other spam comments.
        Remeber we are going to ban theses users so we want to be very sure they are scamming""",
    }

    def __init__(self) -> None:
        example_inputs, example_response = self.process_example(
            examples=[
                self.example_real_thread,
                self.example_spam_thread,
                self.example_author_included_thread,
                self.example_real_comment,
            ]
        )
        self.example_interaction = [
            self.system_message,
            {"role": "user", "content": example_inputs},
            {"role": "assistant", "content": example_response},
        ]

    @staticmethod
    def process_example(examples: list[dict]):
        example_inputs = []
        example_response = []
        for example in examples:
            example_inputs.append(f"Comment Thread: {example['thread']}")
            if example["spam_key"][0]:
                example_response.append(example["thread"]["author_id"])
            for i, key in enumerate(example["spam_key"][1:]):
                if key:
                    example_response.append(example["thread"]["replies"][i]["author_id"])
        return "\n|".join(example_inputs), json.dumps(example_response)

    def generate_prompt(self, comments: list[CommentThread]) -> str:
        string_threads = [f"Comment Thread: {thread.model_dump()}" for thread in comments]
        user_message = [{"role": "user", "content": "\n|".join(string_threads)}]
        return self.example_interaction + user_message

    def analyze_comments(
        self, comments: list[CommentThread], max_tokens: int = 1000
    ) -> tuple[list[Optional[str]], dict[str, int]]:
        messages = self.generate_prompt(comments)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
        )
        response_text = json.loads(response.choices[0]["message"]["content"])
        return response_text, dict(response.usage)

    # helper to build llama2 prompt
    def llama2_prompt(messages):
        huggingface.prompt_builder = "llama2"

        response = huggingface.ChatCompletion.create(
            model="meta-llama/Llama-2-70b-chat-hf",
            messages=[
                {
                    "role": "system",
                    "content": "\nYou are a helpful assistant speaking like a pirate. argh!",
                },
                {"role": "user", "content": "What is the sun?"},
            ],
            temperature=0.9,
            top_p=0.6,
            max_tokens=256,
        )

        print(response)
