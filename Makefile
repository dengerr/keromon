habr_weekly.xml:
	python3 habr_rss.py > habr_weekly.xml

yt_cookies.txt:
	./extract_cookies.sh | grep youtube.com > yt_cookies.txt

subscriptions: yt_cookies.txt
	wget --load-cookies yt_cookies.txt https://www.youtube.com/feed/subscriptions -O subscriptions

yt: subscriptions
	@python3 yt_rss.py > yt.xml

debug:
	python3 yt_rss.py

update_killdozer_cookies:
	rm yt_cookies.txt
	make yt_cookies.txt
	scp yt_cookies.txt killdozer:keromon/
