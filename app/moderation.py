from app.identify_spam import IdentifySpam
from app.ban_db import add_banned_author, is_author_banned
from flask import session

identify_spam = IdentifySpam()

def is_spam(thread):
    # thread: dict with 'snippet', 'replies' (if any)
    # Build a thread_dict for the LLM
    top_comment = thread['snippet']['topLevelComment']
    thread_dict = {
        'author_id': top_comment['snippet']['authorChannelId']['value'],
        'text': top_comment['snippet']['textDisplay'],
        'replies': []
    }
    replies = thread.get('replies', {}).get('comments', [])
    for reply in replies:
        thread_dict['replies'].append({
            'author_id': reply['snippet']['authorChannelId']['value'],
            'text': reply['snippet']['textDisplay']
        })
    # Call LLM to get list of spam author_ids with reasons/evidence
    spam_authors = identify_spam.analyze_thread(thread_dict)
    # Store in DB who banned them (current user)
    banned_by = session.get('user_email', 'unknown')
    for spam in spam_authors:
        if not is_author_banned(spam.author_id):
            add_banned_author(spam.author_id, spam.reason, getattr(spam, 'evidence', ''), banned_by)
    return [spam.author_id for spam in spam_authors]

def find_spam_comments(threads):
    spam_comments = []
    for thread in threads:
        spam_author_ids = is_spam(thread)
        # Check top-level
        top_comment = thread['snippet']['topLevelComment']
        if top_comment['snippet']['authorChannelId']['value'] in spam_author_ids:
            spam_comments.append(top_comment)
        # Check replies
        replies = thread.get('replies', {}).get('comments', [])
        for reply in replies:
            if reply['snippet']['authorChannelId']['value'] in spam_author_ids:
                spam_comments.append(reply)
    return spam_comments
