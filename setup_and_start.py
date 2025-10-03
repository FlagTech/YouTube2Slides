#!/usr/bin/env python3
"""
YouTube 影片懶人觀看術 - 自動安裝與啟動腳本
自動檢查並安裝所有依賴，然後啟動服務
"""

import subprocess
import sys
import os
import platform
import urllib.request
import tempfile
import shutil
from pathlib import Path

def print_header():
    """顯示標題"""
    print("=" * 60)
    print("  YouTube 影片懶人觀看術 - 自動安裝與啟動")
    print("=" * 60)
    print()

def check_command(command):
    """檢查命令是否存在"""
    try:
        subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_python_windows():
    """在 Windows 上安裝 Python"""
    print("[安裝] 正在下載 Python...")
    url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

    with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tmp:
        urllib.request.urlretrieve(url, tmp.name)
        installer = tmp.name

    print("[安裝] 正在安裝 Python（這可能需要幾分鐘）...")
    subprocess.run([installer, '/quiet', 'InstallAllUsers=1', 'PrependPath=1'], check=True)
    os.unlink(installer)
    print("✓ Python 安裝完成")

def install_nodejs_windows():
    """在 Windows 上安裝 Node.js"""
    print("[安裝] 正在下載 Node.js...")
    url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"

    with tempfile.NamedTemporaryFile(delete=False, suffix='.msi') as tmp:
        urllib.request.urlretrieve(url, tmp.name)
        installer = tmp.name

    print("[安裝] 正在安裝 Node.js（這可能需要幾分鐘）...")
    subprocess.run(['msiexec', '/i', installer, '/quiet', '/norestart'], check=True)
    os.unlink(installer)
    print("✓ Node.js 安裝完成")

def install_ffmpeg_windows():
    """在 Windows 上安裝 ffmpeg"""
    print("[安裝] 正在下載 ffmpeg...")
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        urllib.request.urlretrieve(url, tmp.name)
        zip_file = tmp.name

    print("[安裝] 正在解壓縮 ffmpeg...")
    ffmpeg_dir = Path("C:/ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)

    import zipfile
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(ffmpeg_dir)

    # 找到 bin 目錄
    bin_dirs = list(ffmpeg_dir.glob("ffmpeg-*/bin"))
    if bin_dirs:
        bin_path = str(bin_dirs[0])

        # 加入系統 PATH
        current_path = os.environ.get('PATH', '')
        if bin_path not in current_path:
            os.environ['PATH'] = f"{current_path};{bin_path}"

            # 嘗試永久設定（需要管理員權限）
            try:
                subprocess.run(['setx', '/M', 'PATH', f"{current_path};{bin_path}"],
                             check=False, capture_output=True)
            except:
                print("[提示] 無法永久設定 PATH，本次運行仍可使用")

    os.unlink(zip_file)
    print("✓ ffmpeg 安裝完成")

def install_with_package_manager():
    """使用套件管理器安裝依賴"""
    system = platform.system()

    if system == "Darwin":  # macOS
        print("[提示] 在 macOS 上，建議使用 Homebrew 安裝依賴")
        print("請執行以下命令：")
        print("  brew install python node ffmpeg")
        print()
        response = input("是否已安裝 Homebrew? (y/n): ").lower()
        if response == 'y':
            subprocess.run(['brew', 'install', 'python', 'node', 'ffmpeg'])
        else:
            print("請先安裝 Homebrew: https://brew.sh/")
            sys.exit(1)

    elif system == "Linux":
        print("[提示] 在 Linux 上，建議使用套件管理器安裝依賴")
        print("請執行以下命令（需要管理員權限）：")
        print("  sudo apt update")
        print("  sudo apt install python3 python3-pip nodejs npm ffmpeg")
        print()
        response = input("是否現在安裝? (y/n): ").lower()
        if response == 'y':
            subprocess.run(['sudo', 'apt', 'update'])
            subprocess.run(['sudo', 'apt', 'install', '-y', 'python3', 'python3-pip', 'nodejs', 'npm', 'ffmpeg'])
        else:
            print("請手動安裝依賴")
            sys.exit(1)

def install_uv():
    """安裝 uv"""
    print("[安裝] 正在安裝 uv...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)
        print("✓ uv 安裝完成")
    except subprocess.CalledProcessError:
        print("[錯誤] uv 安裝失敗")
        sys.exit(1)

def check_and_install_dependencies():
    """檢查並安裝所有依賴"""
    print("[檢查] 正在檢查系統環境...\n")

    system = platform.system()
    needs_install = []

    # 檢查 Python (應該已經有，因為正在運行這個腳本)
    if check_command('python') or check_command('python3'):
        print("✓ Python 已安裝")
    else:
        print("✗ 找不到 Python")
        needs_install.append('python')

    # 檢查 Node.js
    if check_command('node'):
        print("✓ Node.js 已安裝")
    else:
        print("✗ 找不到 Node.js")
        needs_install.append('node')

    # 檢查 ffmpeg
    if check_command('ffmpeg'):
        print("✓ ffmpeg 已安裝")
    else:
        print("✗ 找不到 ffmpeg")
        needs_install.append('ffmpeg')

    # 檢查 uv
    if check_command('uv'):
        print("✓ uv 已安裝")
    else:
        print("✗ 找不到 uv")
        needs_install.append('uv')

    print()

    # 如果有缺少的依賴
    if needs_install:
        print(f"[提示] 發現缺少以下工具: {', '.join(needs_install)}\n")

        if system == "Windows":
            response = input("是否自動安裝? (y/n): ").lower()
            if response != 'y':
                print("請手動安裝依賴後再運行此腳本")
                sys.exit(1)

            print("\n[提示] 需要管理員權限來安裝軟體")
            print("若出現 UAC 提示，請點擊「是」\n")

            if 'node' in needs_install:
                try:
                    install_nodejs_windows()
                except Exception as e:
                    print(f"[錯誤] Node.js 安裝失敗: {e}")
                    print("請手動下載安裝: https://nodejs.org/")

            if 'ffmpeg' in needs_install:
                try:
                    install_ffmpeg_windows()
                except Exception as e:
                    print(f"[錯誤] ffmpeg 安裝失敗: {e}")
                    print("請手動下載安裝: https://www.gyan.dev/ffmpeg/builds/")

            if 'uv' in needs_install:
                install_uv()

        else:  # macOS or Linux
            install_with_package_manager()
            if 'uv' in needs_install:
                install_uv()

    print()

def setup_project():
    """設置專案環境"""
    print("[設定] 正在初始化專案環境...\n")

    backend_venv = Path('backend/.venv')
    frontend_modules = Path('frontend/node_modules')

    # 檢查後端虛擬環境
    if not backend_venv.exists():
        print("[提示] 首次運行，正在初始化後端環境...")
        subprocess.run(['uv', 'venv'], cwd='backend', check=True)
        print("✓ 後端環境初始化完成")

    # 檢查前端依賴
    if not frontend_modules.exists():
        print("[提示] 首次運行，正在安裝前端依賴...")
        subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        print("✓ 前端依賴安裝完成")

    print()

def start_services():
    """啟動前後端服務"""
    print("=" * 60)
    print("  所有依賴已就緒！")
    print("=" * 60)
    print()
    print("正在啟動服務...\n")

    # 啟動後端
    print("[啟動] 後端服務器 (Port 8000)")

    backend_cmd = ['uv', 'run', 'uvicorn', 'app:app', '--reload', '--host', '0.0.0.0', '--port', '8000']

    if platform.system() == 'Windows':
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd='backend',
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd='backend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    # 等待後端啟動
    print("等待後端服務啟動...")
    import time
    time.sleep(3)

    # 啟動前端
    print("[啟動] 前端服務器 (Port 3000)")

    frontend_cmd = ['npm', 'start']

    if platform.system() == 'Windows':
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd='frontend',
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            shell=True
        )
    else:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd='frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    print()
    print("=" * 60)
    print("  所有服務已啟動！")
    print("=" * 60)
    print()
    print("後端服務: http://localhost:8000")
    print("前端服務: http://localhost:3000")
    print("API 文檔: http://localhost:8000/docs")
    print()

    if platform.system() == 'Windows':
        print("服務已在新視窗中啟動")
        print("若要停止服務，請關閉對應的視窗")
        print()
        input("按 Enter 鍵退出此腳本...")
    else:
        print("按 Ctrl+C 停止所有服務")
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n正在停止服務...")
            backend_process.terminate()
            frontend_process.terminate()
            backend_process.wait()
            frontend_process.wait()
            print("服務已停止")

def main():
    """主函數"""
    print_header()

    try:
        # 檢查並安裝依賴
        check_and_install_dependencies()

        # 設置專案環境
        setup_project()

        # 啟動服務
        start_services()

    except KeyboardInterrupt:
        print("\n\n程序已中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n[錯誤] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
