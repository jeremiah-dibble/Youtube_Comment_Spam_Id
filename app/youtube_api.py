from googleapiclient.errors import HttpError

def fetch_comment_threads(youtube, video_id, max_results=50):
    threads = []
    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=max_results
        )
        response = request.execute()
        for item in response.get('items', []):
            threads.append(item)
    except HttpError as e:
        print(f"An error occurred: {e}")
    return threads

def delete_comment(youtube, comment_id):
    try:
        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="rejected"
        ).execute()
        return True
    except HttpError as e:
        print(f"Failed to delete comment: {e}")
        return False

def ban_user(youtube, comment_id):
    try:
        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="heldForReview",
            banAuthor=True
        ).execute()
        return True
    except HttpError as e:
        print(f"Failed to ban user: {e}")
        return False
