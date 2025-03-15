import json

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP

import src.playground as playground

mcp = FastMCP("Essentials")


class Searcher:
    def __init__(self) -> None:
        self.ddgs = DDGS()

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


class PyGround:
    def __init__(self) -> None:
        self.playground = playground.PythonPlayGround()

    async def setup_virtual_env(self):
        await self.playground.activate_venv()

    async def run_python_code(
        self, code: str, directory: str, file_name_without_extension: str
    ) -> str:
        """Python コードを指定されたディレクトリ内に保存し、実行する。

        Args:
            code (str): 実行する Python コード
            directory (str): スクリプトを保存するディレクトリ（会話履歴の保存場所）
            file_name_without_extension (str): スクリプトのファイル名（拡張子なし）

        Returns:
            str: 実行結果
        """
        """Pythonコードを実行"""
        return await self.playground.execute_code(
            code, directory, file_name_without_extension
        )

    async def install_python_library(self, library: str) -> str:
        """Pythonライブラリをインストール"""
        return await self.playground.install_library(library)


if __name__ == "__main__":
    searcher = Searcher()
    # 手動登録
    mcp.tool()(searcher.text_searcher)
    mcp.tool()(searcher.image_searcher)
    mcp.tool()(searcher.video_searcher)
    mcp.tool()(searcher.news_searcher)
    mcp.tool()(searcher.url_searcher)

    pyground = PyGround()

    venv_create = playground.PythonPlayGround()
    venv_create.init_uv()

    mcp.tool()(pyground.run_python_code)
    mcp.tool()(pyground.install_python_library)
    mcp.tool()(pyground.setup_virtual_env)

    mcp.run()  # `asyncio.run()` を使わず、直接 `mcp.run()` を呼び出す
