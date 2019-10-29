from typing import Generator, Dict, List
from bson.objectid import ObjectId

import feedparser
import pymongo

from storage import rss_feeds, rss_posts
from log import get_logger

POST_SENDED = 1
POST_NOT_SENDED = 2

logger = get_logger("rss")


def add_feed(url: str, tid: int) -> bool:
    """
    Add RSS feed to storage.
    
    :param url: RSS feed URL.
    :param tid: Telegram user id.
    :returns: True is save success else False.
    """
    logger.info("add_feed " + url)
    try:
        feed = feedparser.parse(url)['feed']
    except Exception:
        logger.info("cannot load feed")
        return False
    try:
        if feed.get('title'):
            rss_feeds.insert_one({
                'id': get_sha256_hash(url + str(tid)),
                'tid': tid,
                'title': feed.get('title'),
                'url': url,
                'subtitle': feed.get('subtitle'),
                'published': feed.get('published'),
                'encoding': feed.get('encoding')
            })
            return True
        else:
            logger.info("feed not have a title")
            return False
    except pymongo.errors.DuplicateKeyError:
        logger.info("feed duplicate")
        return False


def feed_refresh_posts(url: str) -> None:
    """
    Refresh feed posts list.

    :param url: RSS feed url.
    """
    for post in feedparser.parse(url)['entries']:
        try:
            rss_posts.insert_one({
                'id': get_sha256_hash(post['link']),
                'feed': rss_feeds.find_one({'url': url})['_id'],
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


def refresh_all_feeds() -> None:
    """
    Refresh posts in all stored RSS feeds.
    """
    logger.info("refresh_all")
    for rss in rss_feeds.find():
        feed_refresh_posts(rss['url'])


def get_feeds(tid: int) -> List:
    """
    Return list of feeds for Telegram user.

    :param tid: Telegram user id.
    :returns: List of RSS feeds records.
    """
    return list(rss_feeds.find({"tid": tid}))


def get_feed(_id: str) -> Dict:
    """
    Get feed by Mongo id.
    
    :param _id: MongoDB document ID.
    :returns: MongoDB document dictionary.
    """
    return rss_feeds.find_one({"_id": ObjectId(_id)})


def get_sha256_hash(string: str) -> str:
    """
    Return SHA256 hash of string.

    :param string: String for hashing.
    :returns: Hashing result string.
    """
    import hashlib
    hash_obj = hashlib.sha256()
    hash_obj.update(string.encode())
    return hash_obj.hexdigest()


def get_all_unreaders_posts(tid: int) -> Generator[Dict, None, None]:
    """
    Return all unreaded posts for Telegram user. All returned posts marking as readed.

    :param tid: Telegram user id.
    :yield: Post MongoDB document dictionary.
    """
    for rss in rss_feeds.find({"tid": tid}):
        for post in rss_posts.find({"feed": rss["id"], "sended": POST_NOT_SENDED}):
            rss_posts.update_one(post, {"$set": {"sended": POST_SENDED}})
            yield post


def get_unreaded_posts(feed__id: str) -> Generator[Dict, None, None]:
    """
    Return all unreaded posts for specific RSS feed. All returned posts marking as readed.

    :param feed__id: RSS feed MongoDB _id.
    :yield: Post MongoDB document dictionary.
    """
    logger.info(feed__id)
    for post in rss_posts.find({"feed": ObjectId(feed__id), "sended": POST_NOT_SENDED}):
        rss_posts.update_one(post, {"$set": {"sended": POST_SENDED}})
        yield post
