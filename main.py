import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP

import src.playground as playground

mcp = FastMCP("Essentials")


class Searcher:
    def __init__(self) -> None:
        self.ddgs = DDGS()

    @mcp.tool()
    async def text_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.text(query, region="ja-jp", max_results=5)
        return results

    @mcp.tool()
    async def image_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.images(query, region="ja-jp", max_results=5)
        return results

    @mcp.tool()
    async def video_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.videos(query, region="ja-jp", max_results=5)
        return results

    @mcp.tool()
    async def news_searcher(self, query: str) -> list[dict[str, str]]:
        results = self.ddgs.news(query, region="ja-jp", max_results=5)
        return results

    @mcp.tool()
    async def url_searcher(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Failed to retrieve page: {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Wikipedia の記事コンテンツは <div id="bodyContent"> に格納される
        content_div = soup.find("div", id="bodyContent")
        if content_div:
            # Extract all paragraph elements from the content
            paragraphs = soup.select("#bodyContent p")
            if paragraphs:
                return "\n".join(
                    [p.get_text() for p in paragraphs][:5]
                )  # 最初の5段落を取得

        return "記事の本文が見つかりませんでした。"


class PyGround:
    async def __init__(self) -> None:
        self.playground = playground.PythonPlayGround()
        await self.playground.setup_virtual_env()

    @mcp.tool()
    async def run_python_code(self, code: str) -> str:
        """Pythonコードを実行"""
        return await self.playground.execute_code(code)

    @mcp.tool()
    async def install_python_library(self, library: str) -> str:
        """Pythonライブラリをインストール"""
        return await self.playground.install_library(library)


if __name__ == "__main__":
    mcp.run()
