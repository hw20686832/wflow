#!/bin/bash

set -e

echo "=========================================="
echo "  WFlow 更新脚本"
echo "=========================================="
echo ""

# 备份当前数据
echo "执行备份..."
./backup.sh

if [ $? -ne 0 ]; then
    echo "备份失败，取消更新"
    exit 1
fi

echo "✓ 备份完成"
echo ""

# 拉取最新代码
echo "拉取最新代码..."
git pull

if [ $? -ne 0 ]; then
    echo "代码拉取失败，取消更新"
    exit 1
fi

echo "✓ 代码更新完成"
echo ""

# 停止服务
echo "停止当前服务..."
docker-compose down

echo "✓ 服务已停止"
echo ""

# 重新构建和启动
echo "重新构建和启动服务..."
docker-compose up -d --build

echo "✓ 服务已更新"
echo ""

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "  更新完成!"
echo "=========================================="
echo ""

# 执行数据库迁移（如果需要）
echo "检查数据库更新..."
docker-compose exec backend python3 database/db_manager.py --test

if [ $? -eq 0 ]; then
    echo "✓ 数据库连接正常"
else
    echo "⚠️  数据库连接异常，请检查"
fi

echo ""
echo "访问地址:"
echo "  前端: http://localhost:80"
echo "  后端: http://localhost:8888"
echo ""
echo "如遇问题，可以使用以下命令回滚:"
echo "  docker-compose down"
echo "  git checkout <previous-commit>"
echo "  ./deploy.sh"
