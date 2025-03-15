import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


class PythonPlayGround:
    """
    # Python PlayGround
    アーティファクトで作成したコードを実際に実行し、コードの動作を確認します。
    """

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

    # uvの初期化
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

    # コードの実行
    async def execute_code(
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
                timeout=5 * 60,  # タイムアウト設定（5分）
            )

            return (
                result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
            )

        except subprocess.TimeoutExpired:
            return "Error: Execution timed out"
        except Exception as e:
            return f"Error: {str(e)}"


class RustPlayGround:
    """
    # Rust PlayGround
    アーティファクトで作成したコードを実際に実行し、コードの動作を確認します。
    """

    def __init__(self) -> None:
        self.rust_base_dir = Path.home() / "essentials_mcp_rs_dir"

        if not self.rust_base_dir.exists():
            self.rust_base_dir.mkdir(parents=True, exist_ok=True)

        self.cargo_path = shutil.which("cargo")
        self.rustc_path = shutil.which("rustc")

    async def create_rust_project(self, project_name: str, project_type: str) -> str:
        """
        Rust の新しいプロジェクトを作成する (`cargo new` を使用)

        Args:
            project_name (str): 作成するプロジェクトの名前
            project_type (str): "bin"（バイナリ）または "lib"（ライブラリ）

        Returns:
            str: プロジェクト作成の成否メッセージ
        """
        project_dir = self.rust_base_dir / project_name

        # 既に同じ名前のプロジェクトが存在する場合はエラーを返す
        if project_dir.exists():
            return f"Error: '{project_name}' は既に存在します。別の名前を指定してください。"

        # `cargo new` の実行
        cargo_command = [self.cargo_path, "new", project_name, f"--{project_type}"]
        try:
            subprocess.run(
                cargo_command,
                cwd=self.rust_base_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return (
                f"Rust プロジェクト '{project_name}' ({project_type}) を作成しました。"
            )
        except subprocess.CalledProcessError as e:
            return f"Error: Rust プロジェクトの作成に失敗しました。\n{e.stderr}"

    async def build_rust_project(self, project_name: str) -> str:
        """
        Rust プロジェクトをビルドする (`cargo build` を使用)

        Args:
            project_name (str): ビルドするプロジェクトの名前

        Returns:
            str: ビルド結果（成功 or 失敗）
        """
        project_dir = self.rust_base_dir / project_name

        # プロジェクトが存在しない場合はエラー
        if not project_dir.exists():
            return f"Error: プロジェクト '{project_name}' が見つかりません。まず `create_rust_project` で作成してください。"

        # cargo_pathがNoneの場合はエラー
        if self.cargo_path is None:
            return "Error: cargoコマンドが見つかりません。Rustがインストールされているか確認してください。"

        # `cargo build` の実行
        try:
            result = subprocess.run(
                [self.cargo_path, "build"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=5 * 60,  # タイムアウト設定（5分）
            )

            return (
                f"Build Success: {result.stdout}"
                if result.returncode == 0
                else f"Build Failed: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            return "Error: Build process timed out."
        except Exception as e:
            return f"Error: {str(e)}"

    async def edit_rust_code(
        self, project_name: str, file_name: str, new_code: str, mode: str = "append"
    ) -> str:
        """
        Rust の `.rs` ファイルのみを編集できるようにする

        Args:
            project_name (str): 編集するプロジェクトの名前
            file_name (str): 編集する `.rs` ファイル名（拡張子付き）
            new_code (str): 追加または上書きするコード
            mode (str): "append"（追加）または "overwrite"（上書き）

        Returns:
            str: 編集結果
        """
        project_dir = self.rust_base_dir / project_name
        file_path = project_dir / "src" / file_name

        # プロジェクトが存在しない場合はエラー
        if not project_dir.exists():
            return f"Error: プロジェクト '{project_name}' が見つかりません。まず `create_rust_project` で作成してください。"

        # `.rs` 以外のファイル編集を防ぐ
        if not file_name.endswith(".rs"):
            return "Error: `.rs` ファイルのみ編集できます。Cargo.toml などの編集は許可されていません。"

        # ファイルが `src/` ディレクトリ内にあるか確認
        if not file_path.exists():
            return f"Error: ファイル `{file_name}` が見つかりません。"

        try:
            # ファイルの編集モードを選択
            if mode == "append":
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write("\n" + new_code + "\n")
                return f"Rust コードを `{file_name}` に **追加** しました。"
            elif mode == "overwrite":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                return f"Rust コードを `{file_name}` に **上書き** しました。"
            else:
                return (
                    "Error: `mode` は 'append' または 'overwrite' を指定してください。"
                )
        except Exception as e:
            return f"Error: Rust コードの編集に失敗しました。\n{str(e)}"

    async def run_rust_code(self, project_name: str) -> str:
        """
        Rust のコードを `cargo run` で安全に実行する（リアルタイムストリーム処理）

        Args:
            project_name (str): 実行するプロジェクトの名前

        Returns:
            str: 実行結果（標準出力 or エラー内容）
        """
        project_dir = self.rust_base_dir / project_name

        # プロジェクトが存在しない場合はエラー
        if not project_dir.exists():
            return f"Error: プロジェクト '{project_name}' が見つかりません。まず `create_rust_project` で作成してください。"

        # cargo_pathがNoneの場合はエラー
        if self.cargo_path is None:
            return "Error: cargoコマンドが見つかりません。Rustがインストールされているか確認してください。"

        try:
            process = subprocess.Popen(
                [self.cargo_path, "run"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # リアルタイムで出力を取得
            output_lines = []
            start_time = time.time()

            while True:
                if process.poll() is not None:  # プロセスが終了した場合
                    break

                # 実行時間が 5分を超えたら強制終了
                if time.time() - start_time > 5 * 60:
                    process.terminate()
                    return "Error: Execution timed out."

                # 標準出力を取得
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(line.strip())

                # 標準エラーを取得
                if process.stderr:
                    err_line = process.stderr.readline()
                    if err_line:
                        output_lines.append("Error: " + err_line.strip())

            # 残りの出力を取得
            stdout, stderr = process.communicate()

            if stdout:
                output_lines.extend(stdout.split("\n"))
            if stderr:
                output_lines.append("Error: " + stderr)

            # 出力が多すぎる場合は省略
            if len(output_lines) > 100:
                output_lines = output_lines[:50] + ["..."] + output_lines[-50:]

            return "\n".join(output_lines)

        except subprocess.TimeoutExpired:
            process.terminate()
            return "Error: Execution timed out."
        except Exception as e:
            return f"Error: {str(e)}"

    async def install_rust_library(self, project_name: str, crate_name: str) -> str:
        """
        Rust プロジェクトに `cargo add` でクレートを追加する

        Args:
            project_name (str): クレートを追加するプロジェクトの名前
            crate_name (str): 追加するクレートの名前

        Returns:
            str: クレート追加の成否メッセージ
        """
        project_dir = self.rust_base_dir / project_name

        # プロジェクトが存在しない場合はエラー
        if not project_dir.exists():
            return f"Error: プロジェクト '{project_name}' が見つかりません。まず `create_rust_project` で作成してください。"

        # cargo_pathがNoneの場合はエラー
        if self.cargo_path is None:
            return "Error: cargoコマンドが見つかりません。Rustがインストールされているか確認してください。"

        try:
            result = subprocess.run(
                [self.cargo_path, "add", crate_name],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )

            return (
                f"Crate '{crate_name}' を '{project_name}' に追加しました。"
                if result.returncode == 0
                else f"Error: {result.stderr}"
            )
        except Exception as e:
            return f"Error: {str(e)}"
