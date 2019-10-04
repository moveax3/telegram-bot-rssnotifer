from typing import Generator, Dict

import feedparser
import pymongo

from storage import rss_feeds, rss_posts
from log import get_logger

POST_SENDED = 1
POST_NOT_SENDED = 2

logger = get_logger("rss")


def prompt_feed():
    return "Please write RSS url bellow:"


def add_feed(url: str, tid: str):
    try:
        feed = feedparser.parse(url)['feed']
    except Exception:
        return "Wrong RSS url."
    try:
        if feed.get('title'):
            rss_feeds.insert_one({
                'id': get_sha256_hash(url),
                'tid': tid,
                'title': feed.get('title'),
                'url': url,
                'subtitle': feed.get('subtitle'),
                'published': feed.get('published'),
                'encoding': feed.get('encoding')
            })
            return "RSS \n'" + feed.get('title') + "'\n successfull added to your list."
        else:
            return "RSS link incorrect. Plase try other link."
    except pymongo.errors.DuplicateKeyError:
        return "RSS \n'" + feed.get('title') + "'\n already added to your list."


def feed_origin_posts(url):
    for post in feedparser.parse(url)['entries']:
        try:
            rss_posts.insert_one({
                'id': get_sha256_hash(post['link']),
                'feed': get_sha256_hash(url),
                'title': post['title'],
                'd_title': post['title_detail']['value'],
                'link': post['link'],
                'summ': post['summary'],
                'd_summ': post['summary_detail']['value'],
                'published': post['published'],
                'sended': POST_NOT_SENDED,
            })
            print('Added "' + post['title'] + '"')
        except pymongo.errors.DuplicateKeyError:
            pass


def refresh_all():
    logger.info("refresh_all")
    for rss in rss_feeds.find():
        feed_origin_posts(rss['url'])


def get_feeds(tid):
    response = ""
    for feed in rss_feeds.find({"tid": tid}):
        response += feed["title"] + "(" + feed["url"] + ")"
    return response


def get_sha256_hash(string: str) -> str:
    import hashlib
    hash_obj = hashlib.sha256()
    hash_obj.update(string.encode())
    return hash_obj.hexdigest()


def get_unreaders_posts() -> Generator[Dict, None, None]:
    logger.info("get_unreaders_posts")
    for rss in rss_feeds.find():

        for post in rss_posts.find({"feed": rss["id"], "sended": POST_NOT_SENDED}):
            post_content = "\n#" + rss["title"] + " >> "
            post_content += \
                '<a href="' + post['link'] + '">' + post['title'] + "</a>\n"
            rss_posts.update_one(post, {"$set": {"sended": POST_SENDED}})
            yield {"tid": rss["tid"], "post": post_content}
