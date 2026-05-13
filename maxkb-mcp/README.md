# MaxKB MCP Server

连接 MaxKB 知识库的 MCP 服务器，支持 Obsidian vault 同步。

## 功能

- 登录认证
- 列出所有知识库
- 创建新知识库
- 搜索知识库文档（支持向量搜索）
- 列出知识库中的文档
- 上传 Markdown 文件（自动解析段落）
- 同步 Obsidian vault 到 MaxKB
- 与应用对话

## 安装

```bash
cd /Users/lizhun/Desktop/my_programs/maxkb-mcp
pip install -r requirements.txt
```

## 配置 Claude Code MCP

编辑 `~/.claude.json`，添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "maxkb": {
      "command": "python",
      "args": ["/Users/lizhun/Desktop/my_programs/maxkb-mcp/server.py"],
      "env": {
        "MAXKB_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

## 使用方法

### 1. 登录

```
使用 maxkb_login 工具登录
参数：
- username: admin
- password: Aadmin@123456
```

### 2. 同步 Obsidian vault

```
使用 maxkb_sync_obsidian 工具同步 vault
参数：
- vault_path: /Users/lizhun/Library/Mobile Documents/iCloud~md~obsidian/Documents/my obsidian vault
- knowledge_base_id: 可选，不指定则创建新知识库
```

### 3. 搜索知识库

```
使用 maxkb_search 工具搜索
参数：
- query: 搜索关键词
- knowledge_base_id: 知识库 ID（可选）
```

### 4. 列出知识库

```
使用 maxkb_list_knowledge_bases 工具
```

### 5. 列出文档

```
使用 maxkb_list_documents 工具
参数：
- knowledge_base_id: 知识库 ID
```

### 6. 上传单个文件

```
使用 maxkb_upload_markdown 工具
参数：
- knowledge_base_id: 知识库 ID
- file_path: /path/to/note.md
```

## 已有的知识库

你已经有以下知识库：

1. **李准的笔记** (ID: `019e0aad-c958-7e30-94aa-0a31cb7dc1a7`)
2. **电信质检知识库** (ID: `019dd9a0-9833-7e62-828b-3720cafafd89`)

## Obsidian 同步示例

```bash
# 同步整个 vault
使用 maxkb_sync_obsidian 工具
参数：
- vault_path: /Users/lizhun/Library/Mobile Documents/iCloud~md~obsidian/Documents/my obsidian vault
- knowledge_base_id: 019e0aad-c958-7e30-94aa-0a31cb7dc1a7
```

## API 端点

| 功能 | API 端点 |
|------|----------|
| 登录 | POST /admin/api/user/login |
| 知识库列表 | GET /admin/api/workspace/default/knowledge/1/100 |
| 创建知识库 | POST /admin/api/workspace/default/knowledge |
| 文档列表 | GET /admin/api/workspace/default/knowledge/{id}/document/1/100 |
| 解析文件 | POST /admin/api/workspace/default/knowledge/{id}/document/split |
| 创建文档 | POST /admin/api/workspace/default/knowledge/{id}/document |
| 搜索 | POST /admin/api/workspace/default/knowledge/{id}/hit_test |
| 应用列表 | GET /admin/api/workspace/default/application/1/100 |
| 应用对话 | POST /admin/api/application/{id}/chat/completions |

## 注意事项

1. 登录时可能需要验证码
2. 同步大量文件可能需要较长时间
3. Token 有效期有限，过期后需要重新登录
4. 文档上传后会自动进行向量化处理

## 相关链接

- [MaxKB 官方文档](https://maxkb.cn)
- [MaxKB GitHub](https://github.com/1Panel-dev/MaxKB)
