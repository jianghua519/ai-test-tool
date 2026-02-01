import Fastify from 'fastify';
import cors from '@fastify/cors';
import proxy from '@fastify/http-proxy';
import dotenv from 'dotenv';

dotenv.config();

const fastify = Fastify({
  logger: true
});

// 启用CORS
await fastify.register(cors, {
  origin: true,
  credentials: true
});

// 健康检查
fastify.get('/health', async (request, reply) => {
  return { status: 'ok', timestamp: new Date().toISOString() };
});

// 代理到用例管理服务
fastify.register(proxy, {
  upstream: process.env.CASE_SERVICE_URL || 'http://localhost:8001',
  prefix: '/api/cases',
  rewritePrefix: '/api/cases',
  http2: false
});

// 代理到测试执行服务
fastify.register(proxy, {
  upstream: process.env.EXEC_SERVICE_URL || 'http://localhost:3001',
  prefix: '/api/exec',
  rewritePrefix: '/api/exec',
  http2: false
});

// 代理到报告服务
fastify.register(proxy, {
  upstream: process.env.REPORT_SERVICE_URL || 'http://localhost:8002',
  prefix: '/api/reports',
  rewritePrefix: '/api/reports',
  http2: false
});

// 代理到AI服务
fastify.register(proxy, {
  upstream: process.env.AI_SERVICE_URL || 'http://localhost:8003',
  prefix: '/api/ai',
  rewritePrefix: '/api/ai',
  http2: false
});

// 启动服务
const start = async () => {
  try {
    const port = process.env.PORT || 3000;
    await fastify.listen({ port, host: '0.0.0.0' });
    console.log(`API Gateway listening on port ${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
