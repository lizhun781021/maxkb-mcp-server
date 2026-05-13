#!/bin/bash

# MaxKB MCP Server 配置脚本

echo "=== MaxKB MCP Server 配置 ==="
echo ""

# 检查 Python
echo "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查 pip
echo "检查 pip 环境..."
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到 pip3，请先安装 pip3"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo ""
echo "=== 依赖安装完成 ==="
echo ""

# 提示用户配置
echo "请按照以下步骤配置："
echo ""
echo "1. 获取 MaxKB API Token："
echo "   - 打开 http://localhost:8080"
echo "   - 登录管理员账号（默认：admin / MaxKB@123..）"
echo "   - 进入"系统设置" -> "API Token""
echo "   - 创建一个新的 API Token"
echo ""
echo "2. 配置 Claude Code MCP："
echo "   编辑 ~/.claude.json，在 mcpServers 中添加："
echo ""
echo '   "maxkb": {'
echo '     "command": "python",'
echo '     "args": ["/Users/lizhun/Desktop/my_programs/maxkb-mcp/server.py"],'
echo '     "env": {'
echo '       "MAXKB_BASE_URL": "http://localhost:8080",'
echo '       "MAXKB_API_TOKEN": "your_api_token_here"'
echo '     }'
echo '   }'
echo ""
echo "3. 重启 Claude Code 使配置生效"
echo ""
echo "=== 配置完成 ==="
