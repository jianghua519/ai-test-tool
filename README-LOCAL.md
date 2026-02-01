# AI Test Tool - 本地启动指南

## 🚀 快速启动

### 1. 启动所有服务

```bash
# 双击或在命令行运行
start-all.bat
```

该脚本会：
- 检查 PostgreSQL 和 MinIO 是否运行
- 启动所有后端服务（6个微服务）
- 启动前端服务
- 自动检测服务状态

### 2. 停止所有服务

```bash
# 双击或在命令行运行
stop-all.bat
```

## 📊 服务访问地址

| 服务 | 地址 | 端口 | 说明 |
|------|------|------|------|
| 前端应用 | http://localhost:5173 | 5173 | React 管理界面 |
| API 网关 | http://localhost:3000 | 3000 | 所有请求的入口 |
| 用例服务 | http://localhost:8001 | 8001 | 测试用例管理 |
| 执行服务 | http://localhost:3001 | 3001 | 测试执行引擎 |
| 报告服务 | http://localhost:8002 | 8002 | 测试报告生成 |
| AI 服务 | http://localhost:8003 | 8003 | AI 能力支持 |
| 探索服务 | http://localhost:8004 | 8004 | 网页探索和自动生成 |
| MinIO 控制台 | http://localhost:9001 | 9001 | 对象存储管理 |
| 数据库 | localhost:5432 | 5432 | PostgreSQL 数据库 |

## 🔧 环境要求

### 必需软件
- **Node.js**: 版本 18+（建议 20+）
- **Python**: 版本 3.8+
- **pnpm**: 包管理器 (`npm install -g pnpm`)
- **PostgreSQL**: 数据库服务器
- **MinIO**: 对象存储服务

### 可选软件
- **Chrome**: 浏览器自动化测试
- **VS Code**: 开发编辑器

## 🛠️ 手动启动（如果脚本失败）

### 1. 启动数据库和存储

使用 Docker 快速启动：
```bash
# PostgreSQL
docker run --name postgres -e POSTGRES_PASSWORD=testpass123 -e POSTGRES_USER=testuser -e POSTGRES_DB=ai_test_tool -p 5432:5432 -d postgres:15

# MinIO
docker run --name minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin123 -p 9000:9000 -p 9001:9001 -d minio/minio server /data
```

### 2. 启动后端服务

```bash
# 进入项目目录
cd backend

# 用例服务
cd case-service
pip install -r requirements.txt
python main.py

# 执行服务（新终端）
cd ../exec-service
npm install
node src/index.js

# 报告服务（新终端）
cd ../report-service
pip install -r requirements.txt
python main.py

# AI 服务（新终端）
cd ../ai-service
pip install -r requirements.txt
python main.py

# 探索服务（新终端）
cd ../explorer-service
python main.py

# API 网关（新终端）
cd ../api-gateway
npm install
node src/index.js
```

### 3. 启动前端

```bash
cd frontend/ai-test-frontend
pnpm install
pnpm dev
```

## 🧪 运行测试

### 1. 集成测试

```bash
# 运行集成测试
python test-integration.py
```

该测试会检查所有服务的健康状态，并测试基本的 API 功能。

### 2. 探索服务测试

```bash
# 运行探索和AI服务测试
python test-explorer.py
```

## 🔍 故障排除

### 1. URI malformed 错误

如果前端出现 "URI malformed" 错误：
- 清理浏览器缓存
- 重启前端服务
- 确保没有特殊字符在 URL 中

### 2. 服务连接失败

检查端口占用：
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8001
netstat -ano | findstr :5173

# Linux/Mac
lsof -i :3000
lsof -i :8001
lsof -i :5173
```

### 3. 数据库连接失败

确保 PostgreSQL 运行：
```bash
# 检查 PostgreSQL 状态
pg_isready -h localhost -p 5432
```

### 4. 前端构建错误

清理并重新安装依赖：
```bash
cd frontend/ai-test-frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

## 📝 开发说明

### 项目结构
```
ai-test-tool/
├── backend/              # 后端微服务
│   ├── api-gateway/      # API 网关 (端口 3000)
│   ├── case-service/     # 用例管理 (端口 8001)
│   ├── exec-service/     # 测试执行 (端口 3001)
│   ├── report-service/   # 报告生成 (端口 8002)
│   ├── ai-service/       # AI 能力 (端口 8003)
│   └── explorer-service/ # 探索服务 (端口 8004)
├── frontend/             # 前端项目
│   └── ai-test-frontend/ # React 应用
├── browser-extension/    # 浏览器扩展
├── start-all.bat         # 启动脚本
├── stop-all.bat          # 停止脚本
├── test-integration.py   # 集成测试
└── test-explorer.py      # 探索测试
```

### 端口冲突
如果某个端口被占用，可以修改相应服务的配置文件：
- 后端服务：修改服务代码中的端口定义
- 前端：修改 `vite.config.ts` 中的 `server.port`

### 日志查看
- 后端服务：直接在终端查看日志
- 前端：浏览器开发者工具 -> Console