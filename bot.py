#!/usr/bin/env python3

import os
import sys
import time
import random
import socket
import subprocess
import tempfile
import tweepy
import praw
import random

# =========================
# 1) CONFIG + CREDENTIALS
# =========================

# Reddit API Credentials
reddit = praw.Reddit(
    client_id='tkFCgP39ajljJbPQcu0Gjw',
    client_secret='MJLQGuTM2l0FhSwCcTWS494MqmYuVw',
    user_agent='Elon Cringe Bot'
)

# Twitter API Credentials
auth = tweepy.OAuth1UserHandler(
    consumer_key='tO6XQjubzTnwZBwVh8KROTiYb',
    consumer_secret='D4A1WjIlQSBldHxq9X05FinThdnlgLVkWgMz3sEaEusFDCNn7X',
    access_token='1937063279312130048-3s4U3TqxZHNLDYtxOTLcB2iGS7TvPP',
    access_token_secret='xLrYFlb6VxABxDrwAsVIZB6UjA7wZh04P5e0o7hkeVxDI'
)

api_v1 = tweepy.API(auth)

client_v2 = tweepy.Client(
    consumer_key='tO6XQjubzTnwZBwVh8KROTiYb',
    consumer_secret='D4A1WjIlQSBldHxq9X05FinThdnlgLVkWgMz3sEaEusFDCNn7X',
    access_token='1937063279312130048-3s4U3TqxZHNLDYtxOTLcB2iGS7TvPP',
    access_token_secret='xLrYFlb6VxABxDrwAsVIZB6UjA7wZh04P5e0o7hkeVxDI'
)

# File to track posted Reddit IDs
POSTED_POSTS_FILE = "posted_posts.txt"

# We only want these subreddits
SUBREDDITS = ["NatureIsFuckingLit"]

# =========================
# 2) HELPER FUNCTIONS
# =========================

def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def load_posted_posts(file_path):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r') as f:
        return set(line.strip() for line in f)

def save_posted_post(file_path, post_id):
    with open(file_path, 'a') as f:
        f.write(post_id + "\n")

# =========================
# 3) REDDIT LOGIC
# =========================

def get_random_video_post():
    posted = load_posted_posts(POSTED_POSTS_FILE)
    random_sub = random.choice(SUBREDDITS)
    print(f"Picked subreddit: r/{random_sub}")

    subreddit = reddit.subreddit(random_sub)
    hot_posts = list(subreddit.hot(limit=200))
    random.shuffle(hot_posts)

    for post in hot_posts:
        if post.id in posted or post.over_18 or post.locked or post.score < 300:
            continue
        if post.is_video:
            full_url = f"https://www.reddit.com{post.permalink}"
            author_name = post.author.name if post.author else "unknown"
            return post.id, post.title, full_url, author_name

    return None, None, None, None

# =========================
# 4) VIDEO DOWNLOADING (FFmpeg)
# =========================

def download_with_ffmpeg(post, output_path):
    """
    Download & mux via Reddit's DASH manifest URL using FFmpeg.
    """
    media = post.media or {}
    rv = media.get('reddit_video') or {}
    dash_url = rv.get('dash_url')
    if not dash_url:
        print("ERROR: No dash_url found; skipping.")
        return False

    cmd = [
        "ffmpeg", "-y",
        "-i", dash_url,
        "-c", "copy",
        output_path
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print("ERROR: FFmpeg failed:\n", proc.stderr.decode('utf-8', errors='ignore'))
        return False
    return True

# =========================
# 5) TWITTER POSTING
# =========================

def post_video_to_twitter(video_path, tweet_text):
    #    hashtags = (
    #        "#fightsvideos #fightvideos #fightingvideos #knockout #ko "
    #        "#shegotbeatup #Fights #fightvids #fightpage #fighting "
    #        "#FightVideo #fightsvideo #hoodfight #hoodfights #boyfight "
    #        "#girlfights #gore #death #schoolfights #hoodfights #fight #fights"
    #    )
    #    formatted_tweet = f"{tweet_text}\n\n{hashtags}"
    #    formatted_tweet = f"{tweet_text}"

    # strip any leading fire emojis
    clean_text = tweet_text.lstrip('🔥').strip()
    formatted_tweet = clean_text

    print("Uploading video chunked to Twitter…")
    media = api_v1.media_upload(filename=video_path, chunked=True, media_category='tweet_video')
    print(f"Posting tweet: {formatted_tweet}")
    client_v2.create_tweet(text=formatted_tweet, media_ids=[media.media_id])
    print("Tweet posted successfully!")

# =========================
# 6) MAIN LOGIC
# =========================

def main():
    post_id, title, full_post_url, author_name = get_random_video_post()
    if not post_id:
        print("No suitable video found; exiting.")
        return

    print(f"Found post: {title}\nURL: {full_post_url}\nID: {post_id}, Author: {author_name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, "reddit.mp4")
        if not download_with_ffmpeg(
                reddit.submission(id=post_id), raw_path):
            save_posted_post(POSTED_POSTS_FILE, post_id)
            return

        post_video_to_twitter(raw_path, title)

    save_posted_post(POSTED_POSTS_FILE, post_id)
    print(f"Done! Post ID {post_id} marked as posted.")

# =========================
# 7) RUN CONTINUOUSLY
# =========================

if __name__ == "__main__":
    main()
