import { CheckCircle2, Edit3, Loader2, X, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

import { approveReview, editReview, rejectReview } from '../api.js';

export default function HumanReview({ analysis, isOpen, onClose, onAnalysis }) {
  const [comment, setComment] = useState('');
  const [draft, setDraft] = useState(analysis.report_markdown || '');
  const [status, setStatus] = useState(analysis.human_review?.status || 'auto_cleared');
  const [loading, setLoading] = useState('');
  const runId = analysis.run_id || 'run_mock_preview';

  useEffect(() => {
    setDraft(analysis.report_markdown || '');
    setStatus(analysis.human_review?.status || 'auto_cleared');
  }, [analysis]);

  if (!isOpen) return null;

  async function submit(action) {
    setLoading(action);
    try {
      const payload = { reviewer: 'local-demo', comment, report_markdown: draft };
      const result =
        action === 'approve'
          ? await approveReview(runId, payload)
          : action === 'edit'
            ? await editReview(runId, payload)
            : await rejectReview(runId, payload);
      setStatus(result.status);
      onAnalysis?.({ ...analysis, report_markdown: draft, human_review: { ...(analysis.human_review || {}), status: result.status } });
    } catch {
      const fallbackStatus = action === 'approve' ? 'approved-local' : action === 'edit' ? 'edited-local' : 'rejected-local';
      setStatus(fallbackStatus);
      onAnalysis?.({ ...analysis, report_markdown: draft, human_review: { ...(analysis.human_review || {}), status: fallbackStatus } });
    } finally {
      setLoading('');
    }
  }

  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer" aria-label="Human review">
        <div className="section-title">
          <span>Human Review</span>
          <button className="icon-btn" onClick={onClose} title="Close review drawer">
            <X size={18} />
          </button>
        </div>

        <section className="metric-grid compact">
          <div className="metric-tile">
            <span>Run ID</span>
            <strong>{runId}</strong>
          </div>
          <div className="metric-tile amber">
            <span>Review status</span>
            <strong>{status}</strong>
          </div>
          <div className="metric-tile green">
            <span>Verifier confidence</span>
            <strong>{Number(analysis.verification_result?.confidence_score ?? 1).toFixed(2)}</strong>
          </div>
        </section>

        <label className="field-group drawer-field">
          <span>Review memo</span>
          <textarea
            className="review-textarea small"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="记录人工复核意见、证据补充或退回原因。"
          />
        </label>

        <label className="field-group drawer-field">
          <span>Report draft</span>
          <textarea className="review-textarea" value={draft} onChange={(event) => setDraft(event.target.value)} />
        </label>

        <section className="control-band review-actions">
          <button className="primary-btn" onClick={() => submit('approve')} disabled={Boolean(loading)}>
            {loading === 'approve' ? <Loader2 className="spin" size={18} /> : <CheckCircle2 size={18} />}
            Approve
          </button>
          <button className="primary-btn secondary" onClick={() => submit('edit')} disabled={Boolean(loading)}>
            {loading === 'edit' ? <Loader2 className="spin" size={18} /> : <Edit3 size={18} />}
            Save edit
          </button>
          <button className="primary-btn danger" onClick={() => submit('reject')} disabled={Boolean(loading)}>
            {loading === 'reject' ? <Loader2 className="spin" size={18} /> : <XCircle size={18} />}
            Reject
          </button>
        </section>
      </aside>
    </div>
  );
}
