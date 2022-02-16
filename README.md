## scrap

show in terminal:

    python3 keromon/scrap.py print daily

send to email. Copy email.ini and add to crontab:

	0 3 * * * python3 keromon/scrap.py daily
	9 3 * * 1 python3 keromon/scrap.py weekly

## readability markdown

print markdown:

    python3 readability_md.py https://habr.com/ru/post/499364/

save html and md:

    python3 readability_md.py --save https://habr.com/ru/post/499364/

links:
- [python package html to markdown](https://github.com/matthewwithanm/python-markdownify)
- [Настройка вида для чтения в Firefox (css)](https://ziscod.com/nastroyka-vida-dlya-chteniya-v-firefox/)
- [Как реализован режим чтения в браузерах?](https://qna.habr.com/q/394546)
- https://github.com/mozilla/readability
- https://stackoverflow.com/questions/30661650/how-does-firefox-reader-view-operate
- https://stackoverflow.com/questions/30730300/optimize-website-to-show-reader-view-in-firefox/

