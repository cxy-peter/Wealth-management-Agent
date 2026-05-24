export const sampleAnalysis = {
  run_id: 'run_mock_preview',
  symbol: '600519',
  company: '贵州茅台',
  workflow_engine: 'mock-preview',
  planner_plan: {
    task_type: 'standard_research',
    analysis_depth: 'standard',
    required_tools: [
      'load_price_series',
      'calculate_metrics',
      'load_fundamental_snapshot',
      'load_valuation_snapshot',
      'load_news',
      'classify_news_risk',
      'product_benchmark'
    ],
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
    }
  ],
  peer_summary: {
    product_count: 108,
    product_universe_size: 108,
    risk_levels: ['R1', 'R2', 'R3', 'R4', 'R5'],
    channels: ['银行渠道', '线上渠道', '机构渠道', '券商渠道', '私行渠道'],
    filter_options: {
      asset_class: ['现金管理', '纯债固收', '固收+', '多资产', '权益增强', '量化对冲', '商品/黄金', 'QDII/全球配置', '养老目标/FOF'],
      strategy_type: ['现金管理', '利率债', '债券增强', '指数增强', '市场中性', '全球多资产'],
      risk_level: ['R1', 'R2', 'R3', 'R4', 'R5'],
      duration_bucket: ['0-3M', '3-6M', '6-12M', '1-3Y', '3Y+'],
      channel: ['银行渠道', '线上渠道', '机构渠道', '券商渠道', '私行渠道'],
      liquidity_type: ['每日开放', '每周开放', '每月开放', '每季开放', '持有期']
    },
    methodology: '基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。',
    table: [
      {
        product_id: 'SP0077',
        product_name: '权益增强指数增强样例077',
        asset_class: '权益增强',
        strategy_type: '指数增强',
        channel: '券商渠道',
        risk_level: 'R5',
        liquidity_type: '每月开放',
        duration_bucket: '1-3Y',
        annualized_return: 0.126,
        annualized_volatility: 0.236,
        max_drawdown: -0.162,
        sharpe_ratio: 0.449,
        calmar_ratio: 0.778,
        benchmark_excess_return: 0.031,
        return_rank: 1,
        risk_adjusted_rank: 18,
        metric_evidence_id: 'ev_product_metric_SP0077',
        source_tool_call_id: 'tc_mock_products'
      },
      {
        product_id: 'SP0034',
        product_name: '多资产目标波动样例034',
        asset_class: '多资产',
        strategy_type: '目标波动',
        channel: '银行渠道',
        risk_level: 'R3',
        liquidity_type: '每季开放',
        duration_bucket: '6-12M',
        annualized_return: 0.061,
        annualized_volatility: 0.082,
        max_drawdown: -0.046,
        sharpe_ratio: 0.500,
        calmar_ratio: 1.326,
        benchmark_excess_return: 0.012,
        return_rank: 16,
        risk_adjusted_rank: 9,
        metric_evidence_id: 'ev_product_metric_SP0034',
        source_tool_call_id: 'tc_mock_products'
      },
      {
        product_id: 'SP0012',
        product_name: '现金管理流动性管理样例012',
        asset_class: '现金管理',
        strategy_type: '流动性管理',
        channel: '线上渠道',
        risk_level: 'R1',
        liquidity_type: '每日开放',
        duration_bucket: '0-3M',
        annualized_return: 0.018,
        annualized_volatility: 0.006,
        max_drawdown: -0.002,
        sharpe_ratio: -0.333,
        calmar_ratio: 9.0,
        benchmark_excess_return: 0.002,
        return_rank: 92,
        risk_adjusted_rank: 71,
        metric_evidence_id: 'ev_product_metric_SP0012',
        source_tool_call_id: 'tc_mock_products'
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
    { tool_call_id: 'tc_mock_products', tool_name: 'product_benchmark', success: true, latency_ms: 3.2, evidence_ids: ['ev_product_benchmark_108'] }
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
  report_markdown: '# 资管投研辅助 Agent 报告\n\n本报告仅用于投研辅助、风险摘要、产品对标和研究报告生成。'
};

export const instrumentOptions = [
  { symbol: '600519', company: '贵州茅台', label: '贵州茅台 / 600519' },
  { symbol: 'SP0012', company: '现金管理流动性管理样例012', label: '现金管理样例 / SP0012' },
  { symbol: 'SP0034', company: '多资产目标波动样例034', label: '多资产样例 / SP0034' }
];

export const evalResults = {
  metrics: {
    tool_call_success: 1,
    report_format_pass: 1,
    metric_consistency: 1,
    risk_warning_coverage: 1,
    evidence_coverage: 1,
    forbidden_wording_fail_rate: 0,
    avg_latency_ms: 240.64
  },
  cases: [{ symbol: '600519', passed: true, workflow_engine: 'langgraph', latency_ms: 240.64 }]
};

export const routeOptimizationResults = {
  average_reward: 0.8657,
  policy: {
    values: {
      fast_snapshot: 0.8737,
      standard_research: 0.8518,
      deep_review: 0.8426,
      product_compare: 0.8785,
      risk_only: 0.882
    }
  },
  evaluations: [
    { action: 'standard_research', reward: 0.8237, planner_task_type: 'standard_research' },
    { action: 'risk_only', reward: 0.8861, planner_task_type: 'risk_only' },
    { action: 'product_compare', reward: 0.885, planner_task_type: 'product_compare' }
  ]
};

export const contextualBanditResults = {
  case_count: 90,
  best_policy: 'linucb_contextual_bandit',
  strategies: {
    fixed_standard_research: {
      average_reward: 0.682,
      average_latency_ms: 504.84,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.1547,
      action_distribution: { standard_research: 90 }
    },
    epsilon_greedy: {
      average_reward: 0.721,
      average_latency_ms: 316.66,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.131,
      action_distribution: { fast_snapshot: 4, standard_research: 11, deep_review: 13, product_compare: 5, risk_only: 57 }
    },
    linucb_contextual_bandit: {
      average_reward: 0.7518,
      average_latency_ms: 340.09,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.1003,
      action_distribution: { fast_snapshot: 18, standard_research: 18, deep_review: 13, product_compare: 18, risk_only: 23 }
    }
  }
};

export const replayBars = [
  { date: '01-02', value: 100, event: '样例期初' },
  { date: '01-14', value: 100.6, event: '新闻风险升温' },
  { date: '01-28', value: 102.1, event: '波动回落' },
  { date: '02-12', value: 102.6, event: '样例期末' }
];
