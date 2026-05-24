import { Pause, Play, RotateCcw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { replayBars } from '../data/mockData.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

export default function PaperReplay({ analysis }) {
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const bars = replayBars;
  const first = bars[0]?.value || 100;
  const current = bars[cursor] || bars[0];
  const pathReturn = current ? current.value / first - 1 : 0;

  useEffect(() => {
    if (!playing) return undefined;
    const timer = window.setInterval(() => {
      setCursor((value) => {
        if (value >= bars.length - 1) {
          setPlaying(false);
          return value;
        }
        return value + 1;
      });
    }, 900);
    return () => window.clearInterval(timer);
  }, [playing, bars.length]);

  const riskContext = useMemo(() => {
    const flags = analysis.risk_flags || [];
    return flags.slice(0, 3);
  }, [analysis.risk_flags]);

  return (
    <div className="page-stack">
      <section className="control-band">
        <button className="primary-btn" onClick={() => setPlaying((value) => !value)}>
          {playing ? <Pause size={18} /> : <Play size={18} />}
          {playing ? '暂停回放' : '开始回放'}
        </button>
        <button
          className="icon-btn"
          onClick={() => {
            setCursor(0);
            setPlaying(false);
          }}
          title="重置回放"
        >
          <RotateCcw size={18} />
        </button>
        <div className="inline-status">
          <span>教学模拟，不连接账户、不发送订单、不使用真实客户数据。</span>
        </div>
      </section>

      <section className="replay-layout">
        <div className="panel replay-chart-panel">
          <div className="section-title">
            <span>{analysis.company || '样例标的'} 路径回放</span>
            <strong>{current.date}</strong>
          </div>
          <div className="bar-chart" aria-label="paper replay chart">
            {bars.map((bar, index) => {
              const height = 36 + (bar.value - 98) * 16;
              return (
                <button
                  key={bar.date}
                  className={`bar ${index <= cursor ? 'active' : ''} ${index === cursor ? 'focus' : ''}`}
                  style={{ height: `${Math.max(24, height)}px` }}
                  onClick={() => setCursor(index)}
                  title={`${bar.date}: ${bar.event}`}
                >
                  <span>{bar.date}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="panel">
          <div className="section-title">
            <span>当前节点</span>
            <strong>{pct(pathReturn)}</strong>
          </div>
          <div className="two-column-facts">
            <div>
              <span>日期</span>
              <strong>{current.date}</strong>
            </div>
            <div>
              <span>样例值</span>
              <strong>{current.value.toFixed(2)}</strong>
            </div>
            <div className="wide-fact">
              <span>事件</span>
              <strong>{current.event}</strong>
            </div>
          </div>
          <div className="evidence-list replay-notes">
            {riskContext.map((item) => (
              <div className="evidence-row" key={item}>
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
