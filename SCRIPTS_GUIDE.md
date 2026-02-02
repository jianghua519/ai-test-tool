# AI测试工具服务管理脚本使用说明

## 📋 概述

本项目提供了三个实用的服务管理脚本，用于简化AI赋能的网页自动化测试工具的部署和管理：

- `start.sh` - 启动所有服务
- `stop.sh` - 停止所有服务  
- `status.sh` - 查看服务状态

## 🚀 快速开始

### 1. 启动所有服务
```bash
./start.sh
```

### 2. 查看服务状态
```bash
./status.sh
```

### 3. 停止所有服务
```bash
./stop.sh
```

## 📖 详细使用说明

### 启动脚本 (start.sh)

**功能**: 启动AI测试工具的所有服务

**用法**:
```bash
./start.sh [COMMAND]
```

**参数**:
- `start` - 启动所有服务 (默认)
- `help` - 显示帮助信息

**特性**:
- ✅ 自动检查和安装依赖 (Node.js, Python, npm)
- ✅ 自动配置Z.AI GLM-4.5-AIR为默认AI模型
- ✅ 智能服务启动顺序 (后端→前端)
- ✅ 自动健康检查和故障恢复
- ✅ 彩色日志输出
- ✅ PID管理和日志记录

**启动的服务**:
1. **Case Service** (端口8001) - 测试用例管理
2. **AI Service** (端口8003) - AI模型服务 (默认: GLM-4.5-AIR)
3. **Exec Service** (端口3001) - 测试执行引擎
4. **API Gateway** (端口3000) - 统一API网关
5. **Frontend** (端口5173) - 前端管理界面

### 停止脚本 (stop.sh)

**功能**: 停止所有正在运行的服务

**用法**:
```bash
./stop.sh [COMMAND]
```

**参数**:
- `stop` - 停止所有服务 (默认)
- `clean` - 停止服务并清理所有文件
- `status` - 显示服务状态
- `help` - 显示帮助信息

**选项**:
- **stop**: 优雅停止所有服务
- **clean**: 停止服务 + 清理日志 + 清理数据库 + 清理缓存
- **status**: 显示详细的服务状态

### 状态检查脚本 (status.sh)

**功能**: 全面检查系统和服务状态

**用法**:
```bash
./status.sh
```

**检查内容**:
- ✅ 服务运行状态和PID
- ✅ 端口监听状态
- ✅ 健康检查状态
- ✅ 系统资源使用情况
- ✅ 网络连接状态
- ✅ 依赖软件版本检查
- ✅ 服务访问地址
- ✅ 操作建议

## ⚙️ 配置说明

### Z.AI GLM-4.5-AIR 配置

脚本已默认配置Z.AI的GLM-4.5-AIR模型：

```bash
# 自动设置的默认值
export ZAI_API_KEY="897b1f45405c4d20a584f84fe2a233c4.7REpblMwoq2Uwe0B"
export ZAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
```

**修改配置**:
如需更换API密钥，编辑 `start.sh` 文件中的相关变量：

```bash
# 在 start.sh 文件中修改
export ZAI_API_KEY="your_new_api_key_here"
```

### 服务路径配置

脚本会自动检测以下路径：
- `./backend/case-service` - 用例服务
- `./backend/ai-service` - AI服务  
- `./backend/exec-service` - 执行服务
- `./backend/api-gateway` - API网关
- `./frontend/ai-test-frontend` - 前端应用

## 🎯 服务访问地址

启动成功后，可以通过以下地址访问服务：

| 服务 | 地址 | 描述 |
|------|------|------|
| 前端管理界面 | http://localhost:5173 | 主要用户界面 |
| API网关 | http://localhost:3000 | 统一API入口 |
| Case Service | http://localhost:8001 | 测试用例管理 |
| AI Service | http://localhost:8003 | AI模型服务 |
| Exec Service | http://localhost:3001 | 测试执行引擎 |

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :端口号
   
   # 强制停止进程
   kill -9 进程ID
   ```

2. **依赖安装失败**
   ```bash
   # 手动安装Node.js
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   
   # 手动安装Python依赖
   pip3 install fastapi uvicorn sqlalchemy pydantic httpx openai
   ```

3. **服务启动失败**
   ```bash
   # 查看日志
   tail -f ./pids/服务名.log
   
   # 检查PID文件
   ls -la ./pids/
   ```

4. **前端访问失败**
   ```bash
   # 检查Vite进程
   ps aux | grep vite
   
   # 重新启动前端
   cd frontend/ai-test-frontend
   npm run dev
   ```

### 日志文件位置

所有服务的日志文件都保存在 `./pids/` 目录下：

```
./pids/
├── case-service.log
├── ai-service.log
├── exec-service.log
├── api-gateway.log
└── frontend.log
```

## 💡 最佳实践

1. **首次使用**: 运行 `./start.sh` 让脚本自动处理所有依赖
2. **日常使用**: 使用 `./status.sh` 检查服务状态
3. **停止服务**: 使用 `./stop.sh stop` 优雅停止
4. **完全清理**: 使用 `./stop.sh clean` 清理所有文件（慎用）
5. **开发调试**: 直接查看 `./pids/` 目录下的日志文件

## 🌟 特色功能

- **智能依赖检测**: 自动检测和安装缺失的依赖
- **默认AI模型**: 自动配置GLM-4.5-AIR作为默认模型
- **彩色日志**: 使用不同颜色区分日志级别
- **PID管理**: 自动管理进程PID文件
- **健康检查**: 自动验证服务启动状态
- **资源监控**: 显示系统资源使用情况
- **网络检查**: 验证端口监听状态

## 📝 更新日志

- **2026-02-02**: 初始脚本创建
- **2026-02-02**: 添加Z.AI GLM-4.5-AIR支持
- **2026-02-02**: 完善错误处理和日志记录
- **2026-02-02**: 添加系统资源监控功能