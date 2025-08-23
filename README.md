# News to RSS

Turn any website’s news page into a usable RSS feed, automatically updated and hosted on GitHub Pages.

This project was built because some university and organization websites do not provide an official RSS feed. Using a simple parser and GitHub Actions, we can scrape their news page and convert it into standard RSS format that works with any feed reader (e.g. Discord [Readybot.io](https://readybot.io/))

> ⚠️ The current configuration uses **[fit.hcmus.edu.vn](https://fit.hcmus.edu.vn/)** as a demo website.  
> You can adapt the parser (`generate_feed.py`) to work with any other site.

---

## 🚀 Features
- Automatically fetches news articles from a website.
- Converts them into **RSS feed** format (`feed.xml`).
- Publishes the feed via **GitHub Pages** at: `https://your-username.github.io/your-repo/feed.xml`
- Updates automatically every hour using GitHub Actions.

---

## 📖 How It Works
1. `generate_feed.py` scrapes the news site with **BeautifulSoup**.
2. It generates `feed.xml` using **feedgen**.
3. A GitHub Action runs hourly:
 - Executes the script.
 - Commits any updated feed to the repo.
 - Publishes via GitHub Pages.

---

## 🛠️ Setup for Your Own Feed
If you want to adapt this project for another site:

### 1. Fork or clone this repository:
 ```bash
 git clone https://github.com/nqthangcs/news-to-rss.git
 cd news-to-rss
```

### 2. **Modify `generate_feed.py`**:

This project is designed to be flexible — you can add new scrapers for different websites without changing the core logic.

Please modify `generate_feed.py` file by the following instruction.

#### 2.1. Create a new scraper class:

Inherit from `BaseScraper` and implement the `_parse_content()` method.
This method should take a `requests.Response` and return a list of news items, where each item is a dictionary with keys:

```py
{
    "title": str,         # article title
    "link": str,          # absolute URL
    "date": datetime,     # publication date
}
```

#### 2.2. Validate & build feed:

Every scraper automatically checks that items have the correct format.

Then you can call `scraper.build_feed(news)` to generate an RSS feed for just that site.

#### 2.3. Merge multiple sites:

If you want a single feed that combines multiple sources, use the `MultiScraper` class:

```py
scrapers = [
    MySiteScraper("https://example.com/news", "Example News", "Unofficial feed for Example.com")
]
multi = MultiScraper(scrapers, "All News", "Merged feed from multiple sites")
all_news = multi.collect_news()
multi.build_feed(all_news, "feed.xml")
```

This will merge, sort by date (newest first), and output one unified feed.xml.


### 3. Test locally:

```bash
pip3 install requests beautifulsoup4 feedgen
python3 generate_feed.py
```

This should create `feed.xml`.

### 4. Modify update frequency:

By default, the feed is updated every hour using GitHub Actions.

If you want to adjust this, edit the workflow file at `.github/workflows/generate-feed.yml` and change the [cron expression](https://crontab.guru/):

```yml
  schedule:
    - cron: "0 * * * *"   # currently runs once per hour
```

For example:

- `0 0 * * *` → once a day at midnight (UTC)
- `*/30 * * * *` → every 30 minutes
- `0 9 * * 1` → every Monday at 09:00 (UTC)

You can customize it to fit your needs.

### 5. Push changes to your GitHub repo:

### 6. Enable GitHub Pages in repo settings:

- Source: main branch, root folder.

### 7. Your feed will be live at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO/feed.xml
```

📌 Example Feed

For demo purposes, the current setup generates a feed for the Faculty of Information Technology – HCMUS news site.

```
https://nqthangcs.github.io/news-to-rss/feed.xml
```

You can subscribe to this URL in any RSS reader.

## 📜 License

MIT License – free to use and adapt for any website.
