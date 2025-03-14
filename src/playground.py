import os
import subprocess
import sys
from pathlib import Path


class PythonPlayGround:
    def __init__(self) -> None:
        # 仮想環境のディレクトリを指定（PathLibを使用）
        self.venv_dir = Path(
            os.getenv("PYTHON_PLAYGROUND_VENV", Path.home() / ".python_playground_env")
        )
        self.python_exec = self.venv_dir / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )

    async def setup_virtual_env(self):
        """uvを使用して仮想環境をセットアップ"""
        if not self.venv_dir.exists():
            print("仮想環境をセットアップ中...")
            subprocess.run(["uv", "venv", str(self.venv_dir)], check=True)

    async def execute_code(self, code: str) -> str:
        """安全なPythonコード実行"""
        try:
            temp_dir = Path(self.venv_dir / "tmp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            script_path = temp_dir / "script.py"
            script_path.write_text(code, encoding="utf-8")

            result = subprocess.run(
                [str(self.python_exec), str(script_path)],
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

    async def install_library(self, library: str) -> str:
        try:
            subprocess.run(["uv", "add", library], check=True)
            return f"Successfully installed {library}"
        except subprocess.CalledProcessError as e:
            return f"Error: Failed to install {library}: {str(e)}"
