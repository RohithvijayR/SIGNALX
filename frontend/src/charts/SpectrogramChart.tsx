import React from 'react';
import Plot from 'react-plotly.js';
import type { SpectrogramData } from '../types/signal';

interface Props {
  data: SpectrogramData;
}

export const SpectrogramChart: React.FC<Props> = ({ data }) => {
  const freqKHz = data.freq.map(f => f / 1000);

  return (
    <div className="glass-card flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-2">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400"></span> STFT Spectrogram Heatmap
        </h3>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
            NFFT: {data.params.nfft}
          </span>
          <span className="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
            Window: {data.params.nperseg} (Overlap: {data.params.noverlap})
          </span>
        </div>
      </div>

      <Plot
        data={[
          {
            x: data.time,
            y: freqKHz,
            z: data.z_db,
            type: 'heatmap',
            colorscale: 'Viridis',
            colorbar: {
              title: 'Magnitude (dB)',
              titleside: 'right',
              tickfont: { color: '#94A3B8', size: 9 },
              titlefont: { color: '#94A3B8', size: 10 }
            }
          }
        ]}
        layout={{
          autosize: true,
          height: 280,
          margin: { l: 45, r: 60, t: 10, b: 35 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: '#0B0F19',
          font: { color: '#94A3B8', size: 10 },
          xaxis: { title: 'Time (seconds)', gridcolor: '#1E293B' },
          yaxis: { title: 'Frequency (kHz)', gridcolor: '#1E293B' }
        }}
        useResizeHandler
        className="w-full"
        config={{ responsive: true, displayModeBar: true }}
      />
    </div>
  );
};
