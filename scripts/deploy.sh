#!/bin/bash

set -e

echo "=========================================="
echo "  WFlow Docker 部署脚本"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker 已安装: $(docker --version)"
echo "✓ Docker Compose 已安装: $(docker-compose --version)"
echo ""

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "✓ .env 文件已创建"
    echo ""
    echo "⚠️  请编辑 .env 文件，设置安全的密码和密钥"
    echo "   重要: 请修改以下配置项:"
    echo "   - MYSQL_ROOT_PASSWORD"
    echo "   - MYSQL_PASSWORD"
    echo "   - SESSION_SECRET_KEY"
    echo ""
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p var/log
mkdir -p conf/workflows
mkdir -p docker
echo "✓ 目录创建完成"
echo ""

# 复制生产配置文件
if [ ! -f "conf/database.prod.conf" ]; then
    echo "警告: 生产配置文件不存在"
    echo "将使用默认配置"
fi

echo "开始构建和启动服务..."
docker-compose up -d --build

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "服务状态:"
docker-compose ps
echo ""
echo "访问地址:"
echo "  前端: http://localhost:80"
echo "  后端: http://localhost:8888"
echo ""
echo "默认管理员账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""
echo "首次部署后，请执行数据库初始化:"
echo "  docker-compose exec backend python3 database/db_manager.py --init"
echo ""
