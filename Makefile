habr_weekly.xml:
	python habr_rss.py > habr_weekly.xml

yt_cookies.txt:
	./extract_cookies.sh | grep youtube.com > yt_cookies.txt

subscriptions: yt_cookies.txt
	wget --load-cookies yt_cookies.txt https://www.youtube.com/feed/subscriptions

yt: subscriptions
	@python yt_rss.py > yt.xml
