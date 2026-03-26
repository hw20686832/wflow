#!/bin/bash

echo "=========================================="
echo "  WFlow 目录结构整理脚本"
echo "=========================================="
echo ""

# 创建新的目录结构
echo "创建新的目录结构..."
mkdir -p config
mkdir -p scripts
mkdir -p docs
mkdir -p tests
mkdir -p var/log
mkdir -p var/uploads
mkdir -p var/workflows
mkdir -p docker

echo "✓ 目录结构创建完成"
echo ""

# 移动配置文件
echo "整理配置文件..."
if [ -f "conf/common.conf" ]; then
    echo "  - common.conf (已弃用，请使用config/settings.yml)"
fi

if [ -f "conf/database.conf" ]; then
    echo "  - database.conf (已弃用，请使用config/settings.yml)"
fi

if [ -f "conf/database.prod.conf" ]; then
    echo "  - database.prod.conf (已弃用，请使用config/settings.prod.yml)"
fi

if [ -f "conf/redis.conf" ]; then
    echo "  - redis.conf (已弃用，请使用config/settings.yml)"
fi

echo "✓ 配置文件整理完成"
echo ""

# 移动脚本文件
echo "整理脚本文件..."
if [ -f "deploy.sh" ]; then
    mv deploy.sh scripts/
    echo "  - deploy.sh -> scripts/"
fi

if [ -f "stop.sh" ]; then
    mv stop.sh scripts/
    echo "  - stop.sh -> scripts/"
fi

if [ -f "backup.sh" ]; then
    mv backup.sh scripts/
    echo "  - backup.sh -> scripts/"
fi

if [ -f "monitor.sh" ]; then
    mv monitor.sh scripts/
    echo "  - monitor.sh -> scripts/"
fi

if [ -f "update.sh" ]; then
    mv update.sh scripts/
    echo "  - update.sh -> scripts/"
fi

if [ -f "setup.sh" ]; then
    mv setup.sh scripts/
    echo "  - setup.sh -> scripts/"
fi

echo "✓ 脚本文件整理完成"
echo ""

# 移动文档文件
echo "整理文档文件..."
if [ -f "DEPLOYMENT.md" ]; then
    mv DEPLOYMENT.md docs/
    echo "  - DEPLOYMENT.md -> docs/"
fi

if [ -f "WEB_README.md" ]; then
    mv WEB_README.md docs/
    echo "  - WEB_README.md -> docs/"
fi

if [ -f "ARCHITECTURE.md" ]; then
    mv ARCHITECTURE.md docs/
    echo "  - ARCHITECTURE.md -> docs/"
fi

if [ -f "REDIS_STATE_GUIDE.md" ]; then
    mv REDIS_STATE_GUIDE.md docs/
    echo "  - REDIS_STATE_GUIDE.md -> docs/"
fi

if [ -f "NEW_FEATURES.md" ]; then
    mv NEW_FEATURES.md docs/
    echo "  - NEW_FEATURES.md -> docs/"
fi

if [ -f "DOCKER_DEPLOYMENT.md" ]; then
    mv DOCKER_DEPLOYMENT.md docs/
    echo "  - DOCKER_DEPLOYMENT.md -> docs/"
fi

if [ -f "DOCKER_QUICKSTART.md" ]; then
    mv DOCKER_QUICKSTART.md docs/
    echo "  - DOCKER_QUICKSTART.md -> docs/"
fi

echo "✓ 文档文件整理完成"
echo ""

# 移动Docker配置文件
echo "整理Docker配置文件..."
if [ -f "docker/nginx.conf" ]; then
    echo "  - docker/nginx.conf (已存在)"
fi

if [ -f "docker/mysql.cnf" ]; then
    echo "  - docker/mysql.cnf (已存在)"
fi

if [ -f "docker/redis.conf" ]; then
    echo "  - docker/redis.conf (已存在)"
fi

echo "✓ Docker配置文件整理完成"
echo ""

# 移动测试文件
echo "整理测试文件..."
if [ -f "test_redis_state.py" ]; then
    mv test_redis_state.py tests/
    echo "  - test_redis_state.py -> tests/"
fi

if [ -f "test_new_features.py" ]; then
    mv test_new_features.py tests/
    echo "  - test_new_features.py -> tests/"
fi

if [ -f "query_state.py" ]; then
    mv query_state.py scripts/
    echo "  - query_state.py -> scripts/"
fi

echo "✓ 测试文件整理完成"
echo ""

# 设置脚本执行权限
echo "设置脚本执行权限..."
chmod +x scripts/*.sh
echo "✓ 脚本执行权限设置完成"
echo ""

echo "=========================================="
echo "  目录结构整理完成!"
echo "=========================================="
echo ""
echo "新的目录结构:"
echo "  config/          - 配置文件"
echo "  scripts/         - 运维脚本"
echo "  docs/            - 文档文件"
echo "  tests/           - 测试文件"
echo "  docker/          - Docker配置"
echo "  web/             - Web后端"
echo "  frontend/        - 前端应用"
echo "  database/        - 数据库相关"
echo "  lib/             - 工具库"
echo "  var/             - 运行时数据"
echo ""
echo "注意:"
echo "  - 旧的配置文件已弃用，请使用config/settings.yml"
echo "  - 脚本文件已移动到scripts/目录"
echo "  - 文档文件已移动到docs/目录"
echo "  - 测试文件已移动到tests/目录"
echo ""
echo "下一步:"
echo "  1. 更新代码以使用新的配置系统"
echo "  2. 更新Docker Compose文件以使用新的目录结构"
echo "  3. 更新文档以反映新的目录结构"
