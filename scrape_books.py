import logging
import random
import time
from datetime import date
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "Mozilla/5.0 (compatible; BookScraper/1.0)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    rp.set_url(urljoin(base_url, "/robots.txt"))
    try:
        rp.read()
        logger.info("robots.txt を読み込みました")
    except Exception as e:
        logger.warning(f"robots.txt の読み込みに失敗しました（アクセス制限なしとして続行）: {e}")
    return rp


def can_fetch(rp: RobotFileParser, url: str) -> bool:
    return rp.can_fetch(USER_AGENT, url)


def get_page(session: requests.Session, url: str) -> BeautifulSoup:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"接続エラー: {e}")
        raise SystemExit(1)
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPエラー: {e}")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"リクエストエラー: {e}")
        raise SystemExit(1)


def parse_books(soup: BeautifulSoup) -> list[dict]:
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"]
        price = article.select_one("p.price_color").text.strip()
        availability = article.select_one("p.availability").text.strip()
        books.append({"title": title, "price": price, "availability": availability})
    return books


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    next_btn = soup.select_one("li.next > a")
    if not next_btn:
        return None
    # current_url がカタログルートの場合とページ内の相対パスを両方考慮
    return urljoin(current_url, next_btn["href"])


def save_markdown(books: list[dict], filename: str) -> None:
    lines = [
        "# Books To Scrape — 書籍一覧",
        "",
        f"取得日: {date.today()}  |  合計: {len(books)} 冊",
        "",
        "| タイトル | 価格 | 在庫状況 |",
        "|----------|------|----------|",
    ]
    for book in books:
        title = book["title"].replace("|", "｜")
        lines.append(f"| {title} | {book['price']} | {book['availability']} |")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"結果を {filename} に保存しました")


def main() -> None:
    rp = load_robots(BASE_URL)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    all_books: list[dict] = []
    url = BASE_URL
    page = 1

    while url:
        if not can_fetch(rp, url):
            logger.warning(f"robots.txt により {url} へのアクセスは禁止されています。スキップします。")
            break

        logger.info(f"ページ {page} を取得中: {url}")
        soup = get_page(session, url)
        books = parse_books(soup)
        all_books.extend(books)
        logger.info(f"  → {len(books)} 冊取得")

        url = get_next_page_url(soup, url)
        page += 1

        if url:
            wait = random.uniform(1, 3)
            logger.info(f"  次のリクエストまで {wait:.1f} 秒待機")
            time.sleep(wait)

    filename = f"books_{date.today().strftime('%Y%m%d')}.md"
    save_markdown(all_books, filename)
    logger.info(f"完了: 合計 {len(all_books)} 冊")


if __name__ == "__main__":
    main()
