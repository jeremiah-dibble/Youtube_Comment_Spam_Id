import re

from dotenv import load_dotenv
from googleapiclient.discovery import build
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

    # base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    youtube = build("youtube", "v3", developerKey=api_key)
    params = {
        "key": api_key,
        "videoId": video_id,
        "part": "snippet, replies",
        "maxResults": maxResults,
        "order": "relevance",
    }

    while len(comments) < total_results:
        # response = requests.get(base_url, params=params)
        response = youtube.commentThreads().list(**params).execute()
        # video_response = response.json()
        # print('video_response', video_response)
        # for item in video_response["items"]:
        for item in response.get("items", []):
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

        if "nextPageToken" in response.keys():
            params["pageToken"] = response.get("nextPageToken")
        else:
            break

    return comments



