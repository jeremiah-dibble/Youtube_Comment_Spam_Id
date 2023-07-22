import json
import os
from pathlib import Path

from scam_comment_id.youtube_comments import (extract_video_id,
                                              get_youtube_comments)

if __name__ == "__main__":
    dev_key = os.getenv("YOUTUBE_API_KEY")
    video_url = "https://www.youtube.com/watch?v=j4yXw7NBzbY&t=878s"
    comments = get_youtube_comments(dev_key, extract_video_id(video_url))
    # save comments to json file

    Path("comments.json", "w").write_text(
        json.dumps(list(map(lambda x: x.model_dump(), comments)), indent=4)
    )

    print(comments)