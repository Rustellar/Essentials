from mcp.server.fastmcp import FastMCP

import src.playground as playground
import src.searcher as searcher

mcp = FastMCP("Essentials")

if __name__ == "__main__":
    # 検索機能
    searcher = searcher.Searcher()
    mcp.tool()(searcher.text_searcher)
    mcp.tool()(searcher.image_searcher)
    mcp.tool()(searcher.video_searcher)
    mcp.tool()(searcher.news_searcher)
    mcp.tool()(searcher.url_searcher)
    mcp.tool()(searcher.arxiv_searcher)

    # Python PlayGround
    pyground = playground.PythonPlayGround()
    pyground.init_uv()

    mcp.tool()(pyground.execute_code)
    mcp.tool()(pyground.install_library)
    mcp.tool()(pyground.activate_venv)

    # Rust PlayGround
    rustground = playground.RustPlayGround()
    mcp.tool()(rustground.create_rust_project)
    mcp.tool()(rustground.build_rust_project)
    mcp.tool()(rustground.edit_rust_code)
    mcp.tool()(rustground.run_rust_code)
    mcp.tool()(rustground.install_rust_library)

    mcp.run()  # `asyncio.run()` を使わず、直接 `mcp.run()` を呼び出す
