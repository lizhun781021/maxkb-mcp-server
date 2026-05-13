#!/usr/bin/env python3
"""
Obsidian Vault 文件监控器
监控 Obsidian vault 文件变化，自动同步到 MaxKB
"""

import os
import sys
import time
import glob
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置
MAXKB_BASE_URL = os.environ.get("MAXKB_BASE_URL", "http://localhost:8080")
MAXKB_API_TOKEN = os.environ.get("MAXKB_API_TOKEN", None)
VAULT_PATH = os.environ.get("VAULT_PATH", "/Users/lizhun/Library/Mobile Documents/iCloud~md~obsidian/Documents/my obsidian vault")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "019e0aad-c958-7e30-94aa-0a31cb7dc1a7")

# 同步间隔（秒）- 防止频繁同步
SYNC_INTERVAL = 5
last_sync_time = {}


def get_headers():
    """获取请求头"""
    if MAXKB_API_TOKEN:
        return {"Authorization": f"Bearer {MAXKB_API_TOKEN}"}
    return {}


def login(username: str, password: str) -> str:
    """登录获取 token"""
    global MAXKB_API_TOKEN
    try:
        url = f"{MAXKB_BASE_URL}/admin/api/user/login"
        payload = {"username": username, "password": password, "captcha": ""}
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                token = data.get("data", {}).get("token")
                if token:
                    MAXKB_API_TOKEN = token
                    return token
        return None
    except Exception as e:
        print(f"[ERROR] 登录失败: {e}")
        return None


def sync_file(file_path: str):
    """同步单个文件到 MaxKB"""
    global last_sync_time

    # 检查是否是 markdown 文件
    if not file_path.endswith(".md"):
        return

    # 检查同步间隔
    now = time.time()
    if file_path in last_sync_time and now - last_sync_time[file_path] < SYNC_INTERVAL:
        return

    # 检查文件是否存在（可能是删除操作）
    if not os.path.exists(file_path):
        print(f"[INFO] 文件已删除，跳过: {os.path.basename(file_path)}")
        return

    try:
        file_name = os.path.basename(file_path)
        doc_name = file_name.replace(".md", "")

        print(f"[SYNC] 同步文件: {file_name}")

        headers = get_headers()

        # Step 1: 解析文件
        split_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{KNOWLEDGE_BASE_ID}/document/split"
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "text/markdown")}
            split_response = requests.post(split_url, files=files, headers=headers, timeout=60)

        if split_response.status_code != 200:
            print(f"[ERROR] 解析失败: {split_response.status_code}")
            return

        split_result = split_response.json()
        if split_result.get("code") != 200:
            print(f"[ERROR] 解析失败: {split_result.get('message')}")
            return

        doc_data = split_result.get("data", [])
        if not doc_data:
            print(f"[WARN] 文件解析后无内容: {file_name}")
            return

        paragraphs = doc_data[0].get("content", [])
        if not paragraphs:
            print(f"[WARN] 文件解析后无段落: {file_name}")
            return

        # Step 2: 检查文档是否已存在
        list_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{KNOWLEDGE_BASE_ID}/document/1/100"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        existing_doc_id = None

        if list_response.status_code == 200:
            list_data = list_response.json()
            if list_data.get("code") == 200:
                for doc in list_data.get("data", {}).get("records", []):
                    if doc.get("name") == doc_name:
                        existing_doc_id = doc.get("id")
                        break

        # Step 3: 更新或创建文档
        if existing_doc_id:
            # 更新现有文档 - 先删除再创建
            delete_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{KNOWLEDGE_BASE_ID}/document/{existing_doc_id}"
            requests.delete(delete_url, headers=headers, timeout=10)

        # 创建新文档
        create_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{KNOWLEDGE_BASE_ID}/document"
        payload = {
            "name": doc_name,
            "paragraphs": [{"content": p.get("content", ""), "title": p.get("title", "")} for p in paragraphs]
        }
        json_headers = {**headers, "Content-Type": "application/json"}
        create_response = requests.post(create_url, json=payload, headers=json_headers, timeout=60)

        if create_response.status_code == 200:
            result = create_response.json()
            if result.get("code") == 200:
                last_sync_time[file_path] = now
                action = "更新" if existing_doc_id else "创建"
                print(f"[OK] {action}成功: {file_name} ({len(paragraphs)} 段落)")
            else:
                print(f"[ERROR] 创建失败: {result.get('message')}")
        else:
            print(f"[ERROR] 创建失败: {create_response.status_code}")

    except Exception as e:
        print(f"[ERROR] 同步失败 {file_name}: {e}")


class MarkdownHandler(FileSystemEventHandler):
    """Markdown 文件变化处理器"""

    def on_created(self, event):
        if not event.is_directory:
            print(f"[EVENT] 文件创建: {event.src_path}")
            sync_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[EVENT] 文件修改: {event.src_path}")
            sync_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"[EVENT] 文件删除: {event.src_path}")
            # 删除操作需要手动处理，这里先跳过

    def on_moved(self, event):
        if not event.is_directory:
            print(f"[EVENT] 文件移动: {event.src_path} -> {event.dest_path}")
            sync_file(event.dest_path)


def main():
    """主函数"""
    global MAXKB_BASE_URL, MAXKB_API_TOKEN, VAULT_PATH, KNOWLEDGE_BASE_ID

    print("=" * 50)
    print("Obsidian Vault 文件监控器")
    print("=" * 50)
    print(f"Vault 路径: {VAULT_PATH}")
    print(f"MaxKB 地址: {MAXKB_BASE_URL}")
    print(f"知识库 ID: {KNOWLEDGE_BASE_ID}")
    print(f"同步间隔: {SYNC_INTERVAL} 秒")
    print("=" * 50)

    # 检查 vault 路径
    if not os.path.exists(VAULT_PATH):
        print(f"[ERROR] Vault 路径不存在: {VAULT_PATH}")
        sys.exit(1)

    # 登录（如果未配置 token）
    if not MAXKB_API_TOKEN:
        print("\n[INFO] 未配置 token，尝试登录...")
        username = input("用户名: ").strip()
        password = input("密码: ").strip()
        token = login(username, password)
        if not token:
            print("[ERROR] 登录失败")
            sys.exit(1)
        print("[OK] 登录成功")

    # 启动文件监控
    print("\n[INFO] 启动文件监控...")
    event_handler = MarkdownHandler()
    observer = Observer()
    observer.schedule(event_handler, VAULT_PATH, recursive=True)
    observer.start()

    print("[OK] 监控已启动，按 Ctrl+C 停止")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 停止监控...")
        observer.stop()

    observer.join()
    print("[OK] 监控已停止")


if __name__ == "__main__":
    main()
