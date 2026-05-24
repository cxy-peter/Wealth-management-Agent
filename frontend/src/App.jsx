import { BarChart3, FileText, GitBranch, Landmark, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { useMemo, useState } from 'react';

import AgentTraceView from './pages/AgentTraceView.jsx';
import HumanReview from './pages/HumanReview.jsx';
import ProductBenchmarkWorkbench from './pages/ProductBenchmarkWorkbench.jsx';
import WeeklyReportDashboard from './pages/WeeklyReportDashboard.jsx';
import { sampleAnalysis } from './data/mockData.js';

const pages = [
  { id: 'weekly', label: '产品周报', icon: FileText },
  { id: 'benchmark', label: '产品对标', icon: BarChart3 },
  { id: 'trace', label: '审计追踪', icon: GitBranch }
];

export default function App() {
  const [activePage, setActivePage] = useState('weekly');
  const [analysis, setAnalysis] = useState(sampleAnalysis);
  const [selectedProductCode, setSelectedProductCode] = useState('WP0031');
  const [reviewOpen, setReviewOpen] = useState(false);

  const activeMeta = useMemo(() => pages.find((page) => page.id === activePage) || pages[0], [activePage]);
  const ActiveIcon = activeMeta.icon;
  const pendingReview = analysis.human_review?.status === 'pending_review';

  function handleAnalysis(nextAnalysis) {
    setAnalysis(nextAnalysis);
    if (nextAnalysis?.human_review?.status === 'pending_review') {
      setReviewOpen(true);
    }
  }

  function navigateToBenchmark(productCode = selectedProductCode) {
    setSelectedProductCode(productCode || 'WP0031');
    setActivePage('benchmark');
  }

  function navigateToTrace() {
    setActivePage('trace');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Landmark size={22} />
          </div>
          <div>
            <div className="brand-title">wealth-research-agent</div>
            <div className="brand-subtitle">资管产品周报工作台</div>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {pages.map((page) => {
            const Icon = page.icon;
            return (
              <button
                key={page.id}
                className={`nav-item ${activePage === page.id ? 'active' : ''}`}
                onClick={() => setActivePage(page.id)}
                title={page.label}
              >
                <Icon size={18} />
                <span>{page.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <div className="status-row">
            <SlidersHorizontal size={16} />
            <span>数据</span>
            <strong>演示数据</strong>
          </div>
          <div className="status-row">
            <ShieldCheck size={16} />
            <span>边界</span>
            <strong>仅用于投研辅助</strong>
          </div>
          {pendingReview ? (
            <button className="review-chip" onClick={() => setReviewOpen(true)}>
              待人工复核
            </button>
          ) : null}
        </div>
      </aside>

      <main className="main-surface">
        <header className="topbar">
          <div>
            <div className="eyebrow">产品周报 / 竞品对标 / 市场分位 / 渠道对标 / 审计追溯</div>
            <h1>
              <ActiveIcon size={26} />
              {activeMeta.label}
            </h1>
          </div>
          <div className="scope-pill">
            <ShieldCheck size={16} />
            合规边界已启用
          </div>
        </header>

        {activePage === 'weekly' ? (
          <WeeklyReportDashboard
            analysis={analysis}
            onAnalysis={handleAnalysis}
            onOpenBenchmark={navigateToBenchmark}
            onOpenTrace={navigateToTrace}
          />
        ) : null}
        {activePage === 'benchmark' ? (
          <ProductBenchmarkWorkbench
            analysis={analysis}
            onAnalysis={handleAnalysis}
            initialProductCode={selectedProductCode}
          />
        ) : null}
        {activePage === 'trace' ? <AgentTraceView analysis={analysis} /> : null}
      </main>

      <HumanReview
        analysis={analysis}
        isOpen={reviewOpen}
        onClose={() => setReviewOpen(false)}
        onAnalysis={handleAnalysis}
      />
    </div>
  );
}
