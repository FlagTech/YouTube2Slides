#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# 設定 Windows 終端機的 UTF-8 編碼
if platform.system() == 'Windows':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def print_header():
    """顯示標題"""
    print("=" * 60)
    print("  YouTube 影片懶人觀看術 - 自動安裝與啟動")
    print("=" * 60)
    print()

def check_command(command):
    """檢查命令是否存在"""
    try:
        result = subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            encoding='utf-8',
            errors='ignore'
        )
        # 對於某些命令，即使成功也可能返回非零代碼
        # 只要能執行且有輸出就視為存在
        return result.returncode == 0 or len(result.stdout) > 0 or len(result.stderr) > 0
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"  [除錯] 檢查 {command} 時發生錯誤: {e}")
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
        print("[提示] 下載中，這可能需要幾分鐘...")
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

        print(f"[安裝] ffmpeg 已解壓至: {bin_path}")

        # 加入當前進程的 PATH
        current_path = os.environ.get('PATH', '')
        if bin_path not in current_path:
            os.environ['PATH'] = f"{bin_path};{current_path}"

        # 永久設定系統 PATH（使用 PowerShell）
        try:
            print("[安裝] 正在將 ffmpeg 加入系統 PATH...")

            # 使用 PowerShell 讀取當前系統 PATH
            ps_get_path = '[Environment]::GetEnvironmentVariable("Path", "Machine")'
            result = subprocess.run(
                ['powershell', '-Command', ps_get_path],
                capture_output=True,
                text=True,
                check=True
            )
            system_path = result.stdout.strip()

            # 檢查是否已經在 PATH 中
            if bin_path not in system_path:
                new_path = f"{system_path};{bin_path}"

                # 使用 PowerShell 設定新的 PATH
                ps_set_path = f'[Environment]::SetEnvironmentVariable("Path", "{new_path}", "Machine")'
                subprocess.run(
                    ['powershell', '-Command', ps_set_path],
                    check=True,
                    capture_output=True
                )
                print("✓ ffmpeg 已成功加入系統 PATH")
            else:
                print("✓ ffmpeg 已在系統 PATH 中")

        except subprocess.CalledProcessError as e:
            print("[警告] 無法永久設定 PATH（可能需要管理員權限）")
            print(f"[提示] 請手動將以下路徑加入系統環境變數 PATH:")
            print(f"       {bin_path}")
        except Exception as e:
            print(f"[警告] PATH 設定失敗: {e}")
            print(f"[提示] 請手動將以下路徑加入系統環境變數 PATH:")
            print(f"       {bin_path}")

    os.unlink(zip_file)
    print("✓ ffmpeg 安裝完成")

    return bin_dirs[0] if bin_dirs else None

def install_with_package_manager():
    """使用套件管理器安裝依賴"""
    system = platform.system()

    if system == "Darwin":  # macOS
        print("[提示] 在 macOS 上，建議使用 Homebrew 安裝依賴")

        # 檢查是否已安裝 Homebrew
        has_brew = False
        try:
            subprocess.run(['brew', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            has_brew = True
            print("✓ 偵測到 Homebrew 已安裝")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ 未安裝 Homebrew")

        if has_brew:
            print("\n準備使用 Homebrew 安裝缺少的套件...")
            response = input("是否繼續? (y/n): ").lower()
            if response == 'y':
                try:
                    subprocess.run(['brew', 'install', 'python', 'node', 'ffmpeg'], check=False)
                    print("✓ 套件安裝完成")
                except Exception as e:
                    print(f"⚠ 安裝過程中發生錯誤: {e}")
            else:
                print("請手動安裝缺少的套件")
                sys.exit(1)
        else:
            print("\n請先安裝 Homebrew:")
            print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("\n或手動安裝所需套件後再執行此腳本")
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
    missing_required = []
    ffmpeg_path = None

    # 檢查 Python (應該已經有，因為正在運行這個腳本)
    if check_command('python') or check_command('python3'):
        print("✓ Python 已安裝")
    else:
        print("✗ 找不到 Python")
        missing_required.append('Python')

    # 檢查 Node.js
    if check_command('node'):
        print("✓ Node.js 已安裝")
    else:
        print("✗ 找不到 Node.js")
        missing_required.append('Node.js')

    # 檢查 ffmpeg
    ffmpeg_found = check_command('ffmpeg')

    # 如果系統 PATH 中沒有 ffmpeg，檢查本地安裝
    if not ffmpeg_found and system == "Windows":
        local_ffmpeg_dir = Path("C:/ffmpeg")
        if local_ffmpeg_dir.exists():
            bin_dirs = list(local_ffmpeg_dir.glob("ffmpeg-*/bin"))
            if bin_dirs:
                ffmpeg_path = bin_dirs[0]
                # 加入當前環境變數
                current_path = os.environ.get('PATH', '')
                ffmpeg_bin = str(ffmpeg_path)
                if ffmpeg_bin not in current_path:
                    os.environ['PATH'] = f"{ffmpeg_bin};{current_path}"
                    print(f"✓ ffmpeg 已安裝（在 {ffmpeg_bin}）")
                    ffmpeg_found = True

    if ffmpeg_found:
        if not ffmpeg_path:
            print("✓ ffmpeg 已安裝")
    else:
        print("✗ 找不到 ffmpeg")
        missing_required.append('ffmpeg')

    # 檢查 uv
    if check_command('uv'):
        print("✓ uv 已安裝")
    else:
        print("✗ 找不到 uv")
        needs_install.append('uv')

    print()

    # 如果缺少必要的依賴（Python、Node.js、ffmpeg）
    if missing_required:
        print(f"[錯誤] 缺少必要的工具: {', '.join(missing_required)}\n")
        print("請先安裝以下工具：\n")

        if 'Python' in missing_required:
            print("  Python 3.9+")
            print("  下載: https://www.python.org/downloads/")
            print()

        if 'Node.js' in missing_required:
            print("  Node.js 16+")
            print("  下載: https://nodejs.org/")
            print()

        if 'ffmpeg' in missing_required:
            print("  ffmpeg")
            if system == "Windows":
                print("  方法 1: choco install ffmpeg")
                print("  方法 2: https://www.gyan.dev/ffmpeg/builds/")
            elif system == "Darwin":
                print("  方法: brew install ffmpeg")
            else:
                print("  方法: sudo apt install ffmpeg")
            print()

        print("安裝完成後請重新執行此腳本")
        sys.exit(1)

    # 只自動安裝 uv
    if 'uv' in needs_install:
        print("[提示] 正在自動安裝 uv...\n")
        install_uv()
        print()

    return ffmpeg_path

def setup_project():
    """設置專案環境"""
    print("[設定] 正在初始化專案環境...\n")

    backend_venv = Path('backend/.venv')
    frontend_modules = Path('frontend/node_modules')

    # 檢查後端虛擬環境與依賴
    if not backend_venv.exists():
        print("[提示] 首次運行，正在初始化後端環境...")
        subprocess.run(['uv', 'venv'], cwd='backend', check=True)
        print("✓ 後端虛擬環境創建完成")

        print("[提示] 正在安裝後端依賴套件...")
        subprocess.run(['uv', 'sync'], cwd='backend', check=True)
        print("✓ 後端依賴安裝完成")
    else:
        # 檢查是否需要更新依賴
        print("[檢查] 檢查後端依賴是否需要更新...")
        try:
            subprocess.run(['uv', 'sync', '--no-install-project'], cwd='backend', check=True)
            print("✓ 後端依賴已是最新")
        except subprocess.CalledProcessError:
            print("⚠ 後端依賴更新失敗，請手動執行: cd backend && uv sync")

    # 檢查前端依賴
    if not frontend_modules.exists():
        print("[提示] 首次運行，正在安裝前端依賴...")
        subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        print("✓ 前端依賴安裝完成")
    else:
        print("✓ 前端依賴已存在")

    print()

def start_services(ffmpeg_path=None):
    """啟動前後端服務"""
    print("=" * 60)
    print("  所有依賴已就緒！")
    print("=" * 60)
    print()
    print("正在啟動服務...\n")

    # 準備環境變數
    env = os.environ.copy()

    # 如果有 ffmpeg 路徑，確保加入 PATH
    if ffmpeg_path:
        ffmpeg_bin = str(ffmpeg_path)
        current_path = env.get('PATH', '')
        if ffmpeg_bin not in current_path:
            env['PATH'] = f"{ffmpeg_bin};{current_path}"
            print(f"[提示] 已將 ffmpeg 路徑加入服務環境變數: {ffmpeg_bin}")

    # 啟動後端
    print("[啟動] 後端服務器 (Port 8000)")

    backend_cmd = ['uv', 'run', 'uvicorn', 'app:app', '--reload', '--host', '0.0.0.0', '--port', '8000']

    if platform.system() == 'Windows':
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd='backend',
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # macOS/Linux: 在背景執行並顯示輸出
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd='backend',
            env=env
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
        # macOS/Linux: 在背景執行並顯示輸出
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd='frontend'
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
        print("服務正在執行中...")
        print("按 Ctrl+C 停止所有服務")
        print()
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n正在停止服務...")
            backend_process.terminate()
            frontend_process.terminate()
            try:
                backend_process.wait(timeout=5)
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
                frontend_process.kill()
            print("✓ 服務已停止")

def main():
    """主函數"""
    print_header()

    try:
        # 檢查並安裝依賴
        ffmpeg_path = check_and_install_dependencies()

        # 設置專案環境
        setup_project()

        # 啟動服務
        start_services(ffmpeg_path)

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
