import React from 'react';
import { Info, Shield, Radio, Code2 } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="space-y-8 pb-16 max-w-4xl mx-auto">
      <div className="border-b border-white/15 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Info className="h-6 w-6 text-white/80" /> About SIGNALFUSION
        </h1>
        <p className="text-xs text-white/60">
          Smart India Hackathon 2026 Problem Statement 26147 Prototype Details.
        </p>
      </div>

      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center text-white">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">National Technical Research Organisation (NTRO)</h2>
            <p className="text-xs text-white/60">Category: Software | Theme: Space Technology | Problem Statement 26147</p>
          </div>
        </div>

        <div className="space-y-2 text-xs text-white/80 leading-relaxed pt-2 border-t border-white/15">
          <h3 className="font-bold text-white uppercase font-mono">Problem Statement Title:</h3>
          <p className="bg-white/5 p-3 rounded border border-white/15 font-mono text-white">
            &ldquo;Automated model for analysis of .IQ and .wav files along with signal parameter extraction&rdquo;
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 space-y-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <Radio className="h-4 w-4 text-white/80" /> Core Objectives
          </h3>
          <ul className="text-xs text-white/80 space-y-2 list-disc list-inside">
            <li>Extract key parameters: Sampling rate, Modulation type, FEC scheme, Interleaving pattern.</li>
            <li>Calculate DSP characteristics: SNR, 99% occupied bandwidth, peak frequency, spectral entropy, higher-order cumulants.</li>
            <li>Explicitly distinguish parameter sources (Metadata vs DSP vs ML vs Pending).</li>
            <li>Multi-modal feature fusion for paired binary `.IQ` and stereo `.WAV` recordings.</li>
          </ul>
        </div>

        <div className="glass-card p-6 space-y-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <Code2 className="h-4 w-4 text-white/80" /> Technology Stack
          </h3>
          <div className="text-xs text-white/80 space-y-1.5 font-mono">
            <p><b className="text-white">Backend:</b> Python, FastAPI, NumPy, SciPy, PyTorch, scikit-learn</p>
            <p><b className="text-white">Frontend:</b> React 18, Vite, TypeScript, Tailwind CSS, Plotly.js</p>
            <p><b className="text-white">Database:</b> SQLite history database</p>
            <p><b className="text-white">Export:</b> ReportLab PDF & JSON exporter</p>
          </div>
        </div>
      </div>
    </div>
  );
};
