import os
from collections import defaultdict
import requests
from fastapi.encoders import jsonable_encoder

if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=RNHytc79cSU"
    data = {"video_url": video_url, "batch_size": 5, "total_results": 5}
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