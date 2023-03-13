import json
import sys

import rss

url = "https://www.youtube.com/feed/subscriptions"


def main():
    channel = dict(
        title="YT subscriptions RSS",
        link=url,
        # description="",
        language="ru",
    )
    rss.print_rss2(channel, load_items())


def debug():
    with open('subscriptions', 'r') as f:
        output = get_from_json(f.read())
    for item in get_items(output):
        debug_item(item)


def load_items():
    with open('subscriptions', 'r') as f:
        output = get_from_json(f.read())
    for item in get_items(output):
        yield load_item(item)


def get_items(output):
    tab = output['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]
    contents = tab['tabRenderer']['content']['sectionListRenderer']['contents']
    for content in contents:
        content = list(content.values())[0]
        if 'contents' in content:
            for cont in content['contents']:
                shelf_content = cont['shelfRenderer']['content']
                try:
                    if 'gridRenderer' in shelf_content:
                        items = shelf_content['gridRenderer']['items']
                    else:
                        items = shelf_content['expandedShelfContentsRenderer']['items']
                except Exception as e:
                    sys.stderr.write(f"Exception: {e}\n")
                    sys.stderr.write(str(shelf_content))
                else:
                    for _item in items:
                        item = _item.get('gridVideoRenderer') or _item.get('videoRenderer')
                        item['duration'] = get_duration(item)
                        if item['duration']:
                            yield item


def get_duration(item):
    for overlay in item['thumbnailOverlays']:
        if 'thumbnailOverlayTimeStatusRenderer' in overlay:
            duration = overlay['thumbnailOverlayTimeStatusRenderer']['text']
            if 'simpleText' in duration and ':' in duration['simpleText']:
                return duration['simpleText']


def load_item(item):
    """
    Изымаем из айтема title, link, thumbnail, duration
    """
    title = item['title']['runs'][0]['text']
    channel = item['shortBylineText']['runs'][0]['text']
    thumbnail = item['thumbnail']['thumbnails'][-1]['url']
    url = "https://www.youtube.com/watch?v=" + item['videoId']
    duration = item["duration"]
    description = f'<img src="{thumbnail}"/><br/>{duration}'
    result = {
        'title': f"{channel}: {title}",
        # 'channel': channel,
        # 'thumb': thumbnail,
        'link': url,
        'description': description,
        # 'pubDate': current,
        'guid': item['videoId'],
    }
    return result


def get_from_json(output):
    output = output.split("var ytInitialData =", 1)[1]
    output = output.split(";</script>", 1)[0]
    return json.loads(output)


def debug_item(item):
    pp(item)
    print()


def pp(val, maxi=150):
    if isinstance(val, dict):
        if len(val) == 1:
            for k,v in val.items():
                print(k,)
                return pp(v, maxi)
        for k,v in val.items():
            print(k, ':', str(v)[:maxi])
    elif isinstance(val, list):
        print('list...')
        for i, item in enumerate(val):
            print('    ', i, '',  end='')
            pp(item)
    else:
        print(val)


if __name__ == "__main__":
    if 'debug' in sys.argv:
        debug()
    else:
        main()
