import json

import feedparser
import pdfplumber
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


class Searcher:
    def __init__(self) -> None:
        self.ddgs = DDGS()
        self.arxiv_api_url = (
            "http://export.arxiv.org/api/query?search_query={query}&max_results=5"
        )

    async def text_searcher(self, query: str) -> str:
        """DuckDuckGo で検索し、Shift-JIS 環境でも可読できる形式で結果を返す"""
        results = list(self.ddgs.text(query, region="ja-jp", max_results=5))

        # JSON 文字列を UTF-8 でエンコードし、Windows では Shift-JIS に変換
        json_str = json.dumps(results, ensure_ascii=False, indent=2)

        return json_str  # Linux/Mac は UTF-8 のまま返す

    async def image_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.images(query, region="ja-jp", max_results=5)
        return results

    async def video_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.videos(query, region="ja-jp", max_results=5)
        return results

    async def news_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.news(query, region="ja-jp", max_results=5)
        return results

    async def url_searcher(self, url: str) -> str:
        """指定された URL のコンテンツを取得し、全文を返す"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return f"Failed to retrieve page: {response.status_code}"

            soup = BeautifulSoup(response.text, "html.parser")

            # 記事の本文を取得
            article_text = []
            for tag in ["h1", "h2", "h3", "p", "li", "article"]:
                for element in soup.find_all(tag):
                    text = element.get_text(strip=True)
                    if text:
                        article_text.append(text)

            if not article_text:
                return "記事の本文が見つかりませんでした。"

            return "\n".join(article_text[:50])  # 最初の 50 要素を取得

        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    # Thank you to arXiv for use of its open access interoperability!
    async def arxiv_searcher(self, query: str) -> str:
        """
        arXiv API を使用して論文を検索し、タイトル、要約、本文を取得
        取得できない場合は PDF からテキストを抽出
        LaTexで数式をレンダリングしてください
        """
        response = requests.get(self.arxiv_api_url.format(query=query))
        if response.status_code != 200:
            return f"Failed to retrieve page: {response.status_code}"

        feed = feedparser.parse(response.text)
        papers = []

        for entry in feed.entries:
            paper_id = str(entry.id).split("/")[-1]  # entry.id を文字列に変換
            title = entry.title
            summary = entry.summary
            html_url = f"https://arxiv.org/html/{paper_id}"
            pdf_url = f"https://arxiv.org/pdf/{paper_id}"

            # HTML から情報を取得
            paper_content = self._fetch_html_content(html_url)
            if paper_content:
                papers.append({
                    "title": title,
                    "url": html_url,
                    "summary": summary,
                    "content": paper_content,
                })
            else:
                # HTML がない場合は PDF から取得
                pdf_text = self._fetch_pdf_content(pdf_url)
                papers.append({
                    "title": title,
                    "url": pdf_url,
                    "summary": summary,
                    "content": pdf_text if pdf_text else "PDF 解析に失敗しました。",
                })

        return json.dumps(papers, ensure_ascii=False, indent=2)

    def _fetch_html_content(self, url: str) -> str:
        """HTML ページから本文を取得"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return f"Failed to retrieve page: {response.status_code}"

            soup = BeautifulSoup(response.text, "html.parser")
            content = []
            for tag in ["h1", "h2", "h3", "p", "li", "article"]:
                for element in soup.find_all(tag):
                    text = element.get_text(strip=True)
                    if text:
                        content.append(text)

            return "\n".join(content[:50]) if content else ""  # 最初の 50 要素を取得
        except requests.exceptions.RequestException:
            return ""

    def _fetch_pdf_content(self, pdf_url: str) -> str:
        """PDF をダウンロードし、テキストを抽出"""
        try:
            response = requests.get(pdf_url, stream=True)
            if response.status_code != 200:
                return ""

            with open("temp.pdf", "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=1024):
                    pdf_file.write(chunk)

            extracted_text = []
            with pdfplumber.open("temp.pdf") as pdf:
                for page in pdf.pages:
                    extracted_text.append(page.extract_text())

            return "\n".join(extracted_text) if extracted_text else ""
        except Exception:
            return f"Failed to retrieve page: {response.status_code}"
