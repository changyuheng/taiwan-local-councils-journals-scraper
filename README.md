# 中華民國地方議會議事錄總庫檢索結果截取器

截取[中華民國地方議會議事錄總庫](https://journal.th.gov.tw/)檢索結果的[後設資料](https://zh.wikipedia.org/zh-tw/%E5%85%83%E6%95%B0%E6%8D%AE)並輸出到 `<關鍵字>.csv` 檔案。

## 下載

\>\> [Releases](https://github.com/changyuheng/taiwan-local-councils-journals-scraper/releases) <<

## 設定

1. \[選擇性] 設定瀏覽器。支援 `Edge` 與 `Firefox`，預設為 `Edge`。

範例：設定瀏覽器為 Firefox

```
lcjournal-scraper config browser "firefox"
```

## 使用

```
lcjournal-scraper scrape [-c <議會 1> [-c <議會 2> ...]] "<關鍵字>"
```

**範例**：在「彰化縣議會」及「雲林縣議會」的記錄中搜尋「供電」

```
lcjournal-scraper scrape -c 彰化縣議會 -c 雲林縣議會 "供電"
```
