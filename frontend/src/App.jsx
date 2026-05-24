import { BarChart3, FileText, Gauge, GitBranch, Landmark, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { useMemo, useState } from 'react';

import HumanReview from './pages/HumanReview.jsx';
import ProductBenchmark from './pages/ProductBenchmark.jsx';
import ResearchDashboard from './pages/ResearchDashboard.jsx';
import TraceView from './pages/TraceView.jsx';
import { sampleAnalysis } from './data/mockData.js';

const pages = [
  { id: 'research', label: 'ResearchDashboard', icon: FileText },
  { id: 'benchmark', label: 'ProductBenchmark', icon: BarChart3 },
  { id: 'trace', label: 'TraceView', icon: GitBranch }
];

export default function App() {
  const [activePage, setActivePage] = useState('research');
  const [analysis, setAnalysis] = useState(sampleAnalysis);
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

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Landmark size={22} />
          </div>
          <div>
            <div className="brand-title">wealth-research-agent</div>
            <div className="brand-subtitle">资管投研辅助 Agent 系统</div>
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
            <Gauge size={16} />
            <span>Workflow</span>
            <strong>{analysis.workflow_engine || 'mock'}</strong>
          </div>
          <div className="status-row">
            <SlidersHorizontal size={16} />
            <span>Data</span>
            <strong>sample/mock</strong>
          </div>
          {pendingReview ? (
            <button className="review-chip" onClick={() => setReviewOpen(true)}>
              Pending review
            </button>
          ) : null}
        </div>
      </aside>

      <main className="main-surface">
        <header className="topbar">
          <div>
            <div className="eyebrow">投研辅助 / 风险摘要 / 产品对标 / 研究报告生成</div>
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

        {activePage === 'research' ? <ResearchDashboard analysis={analysis} onAnalysis={handleAnalysis} /> : null}
        {activePage === 'benchmark' ? <ProductBenchmark analysis={analysis} onAnalysis={handleAnalysis} /> : null}
        {activePage === 'trace' ? <TraceView analysis={analysis} /> : null}
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
