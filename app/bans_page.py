from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.ban_db import DB_PATH
import sqlite3
from functools import wraps

bp_bans = Blueprint('bans', __name__)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_email' not in session or not session['user_email']:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('routes.home'))
        return view(*args, **kwargs)
    return wrapped_view

@bp_bans.route('/bans')
@login_required
def bans():
    user_email = session.get('user_email', 'unknown')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT author_id, reason, evidence, banned_at
        FROM banned_authors
        WHERE banned_by = ?
        ORDER BY banned_at DESC
    """, (user_email,))
    bans = c.fetchall()
    conn.close()
    return render_template('bans.html', bans=bans)
