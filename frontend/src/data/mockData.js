export const sampleAnalysis = {
  run_id: 'run_mock_preview',
  symbol: '600519',
  company: '贵州茅台',
  workflow_engine: 'mock-preview',
  planner_plan: {
    task_type: 'standard_research',
    analysis_depth: 'standard',
    required_tools: ['load_price_series', 'calculate_metrics', 'load_fundamental_snapshot', 'load_valuation_snapshot', 'load_news', 'classify_news_risk', 'product_benchmark'],
    skipped_tools: [],
    risk_level: 'medium',
    human_review_required: false
  },
  metrics: {
    observations: 25,
    total_return: 0.024,
    annualized_return: 0.2828,
    annualized_volatility: 0.0687,
    max_drawdown: -0.0079,
    sharpe_ratio: 3.824
  },
  fundamental_analysis: {
    quality_label: '盈利质量样例较强',
    points: ['营收增速样例值为 8.3%。', 'ROE 样例值为 28.6%，净利率样例值为 47.2%。']
  },
  valuation_analysis: {
    valuation_band: '相对同业中位数偏高',
    points: ['PE(TTM) 为 28.4，同业样例中位数为 24.8。', '估值结论只用于横向描述。']
  },
  technical_analysis: {
    trend_label: '样本内短期趋势偏强',
    risk_regime: '低波动观察',
    ma5: 1530.4,
    ma20: 1518.7,
    momentum_5d: 0.0039,
    momentum_20d: 0.0186
  },
  news_summary: {
    avg_sentiment: 3.5,
    avg_risk: 2.75,
    signal_count: 4,
    top_risks: ['监管关注酒类价格秩序', '消费数据分化']
  },
  news_signals: [
    {
      date: '2025-01-08',
      title: '春节消费预期回暖',
      sentiment_score: 4,
      risk_score: 3,
      model_mode: 'rule-based-fallback',
      evidence: 'positive_hits=2; negative_hits=1; high_risk_hits=1'
    },
    {
      date: '2025-01-14',
      title: '监管关注酒类价格秩序',
      sentiment_score: 2,
      risk_score: 4,
      model_mode: 'rule-based-fallback',
      evidence: 'positive_hits=0; negative_hits=1; high_risk_hits=2'
    },
    {
      date: '2025-01-21',
      title: '公司推进分红规划',
      sentiment_score: 5,
      risk_score: 2,
      model_mode: 'rule-based-fallback',
      evidence: 'positive_hits=2; negative_hits=0; high_risk_hits=0'
    },
    {
      date: '2025-02-07',
      title: '消费数据分化',
      sentiment_score: 2,
      risk_score: 3,
      model_mode: 'rule-based-fallback',
      evidence: 'positive_hits=0; negative_hits=2; high_risk_hits=1'
    }
  ],
  peer_summary: {
    product_count: 5,
    risk_levels: ['R1', 'R2', 'R3', 'R4'],
    channels: ['线上渠道', '券商渠道', '机构渠道', '银行渠道'],
    methodology: '基于样例净值、期限、风险等级和渠道字段做横向对标；排序仅用于投研材料整理。',
    table: [
      {
        product_id: 'P004',
        product_name: '权益精选模拟',
        asset_class: '权益',
        channel: '券商渠道',
        risk_level: 'R4',
        annualized_return: 0.088,
        annualized_volatility: 0.16,
        max_drawdown: -0.072,
        sharpe_ratio: 0.425,
        return_rank: 1,
        risk_adjusted_rank: 4
      },
      {
        product_id: 'P002',
        product_name: '多资产平衡二号',
        asset_class: '多资产',
        channel: '银行渠道',
        risk_level: 'R3',
        annualized_return: 0.052,
        annualized_volatility: 0.075,
        max_drawdown: -0.034,
        sharpe_ratio: 0.427,
        return_rank: 2,
        risk_adjusted_rank: 3
      },
      {
        product_id: 'P005',
        product_name: '量化对冲模拟',
        asset_class: '量化',
        channel: '机构渠道',
        risk_level: 'R3',
        annualized_return: 0.041,
        annualized_volatility: 0.075,
        max_drawdown: -0.034,
        sharpe_ratio: 0.28,
        return_rank: 3,
        risk_adjusted_rank: 5
      },
      {
        product_id: 'P001',
        product_name: '固收+稳健一号',
        asset_class: '固收+',
        channel: '银行渠道',
        risk_level: 'R2',
        annualized_return: 0.036,
        annualized_volatility: 0.035,
        max_drawdown: -0.016,
        sharpe_ratio: 0.457,
        return_rank: 4,
        risk_adjusted_rank: 2
      },
      {
        product_id: 'P003',
        product_name: '现金管理增强',
        asset_class: '现金管理',
        channel: '线上渠道',
        risk_level: 'R1',
        annualized_return: 0.012,
        annualized_volatility: 0.015,
        max_drawdown: -0.007,
        sharpe_ratio: -0.533,
        return_rank: 5,
        risk_adjusted_rank: 1
      }
    ]
  },
  risk_flags: [
    '相对估值样例高于同业中位数，需要拆分质量溢价、成长预期和估值回撤风险。',
    '产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。',
    '输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。'
  ],
  tool_calls: [
    { tool_call_id: 'tc_mock_price', tool_name: 'load_price_series', success: true, latency_ms: 5.1, evidence_ids: ['ev_sample_nav_600519'] },
    { tool_call_id: 'tc_mock_metrics', tool_name: 'calculate_metrics', success: true, latency_ms: 6.8, evidence_ids: ['ev_metrics_600519'] },
    { tool_call_id: 'tc_mock_news', tool_name: 'classify_news_risk', success: true, latency_ms: 4.7, evidence_ids: ['ev_news_risk_600519'] },
    { tool_call_id: 'tc_mock_products', tool_name: 'product_benchmark', success: true, latency_ms: 3.2, evidence_ids: ['ev_product_benchmark_5'] }
  ],
  agent_events: [
    { event_type: 'planner_output', agent_name: 'planner_agent', payload: { task_type: 'standard_research' } },
    { event_type: 'agent_final', agent_name: 'technical_react_agent', payload: { trend_label: '样本内短期趋势偏强' } },
    { event_type: 'verification_result', agent_name: 'verifier_agent', payload: { pass: true, confidence_score: 1 } }
  ],
  verification_result: {
    pass: true,
    failed_checks: [],
    metric_mismatches: [],
    missing_evidence: [],
    forbidden_wording: false,
    confidence_score: 1
  },
  human_review: {
    status: 'auto_cleared',
    interrupt_available: true
  },
  report_markdown: '# 资管投研辅助 Agent 报告\n\n本报告仅用于投研辅助、风险摘要、产品对标和研究报告生成，不构成投资建议。'
};

export const instrumentOptions = [
  { symbol: '600519', company: '贵州茅台', label: '贵州茅台 / 600519' },
  { symbol: 'P001', company: '固收+稳健一号', label: '固收+稳健一号 / P001' },
  { symbol: 'P002', company: '多资产平衡二号', label: '多资产平衡二号 / P002' }
];

export const evalResults = {
  metrics: {
    tool_call_success: 1,
    report_format_pass: 1,
    metric_consistency: 1,
    risk_warning_coverage: 1,
    forbidden_wording_fail_rate: 0,
    avg_latency_ms: 119.23
  },
  cases: [
    {
      symbol: '600519',
      passed: true,
      workflow_engine: 'langgraph',
      latency_ms: 119.23
    }
  ]
};

export const routeOptimizationResults = {
  average_reward: 0.9386,
  policy: {
    values: {
      fast_snapshot: 0,
      standard_research: 0.9328,
      deep_review: 0,
      product_compare: 0.9435,
      risk_only: 0.9394
    }
  },
  evaluations: [
    { action: 'standard_research', reward: 0.9328, planner_task_type: 'standard_research' },
    { action: 'risk_only', reward: 0.9394, planner_task_type: 'risk_only' },
    { action: 'product_compare', reward: 0.9435, planner_task_type: 'product_compare' }
  ]
};

export const replayBars = [
  { date: '01-02', value: 100, event: '样例期初' },
  { date: '01-07', value: 101.4, event: '价格小幅修复' },
  { date: '01-14', value: 100.6, event: '新闻风险升温' },
  { date: '01-21', value: 101.7, event: '分红主题进入观察' },
  { date: '01-28', value: 102.1, event: '波动回落' },
  { date: '02-07', value: 102.4, event: '消费数据分化' },
  { date: '02-12', value: 102.6, event: '样例期末' }
];
