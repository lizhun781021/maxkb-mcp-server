#!/usr/bin/env python3
"""
MaxKB MCP Server
连接 MaxKB 知识库的 MCP 服务器（支持社区版）
支持 Obsidian vault 同步
"""

import json
import sys
import os
import glob
import requests
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

# MaxKB 配置
MAXKB_BASE_URL = "http://localhost:8080"
MAXKB_API_TOKEN = None

# 创建 MCP 服务器
server = Server("maxkb")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="maxkb_login",
            description="登录 MaxKB 获取 API Token",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "用户名"
                    },
                    "password": {
                        "type": "string",
                        "description": "密码"
                    }
                },
                "required": ["username", "password"]
            }
        ),
        Tool(
            name="maxkb_list_knowledge_bases",
            description="列出所有知识库",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="maxkb_create_knowledge_base",
            description="创建新知识库",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "知识库名称"
                    },
                    "desc": {
                        "type": "string",
                        "description": "知识库描述（可选）"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="maxkb_search",
            description="在知识库中搜索文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "知识库 ID（可选，不指定则搜索所有）"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="maxkb_list_documents",
            description="列出知识库中的文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "知识库 ID"
                    }
                },
                "required": ["knowledge_base_id"]
            }
        ),
        Tool(
            name="maxkb_upload_markdown",
            description="上传 Markdown 文件到知识库",
            inputSchema={
                "type": "object",
                "properties": {
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "知识库 ID"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Markdown 文件路径"
                    }
                },
                "required": ["knowledge_base_id", "file_path"]
            }
        ),
        Tool(
            name="maxkb_sync_obsidian",
            description="同步 Obsidian vault 到 MaxKB",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Obsidian vault 路径"
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "目标知识库 ID（可选，不指定则创建新知识库）"
                    }
                },
                "required": ["vault_path"]
            }
        ),
        Tool(
            name="maxkb_list_applications",
            description="列出所有应用",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="maxkb_chat",
            description="与 MaxKB 应用对话",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "string",
                        "description": "应用 ID"
                    },
                    "query": {
                        "type": "string",
                        "description": "用户问题"
                    }
                },
                "required": ["application_id", "query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """调用工具"""
    global MAXKB_API_TOKEN

    if name == "maxkb_login":
        return await login(arguments.get("username"), arguments.get("password"))
    elif name == "maxkb_list_knowledge_bases":
        return await list_knowledge_bases()
    elif name == "maxkb_create_knowledge_base":
        return await create_knowledge_base(arguments.get("name"), arguments.get("desc"))
    elif name == "maxkb_search":
        return await search(arguments.get("query"), arguments.get("knowledge_base_id"))
    elif name == "maxkb_list_documents":
        return await list_documents(arguments.get("knowledge_base_id"))
    elif name == "maxkb_upload_markdown":
        return await upload_markdown(arguments.get("knowledge_base_id"), arguments.get("file_path"))
    elif name == "maxkb_sync_obsidian":
        return await sync_obsidian(arguments.get("vault_path"), arguments.get("knowledge_base_id"))
    elif name == "maxkb_list_applications":
        return await list_applications()
    elif name == "maxkb_chat":
        return await chat(arguments.get("application_id"), arguments.get("query"))
    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


def get_headers():
    """获取请求头"""
    if MAXKB_API_TOKEN:
        return {"Authorization": f"Bearer {MAXKB_API_TOKEN}"}
    return {}


async def login(username: str, password: str) -> List[TextContent]:
    """登录 MaxKB"""
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
                    return [TextContent(type="text", text="登录成功！Token 已保存。")]
            return [TextContent(type="text", text=f"登录失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"登录失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"登录出错: {str(e)}")]


async def list_knowledge_bases() -> List[TextContent]:
    """列出所有知识库"""
    try:
        headers = get_headers()
        url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/1/100?folder_id=default&scope=WORKSPACE"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                records = data.get("data", {}).get("records", [])

                if not records:
                    return [TextContent(type="text", text="没有找到知识库")]

                text = "知识库列表：\n\n"
                for kb in records:
                    kb_id = kb.get("id")
                    name = kb.get("name")
                    desc = kb.get("desc", "")
                    doc_count = kb.get("document_count", 0)
                    text += f"- {name} (ID: {kb_id})\n"
                    if desc:
                        text += f"  描述: {desc}\n"
                    text += f"  文档数: {doc_count}\n\n"

                return [TextContent(type="text", text=text)]
            else:
                return [TextContent(type="text", text=f"获取知识库失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"获取知识库失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"获取知识库出错: {str(e)}")]


async def create_knowledge_base(name: str, desc: str = None) -> List[TextContent]:
    """创建新知识库"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge"

        payload = {
            "name": name,
            "desc": desc or f"{name}的知识库",
            "type": 0
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                kb_id = data.get("data", {}).get("id")
                return [TextContent(type="text", text=f"知识库创建成功！\n\n名称: {name}\nID: {kb_id}")]
            else:
                return [TextContent(type="text", text=f"创建知识库失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"创建知识库失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"创建知识库出错: {str(e)}")]


async def search(query: str, knowledge_base_id: Optional[str] = None) -> List[TextContent]:
    """搜索知识库"""
    try:
        headers = get_headers()

        if knowledge_base_id:
            # 搜索指定知识库
            url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/hit_test"
            payload = {
                "query_text": query,
                "top_number": 5,
                "similarity": 0.1,
                "search_mode": "embedding"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    results = data.get("data", [])
                    if not results:
                        return [TextContent(type="text", text=f"未找到与 '{query}' 相关的文档")]

                    text = f"搜索结果（知识库 {knowledge_base_id}）：\n\n"
                    for i, result in enumerate(results[:5], 1):
                        title = result.get("title", "无标题")
                        content = result.get("content", "")[:200]
                        score = result.get("similarity", 0)
                        doc_name = result.get("document_name", "")
                        text += f"{i}. {title or doc_name} (相关度: {score:.2f})\n{content}...\n\n"

                    return [TextContent(type="text", text=text)]
                else:
                    return [TextContent(type="text", text=f"搜索失败: {data.get('message')}")]
            else:
                return [TextContent(type="text", text=f"搜索失败: {response.status_code}")]
        else:
            # 搜索所有知识库
            kb_list_resp = await list_knowledge_bases()
            return kb_list_resp
    except Exception as e:
        return [TextContent(type="text", text=f"搜索出错: {str(e)}")]


async def list_documents(knowledge_base_id: str) -> List[TextContent]:
    """列出知识库中的文档"""
    try:
        headers = get_headers()
        url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/document/1/100"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                records = data.get("data", {}).get("records", [])

                if not records:
                    return [TextContent(type="text", text="该知识库中没有文档")]

                text = f"文档列表（知识库 {knowledge_base_id}）：\n\n"
                for doc in records:
                    doc_id = doc.get("id")
                    name = doc.get("name")
                    text += f"- {name} (ID: {doc_id})\n"

                return [TextContent(type="text", text=text)]
            else:
                return [TextContent(type="text", text=f"获取文档列表失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"获取文档列表失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"获取文档列表出错: {str(e)}")]


async def upload_markdown(knowledge_base_id: str, file_path: str) -> List[TextContent]:
    """上传 Markdown 文件到知识库"""
    try:
        if not os.path.exists(file_path):
            return [TextContent(type="text", text=f"文件不存在: {file_path}")]

        headers = get_headers()
        file_name = os.path.basename(file_path)
        doc_name = file_name.replace(".md", "")

        # Step 1: Parse the file using the Split endpoint
        split_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/document/split"
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "text/markdown")}
            split_response = requests.post(split_url, files=files, headers=headers, timeout=60)

        if split_response.status_code != 200:
            return [TextContent(type="text", text=f"解析文件失败: {split_response.status_code}")]

        split_result = split_response.json()
        if split_result.get("code") != 200:
            return [TextContent(type="text", text=f"解析文件失败: {split_result.get('message')}")]

        # The split response data is a list of documents
        doc_data = split_result.get("data", [])
        if not doc_data:
            return [TextContent(type="text", text=f"文件 '{doc_name}' 解析后没有内容")]

        # Get paragraphs from the first document
        paragraphs = doc_data[0].get("content", [])
        if not paragraphs:
            return [TextContent(type="text", text=f"文件 '{doc_name}' 解析后没有段落内容")]

        # Step 2: Create the document with parsed paragraphs
        create_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/document"
        payload = {
            "name": doc_name,
            "paragraphs": [{"content": p.get("content", ""), "title": p.get("title", "")} for p in paragraphs]
        }
        headers["Content-Type"] = "application/json"
        create_response = requests.post(create_url, json=payload, headers=headers, timeout=60)

        if create_response.status_code == 200:
            result = create_response.json()
            if result.get("code") == 200:
                doc_id = result.get("data", {}).get("id")
                return [TextContent(type="text", text=f"文档 '{doc_name}' 上传成功！\n文档 ID: {doc_id}\n段落数: {len(paragraphs)}")]
            else:
                return [TextContent(type="text", text=f"创建文档失败: {result.get('message')}")]
        else:
            return [TextContent(type="text", text=f"创建文档失败: {create_response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"上传出错: {str(e)}")]


async def sync_obsidian(vault_path: str, knowledge_base_id: Optional[str] = None) -> List[TextContent]:
    """同步 Obsidian vault 到 MaxKB"""
    try:
        if not os.path.exists(vault_path):
            return [TextContent(type="text", text=f"Vault 路径不存在: {vault_path}")]

        # 查找所有 Markdown 文件
        md_files = glob.glob(os.path.join(vault_path, "**/*.md"), recursive=True)

        if not md_files:
            return [TextContent(type="text", text=f"在 {vault_path} 中未找到 Markdown 文件")]

        # 如果没有指定知识库，创建一个新的
        if not knowledge_base_id:
            vault_name = os.path.basename(vault_path)
            create_result = await create_knowledge_base(f"{vault_name}的笔记")
            # 从结果中提取知识库 ID
            if "ID:" in create_result[0].text:
                knowledge_base_id = create_result[0].text.split("ID:")[-1].strip()
            else:
                return [TextContent(type="text", text="创建知识库失败")]

        auth_headers = get_headers()
        success_count = 0
        fail_count = 0
        errors = []

        for md_file in md_files:
            try:
                file_name = os.path.basename(md_file)
                doc_name = file_name.replace(".md", "")

                # Step 1: Parse the file using the Split endpoint (multipart headers)
                split_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/document/split"
                with open(md_file, "rb") as f:
                    files = {"file": (file_name, f, "text/markdown")}
                    split_response = requests.post(split_url, files=files, headers=auth_headers, timeout=60)

                if split_response.status_code != 200:
                    fail_count += 1
                    errors.append(f"{file_name}: 解析失败 HTTP {split_response.status_code}")
                    continue

                split_result = split_response.json()
                if split_result.get("code") != 200:
                    fail_count += 1
                    errors.append(f"{file_name}: {split_result.get('message')}")
                    continue

                # The split response data is a list of documents
                doc_data = split_result.get("data", [])
                if not doc_data:
                    fail_count += 1
                    errors.append(f"{file_name}: 解析后没有内容")
                    continue

                # Get paragraphs from the first document
                paragraphs = doc_data[0].get("content", [])
                if not paragraphs:
                    fail_count += 1
                    errors.append(f"{file_name}: 解析后没有段落内容")
                    continue

                # Step 2: Create the document with parsed paragraphs (JSON headers)
                create_url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/knowledge/{knowledge_base_id}/document"
                payload = {
                    "name": doc_name,
                    "paragraphs": [{"content": p.get("content", ""), "title": p.get("title", "")} for p in paragraphs]
                }
                json_headers = {**auth_headers, "Content-Type": "application/json"}
                create_response = requests.post(create_url, json=payload, headers=json_headers, timeout=60)

                if create_response.status_code == 200:
                    result = create_response.json()
                    if result.get("code") == 200:
                        success_count += 1
                    else:
                        fail_count += 1
                        errors.append(f"{file_name}: {result.get('message')}")
                else:
                    fail_count += 1
                    errors.append(f"{file_name}: HTTP {create_response.status_code}")
            except Exception as e:
                fail_count += 1
                errors.append(f"{file_name}: {str(e)}")

        text = f"同步完成！\n\n"
        text += f"知识库 ID: {knowledge_base_id}\n"
        text += f"成功: {success_count} 个文件\n"
        text += f"失败: {fail_count} 个文件\n"

        if errors:
            text += "\n失败详情:\n"
            for error in errors[:10]:
                text += f"- {error}\n"

        return [TextContent(type="text", text=text)]
    except Exception as e:
        return [TextContent(type="text", text=f"同步出错: {str(e)}")]


async def list_applications() -> List[TextContent]:
    """列出所有应用"""
    try:
        headers = get_headers()
        url = f"{MAXKB_BASE_URL}/admin/api/workspace/default/application/1/100"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                records = data.get("data", {}).get("records", [])

                if not records:
                    return [TextContent(type="text", text="没有找到应用")]

                text = "应用列表：\n\n"
                for app in records:
                    app_id = app.get("id")
                    name = app.get("name")
                    text += f"- {name} (ID: {app_id})\n"

                return [TextContent(type="text", text=text)]
            else:
                return [TextContent(type="text", text=f"获取应用列表失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"获取应用列表失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"获取应用列表出错: {str(e)}")]


async def chat(application_id: str, query: str) -> List[TextContent]:
    """与 MaxKB 应用对话"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"

        url = f"{MAXKB_BASE_URL}/admin/api/application/{application_id}/chat/completions"
        payload = {"query": query, "stream": False}

        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                answer = data.get("data", {}).get("answer", "")
                if answer:
                    return [TextContent(type="text", text=answer)]
                return [TextContent(type="text", text="未获得回答")]
            else:
                return [TextContent(type="text", text=f"对话失败: {data.get('message')}")]
        else:
            return [TextContent(type="text", text=f"对话失败: {response.status_code}")]
    except Exception as e:
        return [TextContent(type="text", text=f"对话出错: {str(e)}")]


async def main():
    """主函数"""
    import asyncio
    from mcp.server.stdio import stdio_server

    global MAXKB_BASE_URL, MAXKB_API_TOKEN

    if "MAXKB_BASE_URL" in os.environ:
        MAXKB_BASE_URL = os.environ["MAXKB_BASE_URL"]

    if "MAXKB_API_TOKEN" in os.environ:
        MAXKB_API_TOKEN = os.environ["MAXKB_API_TOKEN"]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
