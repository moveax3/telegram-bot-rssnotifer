import pymongo
import os

MONGO_LOGIN = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_CONN_STR = "mongodb://" + MONGO_LOGIN + ":" + MONGO_PASSWORD + "@mongo"
client = pymongo.MongoClient(MONGO_CONN_STR)
db = client.rss
rss_feeds = db.rss_feeds
rss_posts = db.rss_posts
db.rss_feeds.create_index([('id', pymongo.ASCENDING)], unique=True)
db.rss_posts.create_index([('id', pymongo.ASCENDING)], unique=True)
