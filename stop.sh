#!/bin/bash

# AI赋能的网页自动化测试工具 - 停止脚本
# 用于停止所有运行的服务

set -e

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

# 目录定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# 清理僵尸进程和端口占用的函数
cleanup_zombie_and_port_processes() {
    log_info "清理僵尸进程和端口占用..."
    
    # 清理僵尸进程
    local zombie_pids=$(ps aux | grep defunct | grep -v grep | awk '{print $2}')
    if [ -n "$zombie_pids" ]; then
        log_info "发现僵尸进程: $zombie_pids"
        for pid in $zombie_pids; do
            # 查找僵尸进程的父进程并杀死
            local parent_pid=$(ps -o ppid= -p "$pid" | tr -d ' ')
            if [ -n "$parent_pid" ] && [ "$parent_pid" != "1" ]; then
                log_info "杀死僵尸进程 $pid 的父进程 $parent_pid"
                kill -9 "$parent_pid" 2>/dev/null || true
            fi
        done
    fi
    
    # 清理服务端口占用
    local service_ports=("5173" "3000" "3001" "8001" "8003")
    for port in "${service_ports[@]}"; do
        local port_processes=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}')
        if [ -n "$port_processes" ]; then
            log_info "清理端口 $port 的占用进程: $port_processes"
            # 提取进程PID
            local pids=$(echo "$port_processes" | sed 's/.*pid=\([^,]*\).*/\1/' | sed 's/.*node\["\([^"]*\)\].*/\1/')
            for pid in $pids; do
                if [ -n "$pid" ] && [ "$pid" != "0" ]; then
                    log_info "杀死端口 $port 的进程 $pid"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            done
        fi
    done
    
    log_success "僵尸进程和端口占用清理完成"
}

# 服务列表
SERVICES=(
    "frontend:5173"
    "api-gateway:3000"
    "exec-service:3001"
    "ai-service:8003"
    "case-service:8001"
)

# 停止单个服务
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"
    
    if [ ! -f "$pid_file" ]; then
        log_warning "$service_name PID文件不存在，可能未运行"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        log_warning "$service_name 进程不存在 (PID: $pid)"
        rm -f "$pid_file"
        return 0
    fi
    
    log_info "停止 $service_name (PID: $pid)..."
    
    # 优雅停止
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local max_attempts=10
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            log_success "$service_name 已停止"
            rm -f "$pid_file"
            
            # 添加停止日志记录
            local stop_time=$(date '+%Y-%m-%d %H:%M:%S')
            echo "=== $service_name 停止时间 - $stop_time ===" >> "$log_file"
            echo "服务状态: 已停止" >> "$log_file"
            echo "=========================================" >> "$log_file"
            echo "" >> "$log_file"
            
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    # 强制停止
    log_warning "$service_name 未响应，强制停止..."
    kill -KILL "$pid" 2>/dev/null || true
    sleep 2
    
    if ps -p "$pid" > /dev/null 2>&1; then
        log_error "无法停止 $service_name (PID: $pid)"
    else
        log_success "$service_name 已强制停止"
        rm -f "$pid_file"
        
        # 添加强制停止日志记录
        local stop_time=$(date '+%Y-%m-%d %H:%M:%S')
        echo "=== $service_name 强制停止时间 - $stop_time ===" >> "$log_file"
        echo "服务状态: 已强制停止" >> "$log_file"
        echo "=========================================" >> "$log_file"
        echo "" >> "$log_file"
    fi
}

# 停止所有服务
stop_all_services() {
    log_info "=== 停止 AI 测试工具服务 ==="
    
    # 清理僵尸进程和端口占用
    cleanup_zombie_and_port_processes
    
    # 反向遍历服务列表（先停止前端，后停止后端）
    for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
        local service_info="${SERVICES[$i]}"
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        stop_service "$service_name"
        sleep 1
    done
    
    # 再次清理端口占用
    cleanup_zombie_and_port_processes
    
    # 清理日志文件（可选）
    read -p "是否删除日志文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理日志文件..."
        rm -f "$PID_DIR"/*.log
        log_success "日志文件已清理"
    fi
    
    log_success "=== 所有服务已停止 ==="
}

# 清理所有
clean_all() {
    log_info "=== 清理 AI 测试工具 ==="
    
    # 停止所有服务
    stop_all_services
    
    # 清理PID文件
    log_info "清理PID文件..."
    rm -rf "$PID_DIR"/*.pid
    
    # 清理日志文件
    read -p "是否删除日志文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理日志文件..."
        rm -rf "$LOG_DIR"/*.log
        log_success "日志文件已清理"
    else
        log_info "保留日志文件，位置: $LOG_DIR"
    fi
    
    # 清理数据库文件
    read -p "是否删除数据库文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "删除数据库文件..."
        rm -f "$SCRIPT_DIR/backend/case-service/test_cases.db"
        rm -f "$SCRIPT_DIR/backend/exec-service/test_exec.db"
        log_success "数据库文件已删除"
    fi
    
    # 清理缓存
    read -p "是否清理缓存文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理缓存文件..."
        rm -rf "$SCRIPT_DIR/frontend/ai-test-frontend/node_modules/.cache"
        rm -rf "$SCRIPT_DIR/backend/*/node_modules/.cache"
        log_success "缓存文件已清理"
    fi
    
    log_success "=== 清理完成 ==="
}

# 显示日志
show_logs() {
    log_info "=== AI 测试工具日志文件 ==="
    
    for service_info in "${SERVICES[@]}"; do
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        local log_file="$LOG_DIR/${service_name}.log"
        
        if [ -f "$log_file" ]; then
            local log_size=$(du -h "$log_file" | cut -f1)
            local mod_time=$(stat -c "%y" "$log_file" 2>/dev/null | cut -d' ' -f1,2)
            echo -e "  ${service_name}: \033[0;32m存在\033[0m ($log_size, $mod_time)"
            echo "    位置: $log_file"
        else
            echo -e "  ${service_name}: \033[0;31m不存在\033[0m"
        fi
    done
    
    echo ""
    log_info "使用 './start.sh' 启动服务"
    log_info "使用 './stop.sh stop' 停止服务"
    log_info "使用 './stop.sh status' 查看服务状态"
}

# 显示帮助
show_help() {
    echo "AI 测试工具停止脚本"
    echo ""
    echo "用法: $0 [COMMAND]"
    echo ""
    echo "命令:"
    echo "  stop      停止所有服务 (默认)"
    echo "  clean     停止服务并清理所有文件"
    echo "  status    显示服务状态"
    echo "  logs      显示日志文件信息"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 stop     # 停止所有服务"
    echo "  $0 clean    # 停止服务并清理文件"
    echo "  $0 status   # 查看服务状态"
    echo "  $0 logs     # 查看日志文件"
}

# 检查服务状态
check_service_status() {
    local service_name=$1
    local service_port=$(echo "$service_info" | cut -d':' -f2)
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            if curl -s "http://localhost:$service_port/health" > /dev/null 2>&1; then
                echo -e "  ${service_name}: \033[0;32m运行中\033[0m (PID: $pid, 端口: $service_port)"
            else
                echo -e "  ${service_name}: \033[0;33m运行中但无响应\033[0m (PID: $pid, 端口: $service_port)"
            fi
        else
            echo -e "  ${service_name}: \033[0;31m进程不存在\033[0m (PID文件存在)"
        fi
    else
        echo -e "  ${service_name}: \033[0;31m未运行\033[0m"
    fi
}

# 显示所有服务状态
show_status() {
    echo "=== AI 测试工具服务状态 ==="
    
    for service_info in "${SERVICES[@]}"; do
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        check_service_status "$service_name"
    done
    
    echo ""
    echo "使用 './start.sh' 启动服务"
    echo "使用 './stop.sh stop' 停止服务"
}

# 主函数
main() {
    case "${1:-stop}" in
        "stop")
            stop_all_services
            ;;
        "clean")
            clean_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_help
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