-- AI测试工具数据库初始化脚本

-- 创建测试用例表
CREATE TABLE IF NOT EXISTS test_cases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    assertions JSONB,
    variables JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试套件表
CREATE TABLE IF NOT EXISTS test_suites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    case_ids INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试数据表
CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试运行表
CREATE TABLE IF NOT EXISTS test_runs (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES test_cases(id),
    suite_id INTEGER REFERENCES test_suites(id),
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试步骤结果表
CREATE TABLE IF NOT EXISTS test_step_results (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_name VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    ai_analysis TEXT,
    screenshot_url TEXT,
    dom_snapshot_url TEXT,
    execution_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试证据表
CREATE TABLE IF NOT EXISTS test_evidence (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES test_step_results(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    file_url TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试报告表
CREATE TABLE IF NOT EXISTS test_reports (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    suite_id INTEGER REFERENCES test_suites(id),
    title VARCHAR(255) NOT NULL,
    summary JSONB NOT NULL,
    report_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建录制会话表
CREATE TABLE IF NOT EXISTS recording_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(500) NOT NULL,
    actions JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'recording',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_test_cases_name ON test_cases(name);
CREATE INDEX idx_test_runs_case_id ON test_runs(case_id);
CREATE INDEX idx_test_runs_status ON test_runs(status);
CREATE INDEX idx_test_step_results_run_id ON test_step_results(run_id);
CREATE INDEX idx_test_evidence_run_id ON test_evidence(run_id);
CREATE INDEX idx_recording_sessions_session_id ON recording_sessions(session_id);

-- 插入示例数据
INSERT INTO test_cases (name, description, steps, assertions) VALUES
('示例登录测试', '测试用户登录功能', 
 '[{"name":"输入用户名","action":"type","selector":"#username","value":"testuser"},{"name":"输入密码","action":"type","selector":"#password","value":"password123"},{"name":"点击登录按钮","action":"click","selector":"button[type=submit]"}]'::jsonb,
 '[{"type":"urlContains","value":"/dashboard","description":"页面应跳转到仪表盘"}]'::jsonb
);

COMMENT ON TABLE test_cases IS '测试用例表';
COMMENT ON TABLE test_suites IS '测试套件表';
COMMENT ON TABLE test_data IS '测试数据表';
COMMENT ON TABLE test_runs IS '测试运行记录表';
COMMENT ON TABLE test_step_results IS '测试步骤结果表';
COMMENT ON TABLE test_evidence IS '测试证据表';
COMMENT ON TABLE test_reports IS '测试报告表';
COMMENT ON TABLE recording_sessions IS '录制会话表';
