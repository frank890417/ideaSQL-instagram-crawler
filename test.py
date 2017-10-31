# -*- coding: UTF-8 -*-

import sys, os, json, requests
import re
from bs4 import BeautifulSoup
from pprint import pprint  
import json

base_url = "https://www.instagram.com/explore/tags/文青/"
# url = str(base_url + raw_input("請輸入public tag:"))
url = base_url
res = requests.get(url)
soup = BeautifulSoup(res.text, "lxml")
script_tag = soup.find("script", text=re.compile("window\._sharedData"))
shared_data = script_tag.string.partition("=")[-1].strip(" ;")
result = json.loads(shared_data)
tag_page = result["entry_data"]["TagPage"][0]["tag"]
media = tag_page["media"]["nodes"]
pprint(media)

f = open('result.txt', 'w')
f.write(json.dumps(media))
f.close()
