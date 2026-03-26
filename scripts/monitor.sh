#!/bin/bash

echo "=========================================="
echo "  WFlow 服务监控"
echo "=========================================="
echo ""

echo "容器状态:"
docker-compose ps
echo ""

echo "=========================================="
echo "资源使用情况:"
echo "=========================================="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
echo ""

echo "=========================================="
echo "最近日志 (后端):"
echo "=========================================="
docker-compose logs --tail=20 backend
echo ""

echo "=========================================="
echo "健康检查:"
echo "=========================================="

# 检查MySQL
if docker-compose exec -T mysql mysqladmin ping -h localhost &> /dev/null; then
    echo "✓ MySQL: 运行正常"
else
    echo "✗ MySQL: 连接失败"
fi

# 检查Redis
if docker-compose exec -T redis redis-cli ping &> /dev/null; then
    echo "✓ Redis: 运行正常"
else
    echo "✗ Redis: 连接失败"
fi

# 检查后端
if curl -sf http://localhost:8888/api/health &> /dev/null; then
    echo "✓ Backend: 运行正常"
else
    echo "✗ Backend: 连接失败"
fi

# 检查前端
if curl -sf http://localhost:80 &> /dev/null; then
    echo "✓ Frontend: 运行正常"
else
    echo "✗ Frontend: 连接失败"
fi

echo ""
echo "=========================================="
echo "磁盘使用情况:"
echo "=========================================="
df -h | grep -E "Filesystem|/dev/"
echo ""

echo "=========================================="
echo "Docker卷使用情况:"
echo "=========================================="
docker system df -v | grep -E "VOLUME NAME|wflow"
