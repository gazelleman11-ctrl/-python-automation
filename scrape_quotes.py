import logging
import random
import time
from datetime import date
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://quotes.toscrape.com"
TARGET_PATH = "/js"
USER_AGENT = "Mozilla/5.0 (compatible; QuoteScraper/1.0)"

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
        logger.warning(f"robots.txt の読み込みに失敗しました（制限なしとして続行）: {e}")
    return rp


def can_fetch(rp: RobotFileParser, url: str) -> bool:
    return rp.can_fetch(USER_AGENT, url)


def save_markdown(quotes: list[dict], filename: str) -> None:
    lines = [
        "# Quotes To Scrape — 名言一覧",
        "",
        f"取得日: {date.today()}  |  合計: {len(quotes)} 件",
        "",
        "| 名言 | 著者 |",
        "|------|------|",
    ]
    for q in quotes:
        text = q["text"].replace("|", "｜")
        author = q["author"].replace("|", "｜")
        lines.append(f"| {text} | {author} |")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Markdown を {filename} に保存しました")


def scrape(page_url: str, page, screenshot_path: str) -> list[dict]:
    try:
        logger.info(f"ページを開いています: {page_url}")
        page.goto(page_url, wait_until="networkidle", timeout=30000)
        # JS描画完了を待つ
        page.wait_for_selector("div.quote", timeout=15000)
    except PlaywrightTimeoutError as e:
        logger.error(f"ページ読み込みタイムアウト: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"接続エラー: {e}")
        raise SystemExit(1)

    quotes = []
    for el in page.query_selector_all("div.quote"):
        text = el.query_selector("span.text").inner_text().strip()
        author = el.query_selector("small.author").inner_text().strip()
        quotes.append({"text": text, "author": author})

    page.screenshot(path=screenshot_path, full_page=True)
    logger.info(f"スクリーンショットを {screenshot_path} に保存しました")

    return quotes


def get_next_url(page) -> str | None:
    next_btn = page.query_selector("li.next > a")
    if not next_btn:
        return None
    href = next_btn.get_attribute("href")
    return urljoin(BASE_URL, href)


def main() -> None:
    rp = load_robots(BASE_URL)

    today = date.today().strftime("%Y%m%d")
    md_file = f"quotes_{today}.md"
    png_file = f"quotes_{today}.png"

    all_quotes: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        url: str | None = BASE_URL + TARGET_PATH
        first_page = True
        page_num = 1

        while url:
            if not can_fetch(rp, url):
                logger.warning(f"robots.txt により {url} へのアクセスは禁止されています。スキップします。")
                break

            screenshot = png_file if first_page else None
            logger.info(f"ページ {page_num} を取得中: {url}")

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_selector("div.quote", timeout=15000)
            except PlaywrightTimeoutError as e:
                logger.error(f"ページ読み込みタイムアウト: {e}")
                raise SystemExit(1)
            except Exception as e:
                logger.error(f"接続エラー: {e}")
                raise SystemExit(1)

            quotes = []
            for el in page.query_selector_all("div.quote"):
                text = el.query_selector("span.text").inner_text().strip()
                author = el.query_selector("small.author").inner_text().strip()
                quotes.append({"text": text, "author": author})

            all_quotes.extend(quotes)
            logger.info(f"  → {len(quotes)} 件取得")

            if first_page:
                page.screenshot(path=png_file, full_page=True)
                logger.info(f"スクリーンショットを {png_file} に保存しました")
                first_page = False

            next_btn = page.query_selector("li.next > a")
            if next_btn:
                href = next_btn.get_attribute("href")
                url = urljoin(BASE_URL, href)
                page_num += 1
                wait = random.uniform(1, 3)
                logger.info(f"  次のリクエストまで {wait:.1f} 秒待機")
                time.sleep(wait)
            else:
                url = None

        browser.close()

    save_markdown(all_quotes, md_file)
    logger.info(f"完了: 合計 {len(all_quotes)} 件")


if __name__ == "__main__":
    main()
