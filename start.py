#!/usr/bin/env python3
"""
YouTube 影片懶人觀看術 - 啟動腳本
同時啟動前端和後端服務
"""

import subprocess
import sys
import os
import time
import platform
from pathlib import Path

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

def print_header():
    """顯示標題"""
    print("=" * 50)
    print("  YouTube 影片懶人觀看術")
    print("=" * 50)
    print()

def check_dependencies():
    """檢查必要的依賴"""
    print("檢查系統依賴...")

    # 檢查 uv
    if not check_command('uv'):
        print("[錯誤] 找不到 uv，請先安裝 uv")
        print("安裝方式: pip install uv")
        sys.exit(1)

    # 檢查 Node.js
    if not check_command('node'):
        print("[錯誤] 找不到 Node.js，請先安裝 Node.js")
        print("下載地址: https://nodejs.org/")
        sys.exit(1)

    print("✓ 所有依賴已就緒")
    print()

def setup_backend():
    """設置後端環境"""
    backend_dir = Path('backend')
    venv_dir = backend_dir / '.venv'

    if not venv_dir.exists():
        print("[提示] 首次運行，正在初始化後端環境...")
        subprocess.run(['uv', 'venv'], cwd=backend_dir, check=True)
        print("✓ 後端環境初始化完成")

def setup_frontend():
    """設置前端環境"""
    frontend_dir = Path('frontend')
    node_modules = frontend_dir / 'node_modules'

    if not node_modules.exists():
        print("[提示] 首次運行，正在安裝前端依賴...")
        subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        print("✓ 前端依賴安裝完成")

def start_backend():
    """啟動後端服務"""
    print("[啟動] 後端服務器 (Port 8000)")

    cmd = ['uv', 'run', 'uvicorn', 'app:app', '--reload', '--host', '0.0.0.0', '--port', '8000']

    # Windows 使用 CREATE_NEW_CONSOLE 在新視窗啟動
    if platform.system() == 'Windows':
        return subprocess.Popen(
            cmd,
            cwd='backend',
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Unix-like 系統
        return subprocess.Popen(
            cmd,
            cwd='backend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def start_frontend():
    """啟動前端服務"""
    print("[啟動] 前端服務器 (Port 3000)")

    cmd = ['npm', 'start']

    # Windows 使用 CREATE_NEW_CONSOLE 在新視窗啟動
    if platform.system() == 'Windows':
        return subprocess.Popen(
            cmd,
            cwd='frontend',
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            shell=True
        )
    else:
        # Unix-like 系統
        return subprocess.Popen(
            cmd,
            cwd='frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def main():
    """主函數"""
    print_header()

    # 檢查依賴
    check_dependencies()

    # 設置環境
    setup_backend()
    setup_frontend()

    print()
    print("=" * 50)
    print("  啟動服務中...")
    print("=" * 50)
    print()

    # 啟動後端
    backend_process = start_backend()

    # 等待後端啟動
    print("等待後端服務啟動...")
    time.sleep(3)

    # 啟動前端
    frontend_process = start_frontend()

    print()
    print("=" * 50)
    print("  所有服務已啟動！")
    print("=" * 50)
    print()
    print("後端服務: http://localhost:8000")
    print("前端服務: http://localhost:3000")
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

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已終止")
        sys.exit(0)
    except Exception as e:
        print(f"\n[錯誤] {e}")
        sys.exit(1)
