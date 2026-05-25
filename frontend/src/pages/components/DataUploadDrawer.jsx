import { FileSpreadsheet, UploadCloud, X } from 'lucide-react';
import { useMemo, useState } from 'react';

import {
  DATASET_SCOPES,
  allowedSchemasForScope,
  autoMapColumns,
  inferSchema,
  qualityReport,
  saveUpload
} from '../../sessionDataStore.js';

function readFileAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsText(file, 'utf-8');
  });
}

function normalizeRows(rows) {
  return rows.filter((row) => Object.values(row || {}).some((value) => value !== null && value !== undefined && String(value).trim() !== ''));
}

async function parseFile(file) {
  const lower = file.name.toLowerCase();
  if (lower.endsWith('.csv')) {
    const Papa = (await import('papaparse')).default;
    const text = await readFileAsText(file);
    const result = Papa.parse(text, { header: true, skipEmptyLines: true });
    const rows = normalizeRows(result.data || []);
    return {
      parser_status: result.errors?.length ? 'parsed_with_warnings' : 'parsed',
      file_type: 'csv',
      sheets: [{ name: 'CSV', rows }],
      warnings: result.errors || []
    };
  }
  if (lower.endsWith('.xlsx') || lower.endsWith('.xls')) {
    const XLSX = await import('xlsx');
    const buffer = await readFileAsArrayBuffer(file);
    const workbook = XLSX.read(buffer, { type: 'array', cellDates: false });
    const sheets = workbook.SheetNames.map((name) => ({
      name,
      rows: normalizeRows(XLSX.utils.sheet_to_json(workbook.Sheets[name], { defval: '' }))
    }));
    return { parser_status: 'parsed', file_type: 'xlsx', sheets, warnings: [] };
  }
  if (lower.endsWith('.pptx')) {
    return { parser_status: 'unsupported_or_optional', file_type: 'pptx', sheets: [], warnings: ['PPTX 仅保留后端可选解析接口。'] };
  }
  return { parser_status: 'unsupported_or_optional', file_type: lower.split('.').pop() || 'unknown', sheets: [], warnings: ['当前前端 demo 仅支持 CSV/XLSX。'] };
}

function FieldMapping({ mapping }) {
  const rows = Object.entries(mapping || {});
  return (
    <div className="mapping-grid">
      {rows.map(([target, source]) => (
        <div key={target}>
          <span>{target}</span>
          <strong>{source}</strong>
        </div>
      ))}
      {!rows.length ? <p className="panel-copy">未识别到可映射字段，请检查表头。</p> : null}
    </div>
  );
}

export default function DataUploadDrawer({ isOpen, onClose, onImported }) {
  const [fileState, setFileState] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState('');
  const [datasetScope, setDatasetScope] = useState('');
  const [schemaOverride, setSchemaOverride] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const activeSheet = useMemo(() => {
    if (!fileState?.sheets?.length) return null;
    return fileState.sheets.find((sheet) => sheet.name === selectedSheet) || fileState.sheets[0];
  }, [fileState, selectedSheet]);

  const columns = useMemo(() => Object.keys(activeSheet?.rows?.[0] || {}), [activeSheet]);
  const detectedSchema = useMemo(() => inferSchema(columns, datasetScope), [columns, datasetScope]);
  const allowedSchemas = useMemo(() => allowedSchemasForScope(datasetScope), [datasetScope]);
  const schema = schemaOverride || (allowedSchemas.includes(detectedSchema) ? detectedSchema : allowedSchemas[0] || detectedSchema);
  const mapping = useMemo(() => autoMapColumns(columns), [columns]);
  const report = useMemo(() => qualityReport(activeSheet?.rows || [], schema, mapping, datasetScope), [activeSheet, schema, mapping, datasetScope]);

  async function handleFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const parsed = await parseFile(file);
    setFileState({ ...parsed, file_name: file.name });
    setSelectedSheet(parsed.sheets?.[0]?.name || '');
    setSchemaOverride('');
    setError('');
  }

  function confirmImport() {
    if (!datasetScope) {
      setError('请先选择 dataset_scope。');
      return;
    }
    if (!activeSheet?.rows?.length) return;
    setSaving(true);
    try {
      const result = saveUpload({ fileName: fileState.file_name, schema, rows: activeSheet.rows, mapping, datasetScope });
      onImported?.(result);
      onClose?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '导入失败');
    } finally {
      setSaving(false);
    }
  }

  if (!isOpen) return null;
  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer product-drawer" aria-label="导入周报和净值数据">
        <div className="section-title">
          <span>导入周报/净值/同业/利率数据</span>
          <button className="icon-btn" onClick={onClose} title="关闭导入">
            <X size={18} />
          </button>
        </div>
        <section className="panel">
          <div className="section-title">
            <span>dataset_scope</span>
            <strong>必选</strong>
          </div>
          <div className="scope-selector-grid">
            {Object.entries(DATASET_SCOPES).map(([scope, config]) => (
              <button
                type="button"
                key={scope}
                className={`scope-card ${datasetScope === scope ? 'active' : ''}`}
                onClick={() => {
                  setDatasetScope(scope);
                  setSchemaOverride('');
                }}
              >
                <strong>{scope}</strong>
                <span>{config.label}</span>
              </button>
            ))}
          </div>
        </section>
        <section className="upload-dropzone">
          <UploadCloud size={24} />
          <div>
            <strong>选择 CSV 或 XLSX 文件</strong>
            <p>Vercel demo 默认仅在浏览器本地解析并写入 localStorage，不上传真实内部或敏感数据。每条记录会生成 upload_id、dataset_scope、source_type=manual_upload 和 evidence_id。</p>
          </div>
          <input type="file" accept=".csv,.xlsx,.xls,.pptx" onChange={handleFile} />
        </section>
        {error ? <div className="inline-alert">{error}</div> : null}
        {fileState ? (
          <div className="page-stack nested-stack">
            <section className="split-grid">
              <div className="panel">
                <div className="section-title">
                  <span>文件概览</span>
                  <strong>{fileState.parser_status}</strong>
                </div>
                <div className="two-column-facts">
                  <div><span>文件名</span><strong>{fileState.file_name}</strong></div>
                  <div><span>类型</span><strong>{fileState.file_type}</strong></div>
                  <div><span>识别 schema</span><strong>{schema}</strong></div>
                  <div><span>样例行</span><strong>{activeSheet?.rows?.length || 0}</strong></div>
                </div>
              </div>
              <div className="panel">
                <div className="section-title">
                  <span>Sheet / Schema</span>
                  <strong>{fileState.sheets?.length || 0}</strong>
                </div>
                <label className="field-group">
                  <span>选择 sheet</span>
                  <select value={selectedSheet} onChange={(event) => setSelectedSheet(event.target.value)}>
                    {(fileState.sheets || []).map((sheet) => (
                      <option key={sheet.name} value={sheet.name}>{sheet.name}</option>
                    ))}
                  </select>
                </label>
                <label className="field-group">
                  <span>目标 schema</span>
                  <select value={schema} onChange={(event) => setSchemaOverride(event.target.value)} disabled={!datasetScope}>
                    {(allowedSchemas.length ? allowedSchemas : [schema]).map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>
              </div>
            </section>
            <section className="panel">
              <div className="section-title">
                <span>自动字段映射</span>
                <strong>{Object.keys(mapping).length} 个字段</strong>
              </div>
              <FieldMapping mapping={mapping} />
            </section>
            <section className="panel">
              <div className="section-title">
                <span>数据质量检查</span>
                <strong>{report.parser_status}</strong>
              </div>
              <div className="two-column-facts">
                <div><span>scope / schema 是否匹配</span><strong>{report.scope_valid ? '通过' : '需调整'}</strong></div>
                <div><span>缺少必需字段</span><strong>{report.missing_required_fields.join(', ') || '无'}</strong></div>
                <div><span>日期格式错误</span><strong>{report.bad_date_count}</strong></div>
                <div><span>重复键</span><strong>{report.duplicate_key_count}</strong></div>
                <div><span>数值缺失率</span><strong>{Object.keys(report.numeric_missing_rate).length} 项</strong></div>
              </div>
            </section>
            <section className="table-panel compact-table">
              <div className="section-title table-title">
                <span>前 20 行预览</span>
                <strong>{columns.length} 列</strong>
              </div>
              <table>
                <thead>
                  <tr>{columns.slice(0, 8).map((column) => <th key={column}>{column}</th>)}</tr>
                </thead>
                <tbody>
                  {(activeSheet?.rows || []).slice(0, 20).map((row, index) => (
                    <tr key={`${index}-${fileState.file_name}`}>
                      {columns.slice(0, 8).map((column) => <td key={column}>{String(row[column] ?? '')}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <button className="primary-btn" onClick={confirmImport} disabled={saving || !datasetScope || report.missing_required_fields.length > 0 || !report.scope_valid}>
              <FileSpreadsheet size={18} />
              确认导入并刷新工作台
            </button>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
