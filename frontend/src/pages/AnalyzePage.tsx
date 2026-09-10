import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, Download, AlertCircle, RefreshCw, Cpu, Layers, Sparkles, Radio } from 'lucide-react';
import { analyzeSignalFiles, exportReportPDF } from '../services/api';
import type { SignalAnalysisReport } from '../types/signal';
import { TimeDomainChart } from '../charts/TimeDomainChart';
import { FreqSpectrumChart } from '../charts/FreqSpectrumChart';
import { SpectrogramChart } from '../charts/SpectrogramChart';
import { ConstellationChart } from '../charts/ConstellationChart';

interface Props {
  currentReport: SignalAnalysisReport | null;
  setCurrentReport: (report: SignalAnalysisReport | null) => void;
  isLoading: boolean;
  setIsLoading: (val: boolean) => void;
}

interface SigmfPreflight {
  datatype: string;
  sampleRate: number;
  centerFrequency: number | null;
  sampleCount: number | null;
  metadataSource: string;
}

export const AnalyzePage: React.FC<Props> = ({ currentReport, setCurrentReport, isLoading, setIsLoading }) => {
  const [iqFile, setIqFile] = useState<File | null>(null);
  const [sigmfMetaFile, setSigmfMetaFile] = useState<File | null>(null);
  const [sigmfPreflight, setSigmfPreflight] = useState<SigmfPreflight | null>(null);
  const [wavFile, setWavFile] = useState<File | null>(null);
  const [datatype, setDatatype] = useState<string>('auto');
  const [sampleRateOverride, setSampleRateOverride] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const readSigmfPreflight = async (dataFile: File, metaFile: File) => {
    try {
      const metadata = JSON.parse(await metaFile.text());
      const global = metadata.global ?? {};
      const captures = metadata.captures ?? [];
      const datatype = global['core:datatype'];
      const sampleRate = Number(global['core:sample_rate']);
      const centerFrequency = captures[0]?.['core:frequency'] ?? global['core:frequency'] ?? null;
      const bytesPerSample = datatype === 'cf32_le' ? 8 : null;
      if (!datatype || !Number.isFinite(sampleRate) || sampleRate <= 0) {
        throw new Error('The SigMF metadata must provide a valid core:datatype and core:sample_rate.');
      }
      setSigmfPreflight({
        datatype,
        sampleRate,
        centerFrequency: centerFrequency === null ? null : Number(centerFrequency),
        sampleCount: bytesPerSample ? Math.floor(dataFile.size / bytesPerSample) : null,
        metadataSource: 'SigMF Metadata',
      });
    } catch (err: any) {
      setSigmfPreflight(null);
      setErrorMsg(err.message || 'Could not parse the selected SigMF metadata file.');
    }
  };

  const handleFileSelection = (files: FileList | null) => {
    if (!files) return;
    const selected = Array.from(files);
    const dataFile = selected.find(file => file.name.toLowerCase().endsWith('.sigmf-data'));
    const metaFile = selected.find(file => file.name.toLowerCase().endsWith('.sigmf-meta'));
    const rawIqFile = selected.find(file => !file.name.toLowerCase().endsWith('.sigmf-meta'));
    if (dataFile && !metaFile) {
      setIqFile(dataFile);
      setSigmfMetaFile(null);
      setSigmfPreflight(null);
      setErrorMsg('SigMF data requires the matching .sigmf-meta file. Select both files together in the SigMF pair picker.');
      return;
    }
    if (!rawIqFile) return;
    if (!dataFile) {
      setIqFile(rawIqFile);
      setSigmfMetaFile(null);
      setSigmfPreflight(null);
      setErrorMsg(null);
      return;
    }
    if (!metaFile) return;
    setIqFile(dataFile);
    setSigmfMetaFile(metaFile);
    void readSigmfPreflight(dataFile, metaFile);
    setErrorMsg(null);
  };

  const handleAnalyze = async () => {
    if (!iqFile && !wavFile) {
      setErrorMsg('Please select at least one .iq or .wav file to analyze.');
      return;
    }
    if (iqFile?.name.toLowerCase().endsWith('.sigmf-data') && !sigmfMetaFile) {
      setErrorMsg('Select the matching .sigmf-meta file before analyzing this SigMF recording.');
      return;
    }

    setErrorMsg(null);
    setIsLoading(true);

    try {
      const srNum = sampleRateOverride ? parseFloat(sampleRateOverride) : undefined;
      const report = await analyzeSignalFiles(iqFile, wavFile, datatype, srNum, sigmfMetaFile);
      setCurrentReport(report);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error occurred during signal processing.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!currentReport) return;
    try {
      const blob = await exportReportPDF(currentReport);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentReport.metadata.filename}_report.pdf`;
      a.click();
    } catch (err) {
      alert('Failed to export PDF report.');
    }
  };

  const handleExportJSON = () => {
    if (!currentReport) return;
    const jsonStr = JSON.stringify(currentReport, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentReport.metadata.filename}_report.json`;
    a.click();
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/15 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-300 tracking-tight flex items-center gap-3">
            <Radio className="h-8 w-8 text-white/80" />
            Signal Analysis & Feature Extraction
          </h1>
          <p className="text-sm text-white/60 mt-2">
            Ingest .IQ, .WAV, or paired SigMF recordings • Extract DSP features • Infer modulation & channel parameters
          </p>
        </div>

        {currentReport && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleExportPDF}
              className="bg-gradient-to-r from-white/90 to-blue-600 hover:from-white/80 hover:to-blue-500 text-white text-xs px-4 py-2.5 rounded-lg font-semibold shadow-lg shadow-white/10 flex items-center gap-2 transition-all hover:scale-105 group"
            >
              <Download className="h-4 w-4 group-hover:rotate-12 transition-transform" /> Export PDF Report
            </button>
            <button
              onClick={handleExportJSON}
              className="bg-gradient-to-r from-white/10 to-white/10 hover:from-white/15 hover:to-white/10 text-white hover:text-white border border-white/20 hover:border-white/40 text-xs px-4 py-2.5 rounded-lg font-semibold flex items-center gap-2 transition-all backdrop-blur-sm hover:scale-105 group"
            >
              <FileText className="h-4 w-4" /> Export JSON
            </button>
          </div>
        )}
      </div>

      {/* Upload Zone & Config Controls */}
      <div className="glass-card space-y-6">
        <h3 className="text-xs font-bold text-white/80 uppercase tracking-widest font-mono flex items-center gap-2.5">
          <Upload className="h-5 w-5 text-white/80 animate-pulse" /> UPLOAD SIGNAL FILES
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* IQ File Dropzone */}
          <div className="group relative border-2 border-dashed border-white/30 hover:border-white/70 rounded-xl p-5 text-center transition-all duration-300 bg-gradient-to-br from-white/5 to-blue-500/5 hover:from-white/10 hover:to-blue-500/10 cursor-pointer">
            <input
              type="file"
              accept=".iq,.raw,.bin,.sigmf-data,.sigmf-meta,application/json"
              id="iq-upload"
              multiple
              className="hidden"
              onChange={e => handleFileSelection(e.target.files)}
            />
            <label htmlFor="iq-upload" className="cursor-pointer space-y-3 block group-hover:scale-105 transition-transform origin-center">
              <FileText className="h-10 w-10 mx-auto text-white/80 opacity-70 group-hover:opacity-100 transition-opacity" />
              <div>
                <span className="text-xs font-bold text-white block">
                  {iqFile ? iqFile.name : 'IQ Signal Data'}
                </span>
                <span className="text-[11px] text-white/50 block mt-1">
                  {iqFile ? `${(iqFile.size / 1024).toFixed(1)} KB • complex64 / int16` : 'Raw binary complex signal'}
                </span>
              </div>
            </label>
            {iqFile && (
              <button
                onClick={() => { setIqFile(null); setSigmfMetaFile(null); setSigmfPreflight(null); }}
                className="mt-3 text-[11px] text-red-400 hover:text-red-300 font-semibold transition-colors"
              >
                × Remove
              </button>
            )}
          </div>

          {/* SigMF Pair Dropzone */}
          <div className="group relative border-2 border-dashed border-amber-500/30 hover:border-amber-500/70 rounded-xl p-5 text-center transition-all duration-300 bg-gradient-to-br from-amber-500/5 to-orange-500/5 hover:from-amber-500/10 hover:to-orange-500/10 cursor-pointer">
            <input
              type="file"
              accept=".sigmf-data,.sigmf-meta,application/json"
              id="sigmf-pair-upload"
              multiple
              className="hidden"
              onChange={e => handleFileSelection(e.target.files)}
            />
            <label htmlFor="sigmf-pair-upload" className="cursor-pointer space-y-3 block group-hover:scale-105 transition-transform origin-center">
              <FileText className="h-10 w-10 mx-auto text-white opacity-70 group-hover:opacity-100 transition-opacity" />
              <div>
                <span className="text-xs font-bold text-white block">
                  {sigmfMetaFile ? `${sigmfMetaFile.name}` : 'SigMF Pair'}
                </span>
                <span className="text-[11px] text-white/50 block mt-1">
                  {sigmfMetaFile ? 'Paired metadata ready' : '.sigmf-data + .sigmf-meta'}
                </span>
              </div>
            </label>
            {sigmfMetaFile && (
              <button onClick={() => setSigmfMetaFile(null)} className="mt-3 text-[11px] text-red-400 hover:text-red-300 font-semibold transition-colors">
                × Remove
              </button>
            )}
          </div>

          {/* WAV File Dropzone */}
          <div className="group relative border-2 border-dashed border-pink-500/30 hover:border-pink-500/70 rounded-xl p-5 text-center transition-all duration-300 bg-gradient-to-br from-pink-500/5 to-rose-500/5 hover:from-pink-500/10 hover:to-rose-500/10 cursor-pointer">
            <input
              type="file"
              accept=".wav"
              id="wav-upload"
              className="hidden"
              onChange={e => e.target.files?.[0] && setWavFile(e.target.files[0])}
            />
            <label htmlFor="wav-upload" className="cursor-pointer space-y-3 block group-hover:scale-105 transition-transform origin-center">
              <FileText className="h-10 w-10 mx-auto text-white opacity-70 group-hover:opacity-100 transition-opacity" />
              <div>
                <span className="text-xs font-bold text-white block">
                  {wavFile ? wavFile.name : 'WAV Audio/IQ'}
                </span>
                <span className="text-[11px] text-white/50 block mt-1">
                  {wavFile ? `${(wavFile.size / 1024).toFixed(1)} KB` : 'Stereo IQ or mono audio'}
                </span>
              </div>
            </label>
            {wavFile && (
              <button
                onClick={() => setWavFile(null)}
                className="mt-2 text-[11px] text-red-400 hover:underline"
              >
                Remove
              </button>
            )}
          </div>
        </div>

        {sigmfPreflight && (
          <div className="rounded-xl border border-amber-700/70 bg-amber-950/20 p-4 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider font-mono text-white">SigMF Metadata Validation — before inference</div>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
              <div><span className="text-white/50 block">Data type</span><b className="font-mono text-white">{sigmfPreflight.datatype}</b></div>
              <div><span className="text-white/50 block">Sample rate</span><b className="font-mono text-white">{(sigmfPreflight.sampleRate / 1e6).toFixed(3)} MS/s</b></div>
              <div><span className="text-white/50 block">Center frequency</span><b className="font-mono text-white">{sigmfPreflight.centerFrequency === null ? 'Not available' : `${(sigmfPreflight.centerFrequency / 1e6).toFixed(5)} MHz`}</b></div>
              <div><span className="text-white/50 block">Sample count</span><b className="font-mono text-white">{sigmfPreflight.sampleCount?.toLocaleString() ?? 'Calculated by parser'}</b></div>
              <div><span className="text-white/50 block">Source</span><b className="font-mono text-white">{sigmfPreflight.metadataSource}</b></div>
            </div>
          </div>
        )}

        {/* Configuration Options */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 text-xs">
          <div>
            <label className="text-white/60 block mb-1 font-mono">IQ DataType Parser</label>
            <select
              value={datatype}
              onChange={e => setDatatype(e.target.value)}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/40"
            >
              <option value="auto">Auto-detect</option>
              <option value="complex64">complex64 (float32 I/Q)</option>
              <option value="complex128">complex128 (float64 I/Q)</option>
              <option value="int16">int16 interleaved I/Q</option>
              <option value="float32">float32 interleaved I/Q</option>
            </select>
          </div>

          <div>
            <label className="text-white/60 block mb-1 font-mono">Sampling Rate Override (Hz)</label>
            <input
              type="number"
              placeholder="e.g. 1000000 for 1 MS/s"
              value={sampleRateOverride}
              onChange={e => setSampleRateOverride(e.target.value)}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/40"
            />
          </div>

          <div className="flex items-end">
            <button
              disabled={isLoading || (!iqFile && !wavFile)}
              onClick={handleAnalyze}
              className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 shadow transition-colors"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Processing Signal...
                </>
              ) : (
                <>
                  <Cpu className="h-4 w-4" /> Run Analysis Pipeline
                </>
              )}
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="bg-red-950/60 border border-red-800 text-red-300 p-3 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {currentReport && (
        <div className="space-y-8 animate-fadeIn">
          {/* Signal Overview Banner */}
          <div className="glass-card p-4 flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-white/950/40 border-white/900/60">
            <div className="space-y-1">
              <span className="text-[10px] text-white/80 font-mono uppercase tracking-wider">
                Analysis Complete ({currentReport.processing_time_ms.toFixed(1)} ms)
              </span>
              <h2 className="text-lg font-bold text-white font-mono">
                {currentReport.metadata.filename}
              </h2>
              <div className="flex flex-wrap items-center gap-3 text-xs text-white/80">
                <span>Format: <b>{currentReport.metadata.format}</b></span>
                <span>Samples: <b>{currentReport.metadata.sample_count.toLocaleString()}</b></span>
                <span>Duration: <b>{currentReport.metadata.duration_seconds.toFixed(4)} s</b></span>
                <span>Sample Rate: <b>{(currentReport.metadata.sample_rate / 1e6).toFixed(3)} MS/s</b></span>
                <span>Data Type: <b>{currentReport.metadata.datatype}</b></span>
                {currentReport.metadata.center_frequency !== null && <span>Center: <b>{(currentReport.metadata.center_frequency / 1e6).toFixed(6)} MHz</b></span>}
                <span>Metadata: <b>{currentReport.metadata.metadata_source}</b></span>
              </div>
            </div>

            <div className="bg-white/10/80 border border-white/20/80 p-3 rounded-lg text-right">
              <span className="text-[10px] text-white/60 uppercase font-mono block">Inferred Modulation</span>
              <span className="text-xl font-bold text-white font-mono">
                {currentReport.modulation_prediction.prediction}
              </span>
              <span className="text-xs text-white/80 block font-mono">
                {currentReport.modulation_prediction.confidence_label ?? `${currentReport.modulation_prediction.confidence}% model score`}
              </span>
            </div>
          </div>

          <div className={`glass-card p-5 space-y-3 ${currentReport.conflicting_evidence ? 'border-amber-600/70' : ''}`}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">Analysis Evidence</h3>
              <span className={`text-xs font-mono px-2 py-1 rounded ${currentReport.conflicting_evidence ? 'bg-amber-950 text-white border border-amber-800' : 'bg-emerald-950 text-white border border-emerald-800'}`}>
                {currentReport.conflicting_evidence ? 'Conflicting evidence — review candidates' : 'Evidence consistent'}
              </span>
            </div>
            <p className="text-xs text-white/60">The prediction is based on measured signal features. No filename, description, or unannotated SigMF field is used as a label.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {currentReport.analysis_evidence.map((evidence, index) => (
                <div key={index} className="bg-white/10 border border-white/15 rounded-lg p-3 text-xs space-y-1">
                  <span className="font-semibold text-white/80 block">{evidence.feature}</span>
                  <span className="font-mono text-white block">{evidence.value}</span>
                  <span className="text-white/60 block">{evidence.interpretation}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Plotly Analytics Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TimeDomainChart chartData={currentReport.time_domain.chart_data} />
            <FreqSpectrumChart
              chartData={currentReport.freq_domain.chart_data}
              characteristics={currentReport.freq_domain.characteristics}
            />
            <SpectrogramChart data={currentReport.spectrogram} />
            <ConstellationChart data={currentReport.constellation} />
          </div>

          {/* Parameter Extraction Table (Honest Source & Ground Truth Comparison) */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-white" /> Extracted Parameter Profile & Origin
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/10 text-white/60 uppercase font-mono text-[10px] border-b border-white/15">
                  <tr>
                    <th className="p-3">Parameter</th>
                    <th className="p-3">Inferred Result</th>
                    <th className="p-3">Source / Method</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Ground Truth (Demo Mode)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-white/80">
                  {currentReport.parameter_table.map((row, idx) => (
                    <tr key={idx} className="hover:bg-white/20/40">
                      <td className="p-3 font-semibold text-white">{row.parameter}</td>
                      <td className="p-3 font-mono text-white/80 font-bold">{row.result}</td>
                      <td className="p-3">{row.source}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
                          row.confidence.includes('Low') || row.confidence.includes('32%')
                            ? 'bg-amber-950 text-white border border-amber-800'
                            : 'bg-emerald-950 text-white border border-emerald-800'
                        }`}>
                          {row.confidence}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-white">{row.ground_truth}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cross-Format Feature Fusion View (For Paired IQ+WAV) */}
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/20 pb-3">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Layers className="h-4 w-4 text-white/80" /> Multi-Modal ML Modulation Classification
              </h3>
              <span className="text-xs bg-white/10 text-white/80 border border-white/800 px-2.5 py-1 rounded font-mono font-medium">
                Active Mode: {currentReport.inference_mode}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/10 p-4 rounded-xl border border-white/15 space-y-1">
                <span className="text-[10px] text-white/60 uppercase font-mono block">IQ-Only Model</span>
                <span className="text-lg font-bold text-white/80 font-mono">
                  {currentReport.modulation_prediction.mode_comparisons.iq_only}
                </span>
                <p className="text-[11px] text-white/50">Extracted from raw binary IQ complex stream</p>
              </div>

              <div className="bg-white/10 p-4 rounded-xl border border-white/15 space-y-1">
                <span className="text-[10px] text-white/60 uppercase font-mono block">WAV-Only Model</span>
                <span className="text-lg font-bold text-white font-mono">
                  {currentReport.modulation_prediction.mode_comparisons.wav_only}
                </span>
                <p className="text-[11px] text-white/50">Extracted from stereo WAV audio container</p>
              </div>

              <div className="bg-gradient-to-br from-white/10 to-white/10 p-4 rounded-xl border border-white/20 space-y-1 shadow-lg">
                <span className="text-[10px] text-white/80 uppercase font-mono font-bold block flex items-center gap-1">
                  <Sparkles className="h-3 w-3" /> Fused IQ+WAV Prediction
                </span>
                <span className="text-xl font-bold text-white font-mono">
                  {currentReport.modulation_prediction.prediction}
                </span>
                <p className="text-[11px] text-white/80 font-mono">
                  {currentReport.modulation_prediction.confidence_label ?? `${currentReport.modulation_prediction.confidence}% model score`}
                </p>
              </div>
            </div>

            {/* Candidate Probabilities */}
            <div className="space-y-2 pt-2">
              <span className="text-xs text-white/60 uppercase font-mono block">Top-3 Modulation Candidates</span>
              <div className="space-y-1.5">
                {currentReport.modulation_prediction.candidates.map((cand, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-xs">
                    <span className="w-16 font-mono font-bold text-white/80">{cand.modulation}</span>
                    <div className="flex-1 bg-white/10 h-2.5 rounded-full overflow-hidden border border-white/15">
                      <div
                        className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${cand.confidence_pct}%` }}
                      ></div>
                    </div>
                    <span className="w-12 text-right font-mono text-white/60">{cand.confidence_pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Advanced FEC & Interleaving Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* FEC Card */}
            <div className="glass-card p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-white/20 pb-2">
                <h4 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  FEC Scheme Detection
                </h4>
                <span className="text-xs font-bold text-white/80 font-mono">
                  {currentReport.fec_detection.confidence_pct}%
                </span>
              </div>
              <div>
                <span className="text-lg font-bold text-white font-mono block">
                  {currentReport.fec_detection.result}
                </span>
                <span className="text-xs text-white/60 block">{currentReport.fec_detection.status}</span>
              </div>
              <div className="space-y-1 pt-2">
                <span className="text-[10px] text-white/60 uppercase font-mono block">Evidence Used:</span>
                {currentReport.fec_detection.evidence_used.map((ev, i) => (
                  <p key={i} className="text-[11px] text-white/80">• {ev}</p>
                ))}
              </div>
            </div>

            {/* Interleaving Card */}
            <div className="glass-card p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-white/20 pb-2">
                <h4 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  Interleaving Pattern
                </h4>
                <span className="text-xs font-bold text-white/80 font-mono">
                  {currentReport.interleaving_detection.confidence_pct}%
                </span>
              </div>
              <div>
                <span className="text-lg font-bold text-white font-mono block">
                  {currentReport.interleaving_detection.result}
                </span>
                <span className="text-xs text-white/60 block">{currentReport.interleaving_detection.status}</span>
              </div>
              <div className="space-y-1 pt-2">
                <span className="text-[10px] text-white/60 uppercase font-mono block">Evidence Used:</span>
                {currentReport.interleaving_detection.evidence_used.map((ev, i) => (
                  <p key={i} className="text-[11px] text-white/80">• {ev}</p>
                ))}
              </div>
            </div>
          </div>

          {/* Explainability & Supporting Evidence */}
          <div className="glass-card p-6 space-y-3">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
              Analyst Supporting Evidence Checklist
            </h3>
            <div className="space-y-2">
              {currentReport.explainability_evidence.map((ev, idx) => (
                <div key={idx} className="bg-white/10 p-3 rounded-lg border border-white/15 text-xs flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-white shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-white">{ev.check}: </span>
                    <span className="text-white/80">{ev.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
