import Fastify from 'fastify';
import cors from '@fastify/cors';
import { chromium } from 'playwright';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs/promises';
import path from 'path';

dotenv.config();

const fastify = Fastify({ logger: true });

// 数据库连接
let db;
async function initDb() {
  db = await open({
    filename: process.env.DATABASE_URL ? process.env.DATABASE_URL.replace('sqlite:///', '') : './test.db',
    driver: sqlite3.Database
  });
}
await initDb();

// 启用CORS
await fastify.register(cors, {
  origin: true,
  credentials: true
});

// 证据存储目录
const EVIDENCE_DIR = process.env.EVIDENCE_DIR || '/tmp/test-evidence';
await fs.mkdir(EVIDENCE_DIR, { recursive: true });

// 健康检查
fastify.get('/health', async (request, reply) => {
  return { status: 'ok', service: 'exec-service' };
});

// Playwright执行引擎
class PlaywrightExecutor {
  constructor() {
    this.browser = null;
  }

  async initialize() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async executeTestCase(testCase, runId) {
    await this.initialize();
    
    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();
    
    const results = [];
    let currentUrl = null;

    try {
      // 执行每个步骤
      for (let i = 0; i < testCase.steps.length; i++) {
        const step = testCase.steps[i];
        const stepStartTime = Date.now();
        
        try {
          // 执行前截图
          const beforeScreenshot = path.join(EVIDENCE_DIR, `${runId}_step${i}_before.png`);
          await page.screenshot({ path: beforeScreenshot, fullPage: false });
          
          // 执行操作
          await this.executeAction(page, step);
          
          // 等待页面稳定
          await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
          
          // 执行后截图
          const afterScreenshot = path.join(EVIDENCE_DIR, `${runId}_step${i}_after.png`);
          await page.screenshot({ path: afterScreenshot, fullPage: false });
          
          // 保存DOM快照
          const domSnapshot = path.join(EVIDENCE_DIR, `${runId}_step${i}_dom.html`);
          const htmlContent = await page.content();
          await fs.writeFile(domSnapshot, htmlContent);
          
          // 获取控制台日志
          const consoleLogs = [];
          page.on('console', msg => consoleLogs.push(`${msg.type()}: ${msg.text()}`));
          
          currentUrl = page.url();
          
          const stepResult = {
            step_index: i,
            step_name: step.name || `Step ${i + 1}`,
            status: 'passed',
            error_message: null,
            ai_analysis: null,
            screenshot_url: afterScreenshot,
            dom_snapshot_url: domSnapshot,
            execution_time: Date.now() - stepStartTime
          };
          
          results.push(stepResult);
          
          // 保存步骤结果到数据库
          await this.saveStepResult(runId, stepResult);
          
        } catch (error) {
          // 失败时的截图
          const errorScreenshot = path.join(EVIDENCE_DIR, `${runId}_step${i}_error.png`);
          await page.screenshot({ path: errorScreenshot, fullPage: false }).catch(() => {});
          
          // 获取DOM快照
          const errorDom = path.join(EVIDENCE_DIR, `${runId}_step${i}_error_dom.html`);
          const htmlContent = await page.content().catch(() => '');
          await fs.writeFile(errorDom, htmlContent).catch(() => {});
          
          // 调用AI分析错误
          const aiAnalysis = await this.analyzeError(step, error.message, errorScreenshot, htmlContent);
          
          const stepResult = {
            step_index: i,
            step_name: step.name || `Step ${i + 1}`,
            status: 'failed',
            error_message: error.message,
            ai_analysis: JSON.stringify(aiAnalysis),
            screenshot_url: errorScreenshot,
            dom_snapshot_url: errorDom,
            execution_time: Date.now() - stepStartTime
          };
          
          results.push(stepResult);
          
          // 保存步骤结果到数据库
          await this.saveStepResult(runId, stepResult);
          
          // 失败后停止执行
          break;
        }
      }
      
      // 执行断言
      if (testCase.assertions && testCase.assertions.length > 0) {
        for (const assertion of testCase.assertions) {
          try {
            await this.executeAssertion(page, assertion);
          } catch (error) {
            results.push({
              step_index: testCase.steps.length,
              step_name: `Assertion: ${assertion.description}`,
              status: 'failed',
              error_message: error.message,
              execution_time: 0
            });
          }
        }
      }
      
    } finally {
      await context.close();
    }
    
    return results;
  }

  async executeAction(page, step) {
    const { action, selector, value } = step;
    
    switch (action) {
      case 'type':
        await page.fill(selector, value || '');
        break;
      
      case 'click':
        await page.click(selector);
        break;
      
      case 'select':
        await page.selectOption(selector, value);
        break;
      
      case 'check':
        await page.check(selector);
        break;
      
      case 'uncheck':
        await page.uncheck(selector);
        break;
      
      case 'navigate':
        await page.goto(value || selector);
        break;
      
      case 'wait':
        await page.waitForTimeout(parseInt(value) || 1000);
        break;
      
      case 'waitForSelector':
        await page.waitForSelector(selector, { timeout: 10000 });
        break;
      
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  async executeAssertion(page, assertion) {
    const { type, value } = assertion;
    
    switch (type) {
      case 'urlContains':
        if (!page.url().includes(value)) {
          throw new Error(`URL does not contain "${value}". Current URL: ${page.url()}`);
        }
        break;
      
      case 'textVisible':
        const isVisible = await page.locator(`text=${value}`).isVisible();
        if (!isVisible) {
          throw new Error(`Text "${value}" is not visible`);
        }
        break;
      
      case 'elementExists':
        const count = await page.locator(value).count();
        if (count === 0) {
          throw new Error(`Element "${value}" does not exist`);
        }
        break;
      
      case 'elementVisible':
        const visible = await page.locator(value).isVisible();
        if (!visible) {
          throw new Error(`Element "${value}" is not visible`);
        }
        break;
      
      default:
        throw new Error(`Unknown assertion type: ${type}`);
    }
  }

  async analyzeError(step, errorMessage, screenshotPath, domContent) {
    try {
      const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8003';
      const response = await fetch(`${aiServiceUrl}/api/ai/analyze-error`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step_name: step.name || 'Unknown step',
          selector: step.selector || '',
          error_message: errorMessage,
          dom_context: domContent.substring(0, 2000)
        })
      });
      
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('AI analysis failed:', error);
    }
    
    return {
      root_cause: errorMessage,
      explanations: ['AI analysis unavailable'],
      suggestions: ['Check the error message and screenshot'],
      confidence: 'low'
    };
  }

  async saveStepResult(runId, stepResult) {
    const query = `
      INSERT INTO test_step_results 
      (run_id, step_index, step_name, status, error_message, ai_analysis, screenshot_url, dom_snapshot_url, execution_time, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `;
    
    const values = [
      runId,
      stepResult.step_index,
      stepResult.step_name,
      stepResult.status,
      stepResult.error_message,
      stepResult.ai_analysis,
      stepResult.screenshot_url,
      stepResult.dom_snapshot_url,
      stepResult.execution_time
    ];
    
    await db.run(query, values);
  }
}

const executor = new PlaywrightExecutor();

// 执行单个测试用例
fastify.post('/api/exec/run', async (request, reply) => {
  const { case_id, variables } = request.body;
  
  if (!case_id) {
    return reply.code(400).send({ error: 'case_id is required' });
  }
  
  try {
    // 获取测试用例
    const caseServiceUrl = process.env.CASE_SERVICE_URL || 'http://localhost:8001';
    const caseResponse = await fetch(`${caseServiceUrl}/api/cases/${case_id}`);
    
    if (!caseResponse.ok) {
      return reply.code(404).send({ error: 'Test case not found' });
    }
    
    const testCase = await caseResponse.json();
    
    // 替换变量
    if (variables && testCase.steps) {
      testCase.steps = testCase.steps.map(step => ({
        ...step,
        value: step.value ? replaceVariables(step.value, variables) : step.value
      }));
    }
    
    // 创建测试运行记录
    const runId = await createTestRun(case_id, null);
    
    // 更新状态为运行中
    await updateTestRun(runId, 'running', null);
    
    // 执行测试
    const results = await executor.executeTestCase(testCase, runId);
    
    // 判断整体状态
    const hasFailed = results.some(r => r.status === 'failed');
    const status = hasFailed ? 'failed' : 'passed';
    
    // 更新测试运行结果
    await updateTestRun(runId, status, { results });
    
    return {
      run_id: runId,
      status,
      results
    };
    
  } catch (error) {
    fastify.log.error(error);
    return reply.code(500).send({ error: error.message });
  }
});

// 批量执行测试套件
fastify.post('/api/exec/run-suite', async (request, reply) => {
  const { suite_id, variables } = request.body;
  
  if (!suite_id) {
    return reply.code(400).send({ error: 'suite_id is required' });
  }
  
  try {
    // 获取测试套件
    const caseServiceUrl = process.env.CASE_SERVICE_URL || 'http://localhost:8001';
    const suiteResponse = await fetch(`${caseServiceUrl}/api/suites/${suite_id}`);
    
    if (!suiteResponse.ok) {
      return reply.code(404).send({ error: 'Test suite not found' });
    }
    
    const suite = await suiteResponse.json();
    const results = [];
    
    // 执行套件中的每个用例
    for (const caseId of suite.case_ids || []) {
      const runResponse = await fetch('http://localhost:3001/api/exec/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: caseId, variables })
      });
      
      if (runResponse.ok) {
        const runResult = await runResponse.json();
        results.push(runResult);
      }
    }
    
    return {
      suite_id,
      total: suite.case_ids?.length || 0,
      results
    };
    
  } catch (error) {
    fastify.log.error(error);
    return reply.code(500).send({ error: error.message });
  }
});

// 获取测试运行状态
fastify.get('/api/exec/runs/:run_id', async (request, reply) => {
  const { run_id } = request.params;
  
  try {
    const query = 'SELECT * FROM test_runs WHERE id = ?';
    const result = await db.get(query, [run_id]);
    
    if (!result) {
      return reply.code(404).send({ error: 'Test run not found' });
    }
    
    return result;
  } catch (error) {
    fastify.log.error(error);
    return reply.code(500).send({ error: error.message });
  }
});

// 辅助函数
function replaceVariables(text, variables) {
  let result = text;
  for (const [key, value] of Object.entries(variables)) {
    result = result.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), value);
  }
  return result;
}

async function createTestRun(caseId, suiteId) {
  const query = `
    INSERT INTO test_runs (case_id, suite_id, status, start_time)
    VALUES (?, ?, ?, datetime('now'))
  `;
  
  const result = await db.run(query, [caseId, suiteId, 'pending']);
  return result.lastID;
}

async function updateTestRun(runId, status, result) {
  const query = `
    UPDATE test_runs
    SET status = ?, end_time = datetime('now'), result = ?
    WHERE id = ?
  `;
  
  await db.run(query, [status, JSON.stringify(result), runId]);
}

// 启动服务
const start = async () => {
  try {
    const port = process.env.PORT || 3001;
    await fastify.listen({ port, host: '0.0.0.0' });
    console.log(`Exec Service listening on port ${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

// 优雅关闭
process.on('SIGTERM', async () => {
  await executor.close();
  await db.close();
  process.exit(0);
});

start();
