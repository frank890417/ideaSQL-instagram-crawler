# -*- coding: UTF-8 -*-
from __future__ import division
import sys
import argparse
import codecs
from collections import defaultdict
import os
import re
import time
import json
from io import BytesIO
from PIL import Image
import base64
try:
    from urlparse import urljoin
    from urllib import urlretrieve
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlretrieve

import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException



reload(sys)
sys.setdefaultencoding('utf8')

# HOST
HOST = 'http://www.instagram.com'

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._8imhp._glz1g"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//a[contains(@class, '_8mlbc _vbtk2 _t5r8b')]"
TIME_TO_CAPTION_PATH = "../../following-sibling::ul/*/*/span"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"


class url_change(object):
    def __init__(self, prev_url):
        self.prev_url = prev_url

    def __call__(self, driver):
        return self.prev_url != driver.current_url


class InstagramCrawler(object):
    def __init__(self):
        self._driver = webdriver.Firefox()

        self.data = defaultdict(list)

    def crawl(self, query, number, caption, dir_prefix,url):
        print("Query: {}, number: {}, caption: {}, dir_prefix: {}".format(
            query, number, caption, dir_prefix))

        # Browse url
        self.browse_target_page(query,url)

        # Scroll down until target Number photos is reached
        self.scroll_to_num_of_posts(number)

        # Start crawling
        self.scrape_photo_links(number, is_hashtag=query.startswith("#"))

        # Scrape Captions if Specified
        if caption:
            self.click_and_scrape_captions(number)

        # Save to directory
        # self.download_and_save(dir_prefix, query, caption)

        # Get JSON datas
        self.get_json_datas(query,number, is_hashtag=query.startswith("#"))

        # Quit driver
        self._driver.quit()

    def browse_target_page(self, query,url):
        # Browse Hashtags
        if query.startswith('#'):
            relative_url = urljoin('explore/tags/', query.strip('#'))
        else:  # Browse user page
            relative_url = query

        target_url = urljoin(HOST, relative_url)
        if (url!=""):
            target_url=url

        self._driver.get(target_url)

    def scroll_to_num_of_posts(self, number):
        # Get total number of posts of page
        num_info = re.search(r'\], "count": \d+',
                             self._driver.page_source).group()
        num_of_posts = int(re.findall(r'\d+', num_info)[0])
        print("posts: {}, number: {}".format(num_of_posts, number))
        number = number if number < num_of_posts else num_of_posts

        # scroll page until reached
        loadmore = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CSS_LOAD_MORE))
        )
        loadmore.click()

        num_to_scroll = int((number - 12) / 12) + 1
        for countid in range(num_to_scroll):
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.2)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.2)
            print countid,'/',num_to_scroll

    def scrape_photo_links(self, number, is_hashtag=False):

        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                                          r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)

        photo_links = [m.group(1) for m in encased_photo_links]

        print("Number of photo_links: {}".format(len(photo_links)))

        begin = 0 if is_hashtag else 1

        self.data['photo_links'] = photo_links[begin:number + begin]

    def get_json_datas(self,query,number, is_hashtag=False):

        encased_alt_links = re.findall(r'\<a.*?href=\"(.*?)\".*?alt=\"([\s\S]*?)\"[\s\S]*?src=\"(.*?)\"', self._driver.page_source)
        href_texts = [m[0] for m in encased_alt_links]
        alt_texts = [m[1] for m in encased_alt_links]
        src_texts = [m[2] for m in encased_alt_links]


        begin = 0 if is_hashtag else 1

        datas=[]
        for idx in range(1,len(alt_texts)):
            try:


                print("---")
                print(str(idx)+"/"+str(len(alt_texts)))
                infourl = "http://api.instagram.com/oembed?url=http://instagram.com"+href_texts[idx]
                print(infourl)
                res = requests.get(infourl)

                # time_results=re.findall('datetime=\\\"(.*?)\\\"',res.text)
                jsondata=json.loads(res.text)
                htmldata=jsondata['html']
                p = re.compile('datetime=\"(.*?)\"')
                time= p.findall(htmldata)[0]
                print(time)

                # p = re.compile('base64\,(.*?)\)')
                # base64data=p.findall(htmldata)[0]
                # print(base64data)

                try:
                    response = requests.get(jsondata['thumbnail_url']);
                    print 'get image: \033[92m success \033[0m'
                    im = Image.open(BytesIO(response.content))
                    t_width,t_height=im.size
                    print(t_width,t_height)

                    rgb_im = im.convert('RGB')
                    r1, g1, b1 = rgb_im.getpixel((int(t_width/2),int( t_height/2)))
                    r2, g2, b2 = rgb_im.getpixel((int(t_width/5),int( t_height/1.5)))
                    r3, g3, b3 = rgb_im.getpixel((int(t_width/5),int( t_height/5)))
                    r4, g4, b4 = rgb_im.getpixel((int(t_width/1.5),int( t_height/1.5)))
                    r5, g5, b5 = rgb_im.getpixel((int(t_width/1.5),int( t_height/5)))

                    r=(r1+r2+r3+r4+r5)/5
                    g=(g1+g2+g3+g4+g5)/5
                    b=(b1+b2+b3+b4+b5)/5
                except Exception as e:
                    print 'get image: \033[91m fail \033[0m'
                    print e


                print r, g, b
                # time_result = [m[0] for m in time_results]
                # print(time_result[0])
                # print('['+str(idx)+']' +href_texts[idx] + "/" + src_texts[idx] + "/" +alt_texts[idx].split('\n')[0])
                datas.append({"href_link": href_texts[idx],"img_link": src_texts[idx], "content": alt_texts[idx] , 'detail_infos': res.text , 'time': time , 'color_r': r,'color_g': g,'color_b': b,'color': "color("+str(r)+","+str(g)+","+str(b)+")",'source': query})
            except Exception as e:
              print e

        print("alt texts number find: {}".format(len(alt_texts)))





        f = open('result_'+str(query)+'_'+str(number)+'.txt', 'w')
        f.write(json.dumps(datas))
        f.close()

        # self.data['photo_links'] = photo_links[begin:number + begin]

    def click_and_scrape_captions(self, number):

        captions = []

        for post_num in range(number):
            if post_num == 0:  # Click on the first post
                # Chrome
                # self._driver.find_element_by_class_name('_ovg3g').click()
                self._driver.find_element_by_xpath(
                    FIREFOX_FIRST_POST_PATH).click()

                if number != 1:  #

                    WebDriverWait(self._driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, CSS_RIGHT_ARROW)
                        )
                    )

            elif number != 1:  # Click Right Arrow to move to next post
                url_before = self._driver.current_url

                self._driver.find_element_by_css_selector(
                    CSS_RIGHT_ARROW).click()

                # Wait until the page has loaded
                try:
                    WebDriverWait(self._driver, 5).until(
                        url_change(url_before))
                except TimeoutException:
                    print("Time out in caption scraping at number {}".format(post_num))
                    break

            # Parse caption
            try:
                time_element = WebDriverWait(self._driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "time"))
                )
                caption = time_element.find_element_by_xpath(
                    TIME_TO_CAPTION_PATH).text
            except NoSuchElementException:  # Forbidden
                caption = ""

            captions.append(caption)

        self.data['captions'] = captions

    def download_and_save(self, dir_prefix, query, caption):
        # Check if is hashtag
        dir_name = query.lstrip(
            '#') + '.hashtag' if query.startswith('#') else query

        dir_path = os.path.join(dir_prefix, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        print()
        # Save Photos
        for idx, photo_link in enumerate(self.data['photo_links'], 0):
            sys.stdout.write("\033[F")
            print("Downloading {} image...".format(idx + 1))
            # Filename
            _, ext = os.path.splitext(photo_link)
            filename = str(idx) + ext
            filepath = os.path.join(dir_path, filename)

            # Send image request
            urlretrieve(photo_link, filepath)

        # Save Captions
        for idx, caption in enumerate(self.data['captions'], 0):

            filename = str(idx) + '.txt'
            filepath = os.path.join(dir_path, filename)

            with codecs.open(filepath, 'w', encoding='utf-8') as fout:
                fout.write(caption + '\n')


def main():
    # Arguments #
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-q', '--query', type=str, default='instagram',
                        help="target to crawl, add '#' for hashtags")
    parser.add_argument('-u', '--url', type=str, default='',
                        help="specific url or place to get")
    parser.add_argument('-n', '--number', type=int, default=12,
                        help='Number of posts to download: integer or "all"')
    parser.add_argument('-c', '--caption', action='store_true',
                        help='Add this flag to download caption when downloading photos')
    parser.add_argument('-d', '--dir_prefix', type=str,
                        default='./data/', help='directory to save results')
    args = parser.parse_args()

    query = args.query
    number = args.number
    dir_prefix = args.dir_prefix
    caption = args.caption
    url = args.url

    crawler = InstagramCrawler()
    crawler.crawl(query=query, number=number,
                  caption=caption, dir_prefix=dir_prefix,url=url)


if __name__ == "__main__":
    main()
