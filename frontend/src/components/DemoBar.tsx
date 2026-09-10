import React from 'react';
import { Play, Sparkles, Zap, Radio } from 'lucide-react';

interface Props {
  onSelectDemo: (demoId: string) => void;
  isLoading: boolean;
}

export const DemoBar: React.FC<Props> = ({ onSelectDemo, isLoading }) => {
  const demos = [
    { id: 'QPSK', label: 'Demo 1 — QPSK', desc: 'Digital Phase Modulation' },
    { id: 'BPSK', label: 'Demo 2 — BPSK', desc: 'Binary Phase Shift' },
    { id: '16QAM', label: 'Demo 3 — 16QAM', desc: 'Quadrature Amplitude' },
    { id: '2FSK', label: 'Demo 4 — 2FSK', desc: 'Frequency Shift Keying' },
    { id: 'PAIRED', label: 'Demo 5 — Paired IQ + WAV', desc: 'Multi-Modal Fusion' },
  ];

  return (
    <div className="backdrop-blur-xl bg-black/40 border-b border-white/15 shadow-lg py-3 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-white/60" />
            <Zap className="h-3.5 w-3.5 text-white/50" />
          </div>
          <span className="font-semibold text-xs tracking-widest uppercase text-white/70 font-mono">
            SIH Presentation Demo Mode — Pre-Generated Test Signals
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {demos.map((demo, idx) => (
            <button
              key={demo.id}
              disabled={isLoading}
              onClick={() => onSelectDemo(demo.id)}
              className="group relative bg-white/10 hover:bg-white/15 border border-white/20 hover:border-white/40 text-white/80 hover:text-white text-xs px-3 py-1.5 rounded-full transition-all duration-200 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-white/10"
            >
              <Play className="h-3 w-3 text-white/70 fill-white/70 group-hover:rotate-12 transition-transform" />
              <span className="font-semibold">{demo.label}</span>
              {idx === demos.length - 1 && (
                <Radio className="h-2.5 w-2.5 text-white/60 animate-pulse ml-1" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
