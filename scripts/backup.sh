#!/bin/bash

BACKUP_DIR="/backup/wflow"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

echo "开始备份数据..."

# 备份MySQL数据库
echo "备份数据库..."
docker-compose exec -T mysql mysqldump -u wflow_user -pwflow_password wflow_db > $BACKUP_DIR/wflow_db_$DATE.sql

if [ $? -eq 0 ]; then
    echo "✓ 数据库备份完成: $BACKUP_DIR/wflow_db_$DATE.sql"
else
    echo "✗ 数据库备份失败"
    exit 1
fi

# 备份配置文件
echo "备份配置文件..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz conf/

if [ $? -eq 0 ]; then
    echo "✓ 配置文件备份完成: $BACKUP_DIR/config_$DATE.tar.gz"
else
    echo "✗ 配置文件备份失败"
    exit 1
fi

# 备份工作流数据
echo "备份工作流数据..."
docker run --rm -v wflow_workflow_data:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/workflow_$DATE.tar.gz -C /data .

if [ $? -eq 0 ]; then
    echo "✓ 工作流数据备份完成: $BACKUP_DIR/workflow_$DATE.tar.gz"
else
    echo "✗ 工作流数据备份失败"
    exit 1
fi

# 清理7天前的备份
echo "清理旧备份..."
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✓ 旧备份清理完成"
echo ""
echo "备份完成! 备份文件保存在: $BACKUP_DIR"
