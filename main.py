from collections import defaultdict
import logging
import os
from fastapi.params import Query
from fastapi.staticfiles import StaticFiles

import openai
import tiktoken
import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests_cache import install_cache

from scam_comment_id.id_spam import IdentifySpam
from scam_comment_id.youtube_comments import (
    CommentThread,
    extract_video_id,
    get_youtube_comments,
)

load_dotenv()
install_cache("demo_cache", backend="sqlite", expire_after=3600)

openai.api_key = os.getenv("OPENAI_API_KEY")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

app = FastAPI(api_key=os.getenv("API_KEY"))
app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="templates")


def count_tokens(messages):
    total_tokens = 0
    enc = tiktoken.get_encoding('"gpt-3.5-turbo"')
    for message in messages:
        # Considering only 'user' and 'assistant' message types for token counting
        if "role" in message:
            tokens = len(enc.encode(message["content"])) + len(
                enc.encode(message["role"])
            )
            total_tokens += tokens

    return total_tokens


@app.post(
    "/id_spam", response_model=tuple[list[list[str]], list[CommentThread]]
)
def id_spam(
    video_url: str = Body(),
    batch_size: int = Body(5),
    total_results: int = Body(20),
) -> tuple[list[list[str]], list[CommentThread]]:
    comments = get_youtube_comments(
        os.getenv("YOUTUBE_API_KEY"),
        extract_video_id(video_url),
        total_results=total_results,
    )[:total_results]

    batches = [
        comments[i : batch_size + i]
        for i in range(0, len(comments), batch_size)
    ]
    results = []
    identify_spam = IdentifySpam()
    for batch in batches:
        response_text, usage = identify_spam.analyze_comments(batch)
        logging.info(f"Usage: {usage}")
        results.append(response_text)

    return results, comments


@app.route("/", methods=["GET", "POST"])
async def index(request: Request, result: str = Query(None)):
    if request.method == "POST":
        form = await request.form()
        video_url = form.get("video_url")
        if video_url:
            batch_size = 5  # Set your default batch_size if needed
            total_results = 20  # Set your default total_results if needed
            spam_users, comments = id_spam(video_url, batch_size, total_results)
            spam_users = [
                user_id
                for user_id_list in spam_users
                for user_id in user_id_list
            ]
            comment_dict = defaultdict(list)
            for comment in comments:
                comment_dict[comment.author_id].append(comment.text)
                for reply in comment.replies:
                    comment_dict[reply.author_id].append(reply.text)
            result = {
                key: value
                for key, value in comment_dict.items()
                if key in spam_users
            }
    else:
        result = None
    return templates.TemplateResponse(
        "index.html", {"request": request, "result": result}
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app)
