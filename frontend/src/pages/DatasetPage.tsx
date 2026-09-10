import React, { useState } from 'react';
import { Database, Play, RefreshCw, CheckCircle } from 'lucide-react';
import { generateSyntheticSignal } from '../services/api';
import type { SignalAnalysisReport } from '../types/signal';

interface Props {
  onLoadReport: (report: SignalAnalysisReport) => void;
  setActiveTab: (tab: string) => void;
}

export const DatasetPage: React.FC<Props> = ({ onLoadReport, setActiveTab }) => {
  const [modulation, setModulation] = useState('QPSK');
  const [snrDb, setSnrDb] = useState(15);
  const [fecScheme, setFecScheme] = useState('Convolutional');
  const [interleaving, setInterleaving] = useState('16x16 Matrix');
  const sampleRate = 1000000;
  const [generating, setGenerating] = useState(false);
  const [training, setTraining] = useState(false);
  const [trainMsg, setTrainMsg] = useState<string | null>(null);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const report = await generateSyntheticSignal({
        modulation,
        snr_db: snrDb,
        fec_scheme: fecScheme,
        interleaving_pattern: interleaving,
        sample_rate: sampleRate
      });
      onLoadReport(report);
      setActiveTab('analyze');
    } catch (err) {
      alert('Failed to generate synthetic signal.');
    } finally {
      setGenerating(false);
    }
  };

  const handleRetrain = async () => {
    setTraining(true);
    setTrainMsg(null);
    try {
      const res = await fetch('http://localhost:8000/api/train', { method: 'POST' });
      const data = await res.json();
      setTrainMsg(data.message || 'Models retrained successfully.');
    } catch (err) {
      alert('Training failed.');
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <div className="border-b border-white/15 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Database className="h-6 w-6 text-white/80" /> Dataset Generator & Model Training
        </h1>
        <p className="text-xs text-white/60">
          Synthesize ground-truth RF signals with channel impairments and retrain multi-modal ML classifiers.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Synthetic Generator Panel */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
            Synthetic RF Signal Generator
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-white/70 block mb-1 font-mono">Modulation Scheme</label>
              <select
                value={modulation}
                onChange={e => setModulation(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/40 font-mono"
              >
                <option value="BPSK">BPSK</option>
                <option value="QPSK">QPSK</option>
                <option value="8PSK">8PSK</option>
                <option value="2FSK">2FSK</option>
                <option value="4FSK">4FSK</option>
                <option value="16QAM">16QAM</option>
                <option value="64QAM">64QAM</option>
                <option value="AM">AM</option>
                <option value="FM">FM</option>
              </select>
            </div>

            <div>
              <label className="text-white/70 block mb-1 font-mono">Channel SNR ({snrDb} dB)</label>
              <input
                type="range"
                min="0"
                max="30"
                value={snrDb}
                onChange={e => setSnrDb(parseInt(e.target.value))}
                className="w-full accent-white/50"
              />
            </div>

            <div>
              <label className="text-white/70 block mb-1 font-mono">FEC Scheme</label>
              <select
                value={fecScheme}
                onChange={e => setFecScheme(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/40"
              >
                <option value="None">None</option>
                <option value="Convolutional">Convolutional (1/2, K=7)</option>
                <option value="Reed-Solomon">Reed-Solomon (255, 223)</option>
                <option value="LDPC">LDPC</option>
                <option value="BCH">BCH</option>
              </select>
            </div>

            <div>
              <label className="text-white/70 block mb-1 font-mono">Interleaving Pattern</label>
              <select
                value={interleaving}
                onChange={e => setInterleaving(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/40"
              >
                <option value="None">None</option>
                <option value="16x16 Matrix">16x16 Matrix Interleaver</option>
                <option value="8x32 Block">8x32 Block Interleaver</option>
              </select>
            </div>

            <button
              disabled={generating}
              onClick={handleGenerate}
              className="w-full bg-white text-black hover:bg-white/90 font-semibold py-2.5 rounded-full flex items-center justify-center gap-2 shadow transition-colors disabled:opacity-50"
            >
              {generating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Synthesizing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-black" /> Generate & Analyze Signal
                </>
              )}
            </button>
          </div>
        </div>

        {/* Model Training Panel */}
        <div className="glass-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono mb-2">
              Multi-Modal Model Retraining
            </h3>
            <p className="text-xs text-white/60 leading-relaxed mb-4">
              Trigger background synthesis of 360 multi-class RF signal vectors across varying SNR levels (-5 dB to 30 dB) to retrain IQ-only, WAV-only, and Fused feature classifiers.
            </p>
          </div>

          <div className="space-y-3">
            {trainMsg && (
              <div className="bg-white/10 border border-white/20 text-white p-3 rounded-lg text-xs flex items-center gap-2">
                <CheckCircle className="h-4 w-4 shrink-0" />
                <span>{trainMsg}</span>
              </div>
            )}

            <button
              disabled={training}
              onClick={handleRetrain}
              className="w-full bg-white text-black hover:bg-white/90 font-semibold py-2.5 rounded-full flex items-center justify-center gap-2 shadow transition-colors disabled:opacity-50"
            >
              {training ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Retraining ML Engine...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" /> Retrain Modulation Classifiers
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
