#!/bin/bash

echo "=========================================="
echo "  WFlow Web System Quick Start Script"
echo "=========================================="

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# 检查Node.js版本
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

echo "✓ Node.js found: $(node --version)"

# 检查MySQL
if ! command -v mysql &> /dev/null; then
    echo "Warning: MySQL is not installed"
    echo "Please install MySQL 8.0+ before continuing"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ MySQL found: $(mysql --version)"
fi

# 检查Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Warning: Redis is not installed (optional)"
else
    echo "✓ Redis found: $(redis-cli --version)"
fi

echo ""
echo "Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo "✓ Python dependencies installed"
echo ""

echo "Step 2: Installing Node.js dependencies..."
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node.js dependencies"
    exit 1
fi

echo "✓ Node.js dependencies installed"
cd ..
echo ""

echo "Step 3: Checking database configuration..."
if [ ! -f "conf/database.conf" ]; then
    echo "Error: Database configuration file not found"
    echo "Please create conf/database.conf with your database settings"
    exit 1
fi

echo "✓ Database configuration file found"
echo ""

echo "Step 4: Testing database connection..."
python3 database/db_manager.py --test

if [ $? -ne 0 ]; then
    echo "Warning: Database connection test failed"
    echo "Please check your database configuration in conf/database.conf"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Database connection successful"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To start the system:"
echo ""
echo "1. Start the backend server:"
echo "   python3 web/app.py"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run serve"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:8080"
echo "   Backend:  http://localhost:8888"
echo ""
echo "Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "For production deployment, please refer to DEPLOYMENT.md"
echo ""
