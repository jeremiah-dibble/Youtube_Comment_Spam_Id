import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Comment(BaseModel):
    author_id: str
    text: str


class Reply(Comment):
    pass


class CommentThread(Comment):
    replies: list[Reply]


def extract_video_id(url: str):
    pattern = r"(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com\/(?:watch\?.*v=|embed\/)|\.be\/)([\w\-]+)(?:.*)"
    match = re.match(pattern, url)
    if match:
        return match.group(1)
    else:
        return None


def get_youtube_comments(
    api_key: str, video_id: str, maxResults=100, total_results=300
) -> list[CommentThread]:
    comments = []

    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": api_key,
        "videoId": video_id,
        "part": "snippet, replies",
        "maxResults": maxResults,
        "order": "relevance",
    }

    while len(comments) < total_results:
        response = requests.get(base_url, params=params)
        video_response = response.json()

        for item in video_response["items"]:
            replies = []
            if "replies" in item.keys():
                replies = [
                    Reply(
                        author_id=relply["snippet"]["authorChannelId"]["value"],
                        text=relply["snippet"]["textDisplay"],
                    )
                    for relply in item["replies"]["comments"]
                ]
            comments.append(
                CommentThread(
                    author_id=item["snippet"]["topLevelComment"]["snippet"][
                        "authorChannelId"
                    ]["value"],
                    text=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                    replies=replies,
                )
            )

        if "nextPageToken" in video_response:
            params["pageToken"] = video_response["nextPageToken"]
        else:
            break

    return comments


if __name__ == "__main__":
    dev_key = os.getenv("YOUTUBE_API_KEY")
    video_url = "https://www.youtube.com/watch?v=j4yXw7NBzbY&t=878s"
    comments = get_youtube_comments(dev_key, extract_video_id(video_url))
    # save comments to json file

    Path("comments.json", "w").write_text(
        json.dumps(list(map(lambda x: x.model_dump(), comments)), indent=4)
    )

    print(comments)
