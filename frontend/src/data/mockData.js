export const weeklyMock = {
  report_date: '2025-04-04',
  product_count: 96,
  filter_options: {
    product_series: ['稳健添利', '悦享固收', '多元配置', '现金优选', '全球配置', '封闭精选', '持有期增强'],
    product_type: ['纯固收', '固收增强', '多资产', '混合类', 'QDII', '现金管理', '封闭式', '最短持有期型', '日开型'],
    channel: ['个金', '私银', '对公', '直销', '百信', '交行', '厦门银行', '邮惠万家'],
    risk_level: ['R1', 'R2', 'R3', 'R4', 'R5'],
    benchmark_status: ['above_upper', 'below_lower', 'in_range']
  },
  kpis: {
    total_scale_bn: 1330.0452,
    scale_wow_bn: 1.4164,
    scale_mom_bn: 2.8569,
    benchmark_pass_rate: 0.3646,
    benchmark_failed_count: 28,
    low_percentile_product_count: 22,
    attention_product_count: 41,
    scale_drop_count: 43,
    scale_evidence_ids: ['ev_snapshot_WP0001_20250404'],
    benchmark_evidence_ids: ['ev_snapshot_WP0002_20250404']
  },
  scale_change_rank: [
    {
      product_code: 'WP0031',
      product_name: '稳健添利现金管理样例031',
      product_type: '现金管理',
      channel: '交行',
      risk_level: 'R1',
      product_scale_bn: 30.185,
      scale_wow_bn: 0.316,
      scale_mom_bn: 0.472,
      evidence_id: 'ev_snapshot_WP0031_20250404'
    },
    {
      product_code: 'WP0047',
      product_name: '多元配置混合类样例047',
      product_type: '混合类',
      channel: '私银',
      risk_level: 'R4',
      product_scale_bn: 18.622,
      scale_wow_bn: -0.284,
      scale_mom_bn: -0.716,
      evidence_id: 'ev_snapshot_WP0047_20250404'
    }
  ],
  benchmark_failed_products: [
    {
      product_code: 'WP0028',
      product_name: '悦享固收固收增强样例028',
      product_type: '固收增强',
      channel: '百信',
      risk_level: 'R3',
      since_inception_annual_return: 0.021,
      benchmark_lower: 0.031,
      benchmark_upper: 0.052,
      benchmark_status: 'below_lower',
      evidence_id: 'ev_snapshot_WP0028_20250404'
    }
  ],
  percentile_decline_products: [
    {
      product_code: 'WP0047',
      product_name: '多元配置混合类样例047',
      product_type: '混合类',
      return_3m: -0.018,
      max_drawdown: -0.079,
      return_percentile: 0.18,
      drawdown_percentile: 0.24,
      evidence_id: 'ev_percentile_WP0047_20250404'
    }
  ],
  attention_top10: [
    {
      product_code: 'WP0047',
      product_name: '多元配置混合类样例047',
      product_type: '混合类',
      channel: '私银',
      risk_level: 'R4',
      benchmark_status: 'below_lower',
      scale_wow_bn: -0.284,
      return_3m: -0.018,
      max_drawdown: -0.079,
      return_percentile: 0.18,
      drawdown_percentile: 0.24,
      attention_score: 0.73,
      attention_reason_tags: ['基准未达标', '规模下降', '收益分位偏低', '回撤分位偏低'],
      evidence_id: 'ev_snapshot_WP0047_20250404'
    },
    {
      product_code: 'WP0028',
      product_name: '悦享固收固收增强样例028',
      product_type: '固收增强',
      channel: '百信',
      risk_level: 'R3',
      benchmark_status: 'below_lower',
      scale_wow_bn: -0.126,
      return_3m: -0.004,
      max_drawdown: -0.032,
      return_percentile: 0.29,
      drawdown_percentile: 0.41,
      attention_score: 0.49,
      attention_reason_tags: ['基准未达标', '收益分位偏低'],
      evidence_id: 'ev_snapshot_WP0028_20250404'
    }
  ],
  weekly_diff: [
    {
      product_code: 'WP0047',
      product_name: '多元配置混合类样例047',
      scale_change_vs_prev_week: -0.284,
      benchmark_status_prev: 'in_range',
      benchmark_status: 'below_lower',
      benchmark_status_changed: true,
      return_3m_change_vs_prev_week: -0.006,
      drawdown_change_vs_prev_week: -0.012,
      evidence_id: 'ev_snapshot_WP0047_20250404'
    }
  ],
  market_issuance: {
    new_product_count: 72,
    by_investment_nature: { 固定收益类: 38, 混合类: 14, 权益类: 6, 商品及金融衍生品类: 4, QDII: 10 },
    by_duration: { 日开: 9, '30天': 10, '90天': 15, '180天': 13, '360天': 11, '1年封闭': 14 },
    benchmark_lower_avg: 0.024,
    benchmark_upper_avg: 0.047,
    evidence_id: 'ev_market_issuance_20250404'
  },
  evidence_ids: ['ev_snapshot_WP0001_20250404', 'ev_market_issuance_20250404']
};

export const weeklyProductsMock = [
  {
    product_code: 'WP0031',
    product_name: '稳健添利现金管理样例031',
    product_type: '现金管理',
    product_series: '稳健添利',
    channel: '交行',
    risk_level: 'R1',
    open_type: '日开',
    product_scale_bn: 30.185,
    scale_wow_bn: 0.316,
    return_3m: 0.0058,
    max_drawdown: -0.0018,
    volatility: 0.0049,
    sharpe: 0.82,
    benchmark_status: 'in_range',
    return_percentile: 0.62,
    drawdown_percentile: 0.77,
    evidence_id: 'ev_snapshot_WP0031_20250404'
  },
  {
    product_code: 'WP0047',
    product_name: '多元配置混合类样例047',
    product_type: '混合类',
    product_series: '多元配置',
    channel: '私银',
    risk_level: 'R4',
    open_type: '180天',
    product_scale_bn: 18.622,
    scale_wow_bn: -0.284,
    return_3m: -0.018,
    max_drawdown: -0.079,
    volatility: 0.094,
    sharpe: -0.12,
    benchmark_status: 'below_lower',
    return_percentile: 0.18,
    drawdown_percentile: 0.24,
    evidence_id: 'ev_snapshot_WP0047_20250404'
  }
];

export const productDetailMock = {
  report_date: '2025-04-04',
  snapshot: weeklyProductsMock[0],
  nav: [
    { nav_date: '2025-01-10', nav: 1.002, benchmark_nav: 1.001, nav_evidence_id: 'ev_nav_mock_1' },
    { nav_date: '2025-01-17', nav: 1.004, benchmark_nav: 1.003, nav_evidence_id: 'ev_nav_mock_2' },
    { nav_date: '2025-01-24', nav: 1.003, benchmark_nav: 1.004, nav_evidence_id: 'ev_nav_mock_3' },
    { nav_date: '2025-01-31', nav: 1.007, benchmark_nav: 1.005, nav_evidence_id: 'ev_nav_mock_4' },
    { nav_date: '2025-02-07', nav: 1.009, benchmark_nav: 1.007, nav_evidence_id: 'ev_nav_mock_5' }
  ],
  percentile: {
    return_percentile: 0.62,
    drawdown_percentile: 0.77,
    sharpe_percentile: 0.58,
    evidence_id: 'ev_percentile_WP0031_20250404'
  },
  field_source_matrix: [
    { field: 'product_scale_bn', source: 'product_weekly_snapshot', source_type: 'synthetic_weekly_snapshot', as_of_date: '2025-04-04', confidence: 'medium', evidence_id: 'ev_snapshot_WP0031_20250404' },
    { field: 'return_3m', source: 'product_weekly_snapshot', source_type: 'synthetic_weekly_snapshot', as_of_date: '2025-04-04', confidence: 'medium', evidence_id: 'ev_snapshot_WP0031_20250404' },
    { field: 'return_percentile', source: 'peer_product_metrics', source_type: 'synthetic_weekly_snapshot', as_of_date: '2025-04-04', confidence: 'medium', evidence_id: 'ev_percentile_WP0031_20250404' }
  ],
  risk_events: [
    {
      event_date: '2025-04-04',
      event_type: 'benchmark_status',
      event_summary: 'benchmark_status=in_range; return_percentile=0.62',
      evidence_id: 'ev_percentile_WP0031_20250404'
    }
  ],
  evidence_ids: ['ev_snapshot_WP0031_20250404', 'ev_percentile_WP0031_20250404']
};

export const peerBenchmarkMock = {
  product_code: 'WP0031',
  report_date: '2025-04-04',
  product: weeklyProductsMock[0],
  percentile: productDetailMock.percentile,
  peer_count: 41,
  table: [
    {
      peer_product_code: 'PR0007',
      peer_product_name: '现金管理同业样例007',
      product_type: '现金管理',
      channel: '个金',
      return_3m: 0.0064,
      max_drawdown: -0.0019,
      volatility: 0.0047,
      sharpe: 0.86,
      return_percentile: 0.74,
      evidence_id_x: 'ev_peer_metric_PR0007'
    },
    {
      peer_product_code: 'PR0041',
      peer_product_name: '现金管理同业样例041',
      product_type: '现金管理',
      channel: '直销',
      return_3m: 0.0059,
      max_drawdown: -0.0022,
      volatility: 0.0044,
      sharpe: 0.81,
      return_percentile: 0.67,
      evidence_id_x: 'ev_peer_metric_PR0041'
    }
  ],
  peer_universe_explainer: {
    pool_rule: '同产品类型、同风险等级优先、同期限/同渠道优先，成立满3个月；样例不足时使用全市场同类扩展。',
    included: [
      { peer_product_code: 'PR0007', include_reason: ['同产品类型', '同风险等级', '成立满3个月'], evidence_id: 'ev_peer_metric_PR0007' }
    ],
    excluded: [
      { peer_product_code: 'PR0099', exclude_reason: '产品类型不一致', evidence_id: 'ev_peer_metric_PR0099' }
    ]
  },
  evidence_ids: ['ev_snapshot_WP0031_20250404', 'ev_peer_metric_PR0007']
};

export const channelBenchmarkMock = {
  peer_count: 96,
  channels: ['个金', '私银', '对公', '直销'],
  table: [
    { channel: '个金', product_type: '纯固收', peer_count: 12, avg_return_3m: 0.011, total_scale_bn: 118.5 },
    { channel: '私银', product_type: '混合类', peer_count: 9, avg_return_3m: 0.008, total_scale_bn: 74.2 }
  ],
  evidence_ids: ['ev_channel_peer_PR0001']
};

export const topPeersMock = {
  count: 2,
  table: [
    {
      rank: 1,
      peer_product_code: 'PR0012',
      peer_product_name: '固收增强同业样例012',
      product_type: '固收增强',
      return_3m: 0.024,
      return_percentile: 0.94,
      max_drawdown: -0.018,
      sharpe: 1.12,
      evidence_id: 'ev_top_peer_PR0012'
    },
    {
      rank: 2,
      peer_product_code: 'PR0088',
      peer_product_name: '固收增强同业样例088',
      product_type: '固收增强',
      return_3m: 0.021,
      return_percentile: 0.91,
      max_drawdown: -0.016,
      sharpe: 1.04,
      evidence_id: 'ev_top_peer_PR0088'
    }
  ]
};

export const sampleAnalysis = {
  run_id: 'weekly_run_mock_preview',
  weekly_report_date: weeklyMock.report_date,
  workflow_engine: 'weekly-mock-preview',
  planner_plan: {
    task_type: 'standard_weekly_report',
    required_tools: ['load_weekly_snapshot', 'calculate_weekly_metrics', 'peer_benchmark', 'weekly_report_verifier'],
    human_review_required: false
  },
  tool_calls: [
    { tool_call_id: 'tc_weekly_summary_mock', tool_name: 'weekly_summary', success: true, latency_ms: 18.4, evidence_ids: weeklyMock.evidence_ids },
    { tool_call_id: 'tc_peer_mock', tool_name: 'peer_benchmark', success: true, latency_ms: 24.1, evidence_ids: peerBenchmarkMock.evidence_ids }
  ],
  agent_events: [
    { event_type: 'planner_output', agent_name: 'weekly_planner', payload: { task_type: 'standard_weekly_report' } },
    { event_type: 'verification_result', agent_name: 'weekly_report_verifier', payload: { pass: true, confidence_score: 0.96 } }
  ],
  verification_result: {
    pass: true,
    failed_checks: [],
    metric_mismatches: [],
    missing_evidence: [],
    forbidden_wording: false,
    confidence_score: 0.96
  },
  guardrail: {
    pass: true,
    scope: 'weekly product research support only',
    forbidden_wording_hit: false
  },
  dpo_trace: {
    pair_count: 24,
    samples: [
      {
        id: 'dpo_weekly_001',
        chosen: '本周规模变化、收益表现、基准状态和风险提示均带 evidence_id。',
        rejected: '泛泛描述，缺少数字来源和风险提示。'
      }
    ]
  },
  evidence_ids: weeklyMock.evidence_ids,
  human_review: { status: 'auto_cleared' },
  report_markdown: '# 资管产品周报摘要\n\n本摘要基于 synthetic/mock 周报数据生成，仅用于投研辅助、风险摘要、产品对标和报告草稿整理。'
};

export const contextualBanditResults = {
  case_count: 96,
  best_policy: 'linucb_contextual_bandit',
  strategies: {
    fixed_standard_research: {
      average_reward: 0.7482,
      average_latency_ms: 453.43,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.0727,
      verifier_pass_rate: 0.6042,
      action_distribution: { standard_weekly_report: 96 }
    },
    epsilon_greedy: {
      average_reward: 0.7059,
      average_latency_ms: 732.18,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.115,
      verifier_pass_rate: 0.8229,
      action_distribution: { fast_weekly_snapshot: 7, standard_weekly_report: 7, deep_product_review: 72, benchmark_only: 5, market_update_only: 5 }
    },
    linucb_contextual_bandit: {
      average_reward: 0.7659,
      average_latency_ms: 498.52,
      forbidden_wording_fail_rate: 0,
      regret_vs_oracle: 0.055,
      verifier_pass_rate: 0.6875,
      action_distribution: { standard_weekly_report: 47, benchmark_only: 16, market_update_only: 11, deep_product_review: 22 }
    }
  }
};

export const dataFreshnessMock = {
  data_mode: 'sample/mock with explicit source metadata',
  stale_source_count: 0,
  sources_with_missing_metadata: 1,
  sources: [
    {
      source_type: 'historical_business_sample',
      source_name: '历史周报 schema sample',
      record_count: 960,
      latest_as_of_date: '2025-04-04',
      staleness_days: 0,
      confidence_level: 'medium',
      adapter_status: 'available',
      missing_fields: []
    },
    {
      source_type: 'official_disclosure_sample',
      source_name: '公开披露样本',
      record_count: 2,
      latest_as_of_date: '2025-04-04',
      staleness_days: 0,
      confidence_level: 'medium',
      adapter_status: 'available',
      missing_fields: []
    },
    {
      source_type: 'synthetic_weekly_snapshot',
      source_name: '模拟新周报',
      record_count: 96,
      latest_as_of_date: '2025-04-11',
      staleness_days: 0,
      confidence_level: 'medium',
      adapter_status: 'available',
      missing_fields: []
    }
  ]
};

export const dpoAgentEvalMock = {
  training_status: 'not_trained',
  adapter_available: false,
  variants: {
    template_baseline: { average_report_score: 0.57, verifier_pass_rate: 0.25, evidence_coverage_rate: 1, forbidden_wording_rate: 0 },
    sft_adapter_or_base: { average_report_score: 0.28, verifier_pass_rate: 0, evidence_coverage_rate: 0, forbidden_wording_rate: 0 },
    dpo_adapter: { average_report_score: 0.93, verifier_pass_rate: 1, evidence_coverage_rate: 1, forbidden_wording_rate: 0, preference_win_rate_vs_baseline: 1 }
  }
};

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
  cases: [{ case_id: 'weekly_eval_mock', passed: true, latency_ms: 240.64 }]
};
