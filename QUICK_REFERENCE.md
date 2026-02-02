# 🚀 AI测试工具 - 快速参考

## 📁 项目结构
```
ai-test-tool/
├── start.sh          # 启动所有服务
├── stop.sh           # 停止所有服务
├── status.sh         # 查看服务状态
├── SCRIPTS_GUIDE.md  # 详细使用说明
├── backend/          # 后端服务
│   ├── case-service/      # 测试用例管理
│   ├── ai-service/       # AI模型服务
│   ├── exec-service/     # 测试执行
│   └── api-gateway/      # API网关
└── frontend/
    └── ai-test-frontend/  # 前端应用
```

## 🎯 快速启动
```bash
# 一键启动所有服务
./start.sh

# 检查服务状态
./status.sh

# 停止所有服务
./stop.sh
```

## 🌐 服务访问
- **前端界面**: http://localhost:5173
- **API网关**: http://localhost:3000
- **后端服务**: 
  - Case Service: http://localhost:8001
  - AI Service: http://localhost:8003
  - Exec Service: http://localhost:3001

## ⚙️ AI模型配置
- **默认模型**: GLM-4.5-AIR (Z.AI)
- **API密钥**: 已配置
- **支持模型**: OpenAI, Ollama, Z.AI

## 🔧 故障排除
```bash
# 检查端口占用
lsof -i :端口号

# 查看服务日志
tail -f ./pids/服务名.log

# 强制停止进程
pkill -f "服务名"
```

## 📋 完整功能状态
- ✅ 后端服务架构 (微服务)
- ✅ 前端管理界面
- ✅ AI测试用例生成
- ✅ 测试执行引擎
- ✅ Z.AI GLM-4.5-AIR支持
- ✅ 服务管理脚本
- ✅ 默认AI模型配置
- ⚠️ 高级功能 (待开发)

## 📞 获取帮助
```bash
./start.sh help
./stop.sh help
./status.sh help
```

---

**提示**: 首次运行请使用 `./start.sh`，脚本会自动安装所有依赖！