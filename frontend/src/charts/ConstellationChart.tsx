import React from 'react';
import Plot from 'react-plotly.js';
import type { ConstellationData } from '../types/signal';

interface Props {
  data: ConstellationData;
}

export const ConstellationChart: React.FC<Props> = ({ data }) => {
  const symbolAvailable = data.timing.reliable && data.symbol_sampled.i.length > 0;

  return (
    <div className="glass-card flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-2">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400"></span> I/Q Scatter and Symbol Evidence
        </h3>
        <span className="text-xs text-slate-400">Timing: {data.timing.reason}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <p className="text-xs font-mono text-cyan-300 mb-2">Raw IQ Scatter — not a symbol constellation</p>
          <Plot
            data={[
          {
            x: data.raw.i,
            y: data.raw.q,
            type: 'scatter',
            mode: 'markers',
            name: 'Raw IQ samples',
            marker: {
              color: '#38BDF8',
              size: 4,
              opacity: 0.6
            }
          }
            ]}
            layout={{
          autosize: true,
          height: 250,
          margin: { l: 45, r: 45, t: 10, b: 35 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: '#0B0F19',
          font: { color: '#94A3B8', size: 10 },
          xaxis: { title: 'In-phase (I)', gridcolor: '#1E293B', zerolinecolor: '#475569' },
          yaxis: { title: 'Quadrature (Q)', gridcolor: '#1E293B', zerolinecolor: '#475569', scaleanchor: 'x', scaleratio: 1 }
            }} useResizeHandler className="w-full" config={{ responsive: true, displayModeBar: true }} />
        </div>
        <div>
          <p className="text-xs font-mono text-emerald-300 mb-2">Symbol-Sampled Constellation {symbolAvailable ? '' : '— unavailable'}</p>
          {symbolAvailable ? <Plot data={[{ x: data.symbol_sampled.i, y: data.symbol_sampled.q, type: 'scatter', mode: 'markers', name: 'Timing-synchronized symbols', marker: { color: '#34D399', size: 4, opacity: 0.65 } }]} layout={{ autosize: true, height: 250, margin: { l: 45, r: 45, t: 10, b: 35 }, paper_bgcolor: 'transparent', plot_bgcolor: '#0B0F19', font: { color: '#94A3B8', size: 10 }, xaxis: { title: 'In-phase (I)', gridcolor: '#1E293B' }, yaxis: { title: 'Quadrature (Q)', gridcolor: '#1E293B', scaleanchor: 'x', scaleratio: 1 } }} useResizeHandler className="w-full" config={{ responsive: true, displayModeBar: true }} /> : <div className="h-[250px] grid place-items-center bg-slate-900/60 border border-slate-800 rounded text-xs text-slate-400 text-center p-6">No reliable symbol timing was found. Raw IQ geometry is excluded from QAM/PSK evidence.</div>}
        </div>
      </div>
    </div>
  );
};
