import type { SignalAnalysisReport, HistoryRecord } from '../types/signal';

const API_BASE = 'http://localhost:8000/api';

export async function analyzeSignalFiles(
  iqFile: File | null,
  wavFile: File | null,
  datatype: string = 'auto',
  sampleRateOverride?: number,
  sigmfMetaFile?: File | null
): Promise<SignalAnalysisReport> {
  const formData = new FormData();
  if (iqFile) formData.append('iq_file', iqFile);
  if (wavFile) formData.append('wav_file', wavFile);
  if (sigmfMetaFile) formData.append('sigmf_meta_file', sigmfMetaFile);
  formData.append('datatype', datatype);
  if (sampleRateOverride) {
    formData.append('sample_rate_override', sampleRateOverride.toString());
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(err.detail || 'Failed to analyze signal file.');
  }

  return res.json();
}

export async function generateSyntheticSignal(params: {
  modulation: string;
  snr_db: number;
  fec_scheme: string;
  interleaving_pattern: string;
  sample_rate: number;
}): Promise<SignalAnalysisReport> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    throw new Error('Failed to generate synthetic signal.');
  }

  return res.json();
}

export async function fetchAnalysisHistory(): Promise<HistoryRecord[]> {
  const res = await fetch(`${API_BASE}/history`);
  if (!res.ok) throw new Error('Failed to fetch analysis history.');
  return res.json();
}

export async function fetchHistoryDetail(id: number): Promise<SignalAnalysisReport> {
  const res = await fetch(`${API_BASE}/history/${id}`);
  if (!res.ok) throw new Error('Failed to fetch analysis report detail.');
  const data = await res.json();
  return data.report_json;
}

export async function fetchModelStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/model/status`);
  if (!res.ok) throw new Error('Failed to fetch model status.');
  return res.json();
}

export async function fetchModelMetrics(): Promise<any> {
  const res = await fetch(`${API_BASE}/model/metrics`);
  if (!res.ok) throw new Error('Failed to fetch model metrics.');
  return res.json();
}

export async function exportReportPDF(reportData: SignalAnalysisReport): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reportData),
  });
  if (!res.ok) throw new Error('Failed to generate PDF report.');
  return res.blob();
}
