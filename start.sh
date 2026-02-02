#!/bin/bash

# AI赋能的网页自动化测试工具 - 启动脚本
# 用于启动所有后端服务和前端服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 服务配置
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Z.AI 配置（设置为默认）
export ZAI_API_KEY="897b1f45405c4d20a584f84fe2a233c4.7REpblMwoq2Uwe0B"
export ZAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# 其他配置
export OPENAI_API_KEY=""
export OLLAMA_BASE_URL="http://localhost:11434"
export DATABASE_URL="sqlite:///./test_cases.db"
export EXEC_DATABASE_URL="sqlite:///./test_exec.db"

# 服务路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend/ai-test-frontend"
BACKEND_API_GATEWAY_DIR="$SCRIPT_DIR/backend/api-gateway"
BACKEND_EXEC_SERVICE_DIR="$SCRIPT_DIR/backend/exec-service"

# PID文件目录
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# 日志管理函数
setup_logging() {
    local service_name=$1
    local log_file="$LOG_DIR/${service_name}.log"
    local current_date=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 创建带时间戳的日志文件名
    local timestamped_log="$LOG_DIR/${service_name}_$(date '+%Y%m%d_%H%M%S').log"
    
    # 如果日志文件过大（超过10MB），则轮转
    if [ -f "$log_file" ] && [ $(stat -c%s "$log_file" 2>/dev/null || echo 0) -gt 10485760 ]; then
        log_info "轮转 $service_name 日志文件 (大小超过10MB)"
        mv "$log_file" "$timestamped_log"
    fi
    
    echo "=== $service_name 启动日志 - $current_date ===" > "$log_file"
    echo "工作目录: $(pwd)" >> "$log_file"
    echo "启动命令: $2" >> "$log_file"
    echo "=========================================" >> "$log_file"
    echo "" >> "$log_file"
}

# 清理旧日志文件
cleanup_old_logs() {
    local service_name=$1
    local keep_days=7
    
    log_info "清理 $service_name 旧日志文件 (保留最近$keep_days天)"
    
    # 删除7天前的日志文件
    find "$LOG_DIR" -name "${service_name}_*.log" -mtime +$keep_days -delete 2>/dev/null || true
    
    # 只保留最新的日志文件
    ls -t "$LOG_DIR/${service_name}"*.log 2>/dev/null | tail -n +10 | xargs -r rm 2>/dev/null || true
}

# 服务列表
SERVICES=(
    "case-service:8001"
    "ai-service:8003"
    "exec-service:3001"
    "api-gateway:3000"
    "frontend:5173"
)

# 清理端口占用的函数
clear_port_usage() {
    local port=$1
    log_info "检查端口 $port 是否被占用..."
    
    # 查找占用端口的进程
    local port_processes=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}')
    if [ -n "$port_processes" ]; then
        log_warning "端口 $port 被占用: $port_processes"
        
        # 提取进程PID
        local pids=$(echo "$port_processes" | sed 's/.*pid=\([^,]*\).*/\1/' | sed 's/.*node\["\([^"]*\)\"].*/\1/')
        for pid in $pids; do
            if [ -n "$pid" ] && [ "$pid" != "0" ]; then
                log_info "杀死占用端口 $port 的进程 $pid"
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi
        done
        
        # 再次检查端口是否释放
        local port_processes_after=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}')
        if [ -n "$port_processes_after" ]; then
            log_error "无法释放端口 $port，请手动检查: $port_processes_after"
            return 1
        else
            log_success "端口 $port 已释放"
        fi
    else
        log_info "端口 $port 可用"
    fi
    return 0
}

# 检查Node.js版本
check_nodejs() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        log_info "正在安装 Node.js..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install 22
    fi
    
    NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        log_warning "Node.js 版本较低，建议使用 Node.js 20+"
    fi
}

# 检查Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "检查并安装 Python 依赖..."
    
    cd "$BACKEND_DIR/case-service"
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安装 Case Service 依赖..."
        pip3 install fastapi uvicorn sqlalchemy pydantic httpx
    fi
    
    cd "$BACKEND_DIR/ai-service"
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安装 AI Service 依赖..."
        pip3 install fastapi uvicorn sqlalchemy pydantic httpx openai
    fi
}

# 安装Node.js依赖
install_nodejs_deps() {
    log_info "检查并安装 Node.js 依赖..."
    
    cd "$BACKEND_API_GATEWAY_DIR"
    if [ ! -d "node_modules" ]; then
        log_info "安装 API Gateway 依赖..."
        npm install
    fi
    
    cd "$BACKEND_EXEC_SERVICE_DIR"
    if [ ! -d "node_modules" ]; then
        log_info "安装 Exec Service 依赖..."
        npm install
    fi
    
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        log_info "安装 Frontend 依赖..."
        npm install
    fi
}

# 启动服务
start_service() {
    local service_name=$1
    local service_port=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"
    # 强制绑定到所有接口，以便从Windows访问
    local host_address="0.0.0.0"
    
    # 检查服务是否已在运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warning "$service_name (端口 $service_port) 已在运行 (PID: $pid)"
            return 0
        else
            log_info "$service_name 进程不存在，清理PID文件"
            rm -f "$pid_file"
        fi
    fi
    
    # 清理端口占用
    log_info "检查并清理端口 $service_port..."
    if ! clear_port_usage "$service_port"; then
        log_error "无法启动 $service_name - 端口 $service_port 被占用"
        return 1
    fi
    
    log_info "启动 $service_name..."
    
    case "$service_name" in
        "case-service")
            cd "$BACKEND_DIR/case-service"
            setup_logging "$service_name" "python3 main.py --host 0.0.0.0 --port 8001"
            nohup python3 main.py --host 0.0.0.0 --port 8001 >> "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        "ai-service")
            cd "$BACKEND_DIR/ai-service"
            setup_logging "$service_name" "python3 main.py --host 0.0.0.0 --port 8003"
            nohup python3 main.py --host 0.0.0.0 --port 8003 >> "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        "exec-service")
            cd "$BACKEND_EXEC_SERVICE_DIR"
            setup_logging "$service_name" "node src/index.js --host 0.0.0.0 --port 3001"
            nohup node src/index.js --host 0.0.0.0 --port 3001 >> "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        "api-gateway")
            cd "$BACKEND_API_GATEWAY_DIR"
            setup_logging "$service_name" "node src/index.js --host 0.0.0.0 --port 3000"
            nohup node src/index.js --host 0.0.0.0 --port 3000 >> "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        "frontend")
            cd "$FRONTEND_DIR"
            setup_logging "$service_name" "npm run dev -- --host 0.0.0.0 --port 5173"
            nohup npm run dev -- --host 0.0.0.0 --port 5173 >> "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        *)
            log_error "未知的服务: $service_name"
            return 1
            ;;
    esac
    
    # 清理旧日志文件
    cleanup_old_logs "$service_name"
    
    # 等待服务启动
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$service_port/health" > /dev/null 2>&1; then
            log_success "$service_name 启动成功 (端口: $service_port)"
            log_info "日志文件: $log_file"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    # 对于前端服务，增加额外的等待时间
    if [ "$service_name" = "frontend" ]; then
        log_info "前端服务正在编译，增加额外等待时间..."
        local extra_attempts=30
        local extra_attempt=1
        while [ $extra_attempt -le $extra_attempts ]; do
            if curl -s "http://localhost:$service_port/health" > /dev/null 2>&1; then
                log_success "$service_name 启动成功 (端口: $service_port)"
                log_info "日志文件: $log_file"
                return 0
            fi
            sleep 1
            extra_attempt=$((extra_attempt + 1))
        done
    fi
    
    log_error "$service_name 启动超时"
    log_info "检查日志文件: $log_file"
    return 1
}

# 启动所有服务
start_all_services() {
    log_info "=== 启动 AI 测试工具 ==="
    log_info "当前工作目录: $SCRIPT_DIR"
    
    # 检查环境
    log_info "检查运行环境..."
    check_nodejs
    check_python
    log_success "环境检查完成"
    
    # 安装依赖
    log_info "安装依赖包..."
    install_python_deps
    install_nodejs_deps
    log_success "依赖安装完成"
    
    # 启动后端服务
    log_info "启动后端服务..."
    
    # 启动 Case Service
    start_service "case-service" "8001"
    sleep 2
    
    # 启动 AI Service
    start_service "ai-service" "8003"
    sleep 2
    
    # 启动 Exec Service
    start_service "exec-service" "3001"
    sleep 2
    
    # 启动 API Gateway
    start_service "api-gateway" "3000"
    sleep 3
    
    # 启动前端服务
    log_info "启动前端服务..."
    start_service "frontend" "5173"
    
    # 前端服务需要更长的启动时间
    sleep 10

    # 启动完成后检查所有服务状态
    check_all_services
}

# 显示服务状态
check_all_services() {
    log_info "=== 服务状态检查 ==="
    
    check_service_status "frontend" "5173"
    check_service_status "api-gateway" "3000"
    check_service_status "exec-service" "3001"
    check_service_status "ai-service" "8003"
    check_service_status "case-service" "8001"
    
    echo ""
    log_info "=== Windows浏览器访问地址 ==="
    # 获取WSL IP地址
    local wsl_ip=$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    if [ -n "$wsl_ip" ]; then
        log_info "前端地址: http://localhost:5173 或 http://$wsl_ip:5173"
        log_info "API网关: http://localhost:3000 或 http://$wsl_ip:3000"
    else
        log_info "前端地址: http://localhost:5173"
        log_info "API网关: http://localhost:3000"
    fi
    log_info ""
    log_info "请在Windows浏览器中访问上述地址"
}

# 检查服务状态
check_service_status() {
    local service_name=$1
    local service_port=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            if ss -tlnp 2>/dev/null | grep -q ":$service_port "; then
                echo -e "  ${service_name}: \033[0;32m运行中\033[0m (PID: $pid, 端口: $service_port)"
                echo -e "    访问地址: http://localhost:$service_port 或 http://$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1):$service_port"
            else
                echo -e "  ${service_name}: \033[0;33m进程存在但未监听端口\033[0m (PID: $pid, 端口: $service_port)"
            fi
        else
            echo -e "  ${service_name}: \033[0;31m进程不存在\033[0m (PID文件存在)"
        fi
    else
        if ss -tlnp 2>/dev/null | grep -q ":$service_port "; then
            echo -e "  ${service_name}: \033[0;33m端口被占用但无PID文件\033[0m (端口: $service_port)"
        else
            echo -e "  ${service_name}: \033[0;31m未运行\033[0m"
        fi
    fi
}

# 检查所有服务状态
check_all_services() {
    log_info "=== 服务状态检查 ==="
    
    check_service_status "frontend" "5173"
    check_service_status "api-gateway" "3000"
    check_service_status "exec-service" "3001"
    check_service_status "ai-service" "8003"
    check_service_status "case-service" "8001"
    
    echo ""
    log_info "=== Windows浏览器访问地址 ==="
    # 获取WSL IP地址
    local wsl_ip=$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    if [ -n "$wsl_ip" ]; then
        log_info "前端地址: http://localhost:5173 或 http://$wsl_ip:5173"
        log_info "API网关: http://localhost:3000 或 http://$wsl_ip:3000"
    else
        log_info "前端地址: http://localhost:5173"
        log_info "API网关: http://localhost:3000"
    fi
    log_info ""
    log_info "请在Windows浏览器中访问上述地址"
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            start_all_services
            ;;
        "help"|"-h"|"--help")
            echo "AI 测试工具启动脚本"
            echo ""
            echo "用法: $0 [COMMAND]"
            echo ""
            echo "命令:"
            echo "  start     启动所有服务 (默认)"
            echo "  help      显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0     # 启动所有服务"
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"