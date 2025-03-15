import os
import subprocess
import sys
import time
from pathlib import Path


class PythonPlayGround:
    def __init__(self) -> None:
        # Essentialsが使用するPythonディレクトリ
        self.essential_dir = Path(
            os.getenv("ESSENTIALS_MCP_PY_DIR", Path.home() / "essentials_mcp_py_dir")
        )

        # Essentialsの仮想環境のパス
        self.venv_dir = Path().joinpath(self.essential_dir, ".venv")
        # EssentialsのPythonパス
        self.essential_py = Path().joinpath(
            self.venv_dir,
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python",
        )
        # 仮想環境が有効かどうか?
        self.is_venv_activate = False

    def init_uv(self):
        """uv の初期化（`pyproject.toml` が存在しない場合のみ実行）"""
        if not self.essential_dir.exists():
            self.essential_dir.mkdir(parents=True, exist_ok=True)

        os.chdir(self.essential_dir)

        # `pyproject.toml` が存在しない場合のみ `uv init` を実行
        if not (self.essential_dir / "pyproject.toml").exists():
            try:
                subprocess.run(["uv", "init"], check=True)
                subprocess.run(["uv", "sync"], check=True)  # 仮想環境を自動作成
            except subprocess.CalledProcessError as e:
                print(f"Error during uv init: {e}", file=sys.stderr)
        else:
            print("Project is already initialized. Skipping `uv init`.")

    # 仮想環境の有効化
    async def activate_venv(self):
        # 仮想環境が有効化されているかどうか
        if self.is_venv_activate:
            return
        # 仮想環境の有効化
        os.environ["VIRTUAL_ENV"] = str(self.venv_dir)
        os.environ["PATH"] = (
            f"{self.venv_dir / 'bin'}:{os.environ['PATH']}"
            if sys.platform != "win32"
            else f"{self.venv_dir / 'Scripts'};{os.environ['PATH']}"
        )
        self.is_venv_activate = True
        os.chdir(self.essential_dir)
        print(f"仮想環境をアクティブ化しました: {self.venv_dir}")

    # ライブラリのインストール
    async def install_library(self, library: str):
        # 仮想環境の有効化
        await self.activate_venv()
        try:
            if library.startswith("torch"):
                # `pyproject.toml` に Pytorch の記述を追記
                pyproject_path = self.venv_dir / "pyproject.toml"
                with open(pyproject_path, "a", encoding="utf-8") as f:
                    f.write("""
                            dependencies = [
                            "torch>=2.6.0",
                            "torchvision>=0.21.0",
                            "markupsafe>=2.1.1,<3.0.0"
                            ]

                            [[tool.uv.index]]
                            name = "pytorch-cu126"
                            url = "https://download.pytorch.org/whl/cu126"
                            explicit = true

                            [tool.uv.sources]
                            torch = [
                              { index = "pytorch-cu126", marker = "sys_platform == 'linux' or sys_platform == 'win32'" },
                            ]
                            torchvision = [
                              { index = "pytorch-cu126", marker = "sys_platform == 'linux' or sys_platform == 'win32'" },
                            ]
                            """)
                time.sleep(1)
                # `uv sync` を実行
                subprocess.run(["uv", "sync"], check=True)
                return "Successfully installed PyTorch via uv sync"

            # 通常のライブラリインストール
            subprocess.run(["uv", "add", library], check=True)
            return f"Successfully installed {library}"
        except subprocess.CalledProcessError as e:
            return f"Error: Failed to install {library}: {str(e)}"

    async def execute_code(
        self, code: str, directory: str, file_name_without_extension: str
    ) -> str:
        """安全なPythonコード実行"""
        # 仮想環境の有効化
        await self.activate_venv()
        try:
            parent_dir = Path(self.essential_dir, directory)
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)
            script_path = Path(parent_dir).joinpath(file_name_without_extension + ".py")
            script_path.write_text(code, encoding="utf-8")

            result = subprocess.run(
                ["uv", "run", script_path],
                capture_output=True,
                text=True,
            )

            return (
                result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
            )

        except subprocess.TimeoutExpired:
            return "Error: Execution timed out"
        except Exception as e:
            return f"Error: {str(e)}"
