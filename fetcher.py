"""
tl;dr Fetches the recent posts from lobste.rs into the db.

I am an SQL newb and hate Python.  As I'm writing this I still don't know why
I'm even using Python for this.  Brace yourself.
"""

from urllib import request
from time import sleep
import datetime
import json
import sqlite3

def fetch(page):
	# https://github.com/lobsters/lobsters/blob/master/config/initializers/rack_attack.rb
	# I could skip the first sleep, but eh, this prevents going past the ratelimit with manual use.
	sleep(1)
	res = request.urlopen(f"https://lobste.rs/newest/page/{page}.json")
	if res.code != 200:
		raise Exception(f"got code {res.code}")
	return json.load(res)

def insert_story(story, cur, now):
	params = {
		# TODO this is naive, probably sensitive to timezone shenanigans
		"story_ts": int(datetime.datetime.fromisoformat(story['created_at']).timestamp()),
		"fetch_ts": int(now.timestamp()),

		"id": story['short_id'],
		"title": story['title'],
		"url": story['url'],
		"tags": ' '.join(sorted(story['tags'])),
		"score": story['score'],
	}

	# https://stackoverflow.com/a/15277374
	cur.execute("BEGIN")
	cur.execute("""
		UPDATE posts
		SET title=:title, url=:url, tags=:tags
		WHERE short_id=:id
	""", params)
	cur.execute("""
		INSERT OR IGNORE
		INTO posts (short_id, created_ts, title, url, tags)
		VALUES (:id, :story_ts, :title, :url, :tags)
	""", params)
	cur.execute("""
		INSERT INTO scores (short_id, fetch_ts, score)
		VALUES (:id, :fetch_ts, :score)
	""", params)
	cur.execute("COMMIT")

if __name__ == "__main__":
	con = sqlite3.connect("lobdgst.db")
	cur = con.cursor()
	with open('schema.sql') as f:
		cur.executescript(f.read())

	now = datetime.datetime.now()
	"""
	At its peak, lobste.rs had 1200 posts/month == avg 40 posts/day
	Each page has 25 posts (at the time of writing), 25*3 = 75 posts are fetched

	That should provide enough of a buffer even for days which almost double the
	average peak posting volume. "Average peak" is a stupid term, and this WILL
	probably end up missing posts. Whatever.

	There are three solutions to this:
	1. crawl until i encounter a post which matches some random criteria.
	   errorprone
	2. up the page limit. probably won't use up that much traffic in the
	   grand scheme of things
	3. ask pushcx for SELECT created_ts FROM posts; and tune based on that
	"""
	# lobste.rs had 1200 posts/month at the peak
	# 1200/30 = 40 posts/day
	# each page has 25 posts, 25*3=75 posts
	# which should hopefully be enough
	for page in [1, 2, 3]:
		print(f"fetching page {page}")
		for story in fetch(page):
			insert_story(story, cur, now)
