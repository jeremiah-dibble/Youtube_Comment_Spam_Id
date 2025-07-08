from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from .auth import get_flow, get_youtube_service
from .youtube_api import fetch_comment_threads, delete_comment, ban_user
from .moderation import find_spam_comments
from functools import wraps

bp = Blueprint('routes', __name__)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_email' not in session or not session['user_email']:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('routes.home'))
        return view(*args, **kwargs)
    return wrapped_view

@bp.route('/authorize')
def authorize():
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@bp.route('/oauth2callback')
def oauth2callback():
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    # Get user identity from YouTube API
    youtube = get_youtube_service()
    user_info = youtube.channels().list(part="snippet", mine=True).execute()
    email = user_info['items'][0]['snippet'].get('title', 'unknown')
    session['user_email'] = email
    flash('YouTube authorization successful!', 'success')
    return redirect(url_for('routes.home'))

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('routes.home'))

@bp.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    result = None
    actions = []
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        if video_url:
            # Extract video ID (simple logic, can be improved)
            if 'v=' in video_url:
                video_id = video_url.split('v=')[1].split('&')[0]
            else:
                video_id = video_url
            youtube = get_youtube_service()
            threads = fetch_comment_threads(youtube, video_id)
            spam_comments = find_spam_comments(threads)
            for c in spam_comments:
                comment_id = c['id']
                ban_success = ban_user(youtube, comment_id)
                del_success = delete_comment(youtube, comment_id)
                actions.append({
                    'comment': c['snippet']['textDisplay'],
                    'ban': ban_success,
                    'delete': del_success
                })
            result = actions
    return render_template('index.html', result=result, authorized=True)
