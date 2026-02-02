#!/bin/bash

# AI赋能的网页自动化测试工具 - 服务状态检查脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# PID文件目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
mkdir -p "$PID_DIR"

# 服务信息
SERVICES=(
    "case-service:8001:Case Service"
    "ai-service:8003:AI Service"
    "exec-service:3001:Exec Service"
    "api-gateway:3000:API Gateway"
    "frontend:5173:Frontend"
)

# 检查单个服务
check_service() {
    local service_info=$1
    local service_name=$(echo "$service_info" | cut -d':' -f1)
    local service_port=$(echo "$service_info" | cut -d':' -f2)
    local service_display=$(echo "$service_info" | cut -d':' -f3)
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo -e "${CYAN}检查 $service_display...${NC}"
    
    # 检查PID文件
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        # 检查进程是否存在
        if ps -p "$pid" > /dev/null 2>&1; then
            # 检查端口是否监听
            if netstat -tuln 2>/dev/null | grep -q ":$service_port "; then
                # 检查服务健康状态
                if curl -s "http://localhost:$service_port/health" > /dev/null 2>&1; then
                    echo -e "  状态: ${GREEN}● 正常运行${NC}"
                    echo -e "  PID: $pid"
                    echo -e "  端口: $service_port"
                    echo -e "  健康检查: ${GREEN}✓ 通过${NC}"
                    
                    # 显示最近的日志
                    if [ -f "$PID_DIR/${service_name}.log" ]; then
                        echo -e "  最近日志:"
                        tail -3 "$PID_DIR/${service_name}.log" | sed 's/^/    /'
                    fi
                else
                    echo -e "  状态: ${YELLOW}● 运行中但异常${NC}"
                    echo -e "  PID: $pid"
                    echo -e "  端口: $service_port"
                    echo -e "  健康检查: ${RED}✗ 失败${NC}"
                fi
            else
                echo -e "  状态: ${RED}✗ 进程存在但未监听端口${NC}"
                echo -e "  PID: $pid"
                echo -e "  端口: $service_port (未监听)"
            fi
        else
            echo -e "  状态: ${RED}✗ 进程不存在${NC}"
            echo -e "  PID: $pid (僵尸进程)"
            echo -e "  建议: 清理PID文件并重启服务"
        fi
    else
        echo -e "  状态: ${RED}✗ 未运行${NC}"
        echo -e "  PID文件: 不存在"
        echo -e "  建议: 使用 './start.sh' 启动服务"
    fi
    
    echo ""
}

# 检查系统资源
check_system_resources() {
    echo -e "${CYAN}=== 系统资源检查 ===${NC}"
    
    # CPU使用率
    if command -v top &> /dev/null; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        echo -e "CPU 使用率: ${cpu_usage}%"
    fi
    
    # 内存使用率
    if command -v free &> /dev/null; then
        local mem_info=$(free -m | awk 'NR==2{printf "%.2f%% (%sMB/%sMB)", $3*100/$2, $3, $2}')
        echo -e "内存使用: $mem_info"
    fi
    
    # 磁盘使用率
    if command -v df &> /dev/null; then
        local disk_usage=$(df -h . | awk 'NR==2{print $5}')
        echo -e "磁盘使用: $disk_usage"
    fi
    
    echo ""
}

# 检查网络连接
check_network_connectivity() {
    echo -e "${CYAN}=== 网络连接检查 ===${NC}"
    
    # 检查关键端口
    local ports=("8001" "8003" "3001" "3000" "5173")
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "端口 $port: ${GREEN}● 监听中${NC}"
        else
            echo -e "端口 $port: ${RED}✗ 未监听${NC}"
        fi
    done
    
    echo ""
}

# 检查依赖
check_dependencies() {
    echo -e "${CYAN}=== 依赖检查 ===${NC}"
    
    # Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version 2>/dev/null || echo "未知")
        echo -e "Node.js: ${GREEN}✓ 安装${NC} (版本: $node_version)"
    else
        echo -e "Node.js: ${RED}✗ 未安装${NC}"
    fi
    
    # Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>/dev/null || echo "未知")
        echo -e "Python: ${GREEN}✓ 安装${NC} (版本: $python_version)"
    else
        echo -e "Python: ${RED}✗ 未安装${NC}"
    fi
    
    # npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version 2>/dev/null || echo "未知")
        echo -e "npm: ${GREEN}✓ 安装${NC} (版本: $npm_version)"
    else
        echo -e "npm: ${RED}✗ 未安装${NC}"
    fi
    
    echo ""
}

# 显示服务访问地址
show_access_urls() {
    echo -e "${CYAN}=== 服务访问地址 ===${NC}"
    echo -e "前端管理界面: ${GREEN}http://localhost:5173${NC}"
    echo -e "API网关: ${GREEN}http://localhost:3000${NC}"
    echo -e "Case Service: ${GREEN}http://localhost:8001${NC}"
    echo -e "AI Service: ${GREEN}http://localhost:8003${NC}"
    echo -e "Exec Service: ${GREEN}http://localhost:3001${NC}"
    echo ""
}

# 显示操作建议
show_suggestions() {
    echo -e "${CYAN}=== 操作建议 ===${NC}"
    
    local running_count=0
    local total_count=${#SERVICES[@]}
    
    for service_info in "${SERVICES[@]}"; do
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        local pid_file="$PID_DIR/${service_name}.pid"
        
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                running_count=$((running_count + 1))
            fi
        fi
    done
    
    echo "当前运行状态: $running_count/$total_count 服务正在运行"
    
    if [ $running_count -eq 0 ]; then
        echo -e "建议: ${GREEN}使用 './start.sh' 启动所有服务${NC}"
    elif [ $running_count -lt $total_count ]; then
        echo -e "建议: ${YELLOW}使用 './start.sh' 启动剩余服务${NC}"
    else
        echo -e "建议: ${GREEN}所有服务正常运行${NC}"
        echo -e "提示: 使用 './stop.sh stop' 停止服务"
    fi
    
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo -e "${CYAN}AI 测试工具 - 服务状态检查${NC}"
    echo "========================================"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 检查系统资源
    check_system_resources
    
    # 检查网络连接
    check_network_connectivity
    
    # 检查各个服务
    echo -e "${CYAN}=== 服务状态检查 ===${NC}"
    for service_info in "${SERVICES[@]}"; do
        check_service "$service_info"
    done
    
    # 显示访问地址
    show_access_urls
    
    # 显示建议
    show_suggestions
    
    echo -e "${CYAN}检查完成于: $(date)${NC}"
}

# 执行主函数
main "$@"