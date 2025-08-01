habr_weekly.xml:
	python3 habr_rss.py > habr_weekly.xml

yt_cookies.txt:
	./extract_cookies.sh ~/.mozilla/firefox/*default*/cookies.sqlite | grep youtube.com > yt_cookies.txt

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
	ssh killdozer "wget --load-cookies keromon/yt_cookies.txt https://www.youtube.com/feed/subscriptions -O subscriptions"
	ssh killdozer "python3 keromon/yt_rss.py > /var/www/html/buryi.ru/yt.xml"

update_karak_cookies:
	rm yt_cookies.txt
	make yt_cookies.txt
	scp yt_cookies.txt karak:keromon/
	ssh karak "wget --load-cookies keromon/yt_cookies.txt https://www.youtube.com/feed/subscriptions -O subscriptions"
	ssh karak "python3 keromon/yt_rss.py > /var/www/mirror.buryi.ru/yt.xml"

update_cubic_cookies:
	rm yt_cookies.txt
	make yt_cookies.txt
	scp yt_cookies.txt cubic:keromon/
	ssh cubic "wget --load-cookies keromon/yt_cookies.txt https://www.youtube.com/feed/subscriptions -O subscriptions"
	ssh cubic "python3 keromon/yt_rss.py > /var/www/html/buryi.ru/yt.xml"

copy_cubic_karak_habr:
	scp cubic:/var/www/html/buryi.ru/habr_weekly.xml karak:/var/www/mirror.buryi.ru/
