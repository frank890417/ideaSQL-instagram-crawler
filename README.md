# ideaSQL-instagram-crawler
## 用法

在mac上安裝 firefox
安裝python selenium

-q : hashtag   /  -n 數量

## 執行抓取
```
python instagramcrawler.py -q "#端午節" -n 3000
python instagramcrawler.py -q "#台中" -n 3000
```

## 上傳抓取檔案
旁邊會自動建立名稱為：result_#台中小吃_2000.txt 類似的檔名
到上傳系統 http://designav.io/image

![](https://i.imgur.com/Myir1m4.png)
1. 可以用列表移除舊的資料集，建議刪光重建
2. 選擇群組加入，上傳新的資料集，選取文字檔案上傳即可
