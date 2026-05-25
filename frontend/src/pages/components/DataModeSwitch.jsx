import { Database, RotateCcw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { DATA_MODES, restoreDemoSynthetic, sessionSourceCounts, setDataMode } from '../../sessionDataStore.js';

const MODE_OPTIONS = [
  ['demo_synthetic', 'Demo synthetic'],
  ['uploaded_only', 'Uploaded only'],
  ['official_sample_uploaded', 'Official sample + uploaded'],
  ['hybrid', 'Hybrid']
];

function ScopeCounts({ scope, counts }) {
  const rows = Object.entries(counts || {});
  return (
    <div className="source-count-row">
      <strong>{scope}</strong>
      <span>{rows.length ? rows.map(([source, count]) => `${source} ${count}`).join(' / ') : 'no session records'}</span>
    </div>
  );
}

export default function DataModeSwitch({ demoCounts = {} }) {
  const [snapshot, setSnapshot] = useState(() => sessionSourceCounts(demoCounts));
  const currentMode = snapshot.data_mode || 'hybrid';

  useEffect(() => {
    const refresh = () => setSnapshot(sessionSourceCounts(demoCounts));
    window.addEventListener('wealth-agent-session-data-updated', refresh);
    refresh();
    return () => window.removeEventListener('wealth-agent-session-data-updated', refresh);
  }, [demoCounts]);

  const modeLabel = useMemo(() => DATA_MODES[currentMode] || currentMode, [currentMode]);

  return (
    <section className="panel data-mode-panel">
      <div className="section-title">
        <span>数据模式</span>
        <strong>{modeLabel}</strong>
      </div>
      <div className="data-mode-controls">
        <Database size={18} />
        <select
          value={currentMode}
          onChange={(event) => {
            setDataMode(event.target.value);
            setSnapshot(sessionSourceCounts(demoCounts));
          }}
        >
          {MODE_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <button
          className="link-btn"
          onClick={() => {
            restoreDemoSynthetic();
            setSnapshot(sessionSourceCounts(demoCounts));
          }}
        >
          <RotateCcw size={14} />
          恢复 demo 数据
        </button>
      </div>
      <div className="source-count-grid">
        <ScopeCounts scope="own_company" counts={snapshot.scopes?.own_company} />
        <ScopeCounts scope="full_market" counts={snapshot.scopes?.full_market} />
        <ScopeCounts scope="reference_rates" counts={snapshot.scopes?.reference_rates} />
      </div>
    </section>
  );
}
