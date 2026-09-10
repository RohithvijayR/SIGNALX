import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import type { FreqChartData, FreqCharacteristics } from '../types/signal';

interface Props {
  chartData: FreqChartData;
  characteristics: FreqCharacteristics;
}

export const FreqSpectrumChart: React.FC<Props> = ({ chartData, characteristics }) => {
  const [plotMode, setPlotMode] = useState<'psd' | 'fft'>('psd');

  const isPSD = plotMode === 'psd';
  const xVals = isPSD ? chartData.psd_freqs.map(f => f / 1000) : chartData.fft_freqs.map(f => f / 1000); // kHz
  const yVals = isPSD ? chartData.psd_db : chartData.fft_mag_db;

  return (
    <div className="glass-card flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-2">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Frequency Domain Analysis
          </h3>
          <span className="text-xs bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded">
            {characteristics.frequency_label}
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <button
            onClick={() => setPlotMode('psd')}
            className={`px-2.5 py-1 rounded transition-colors ${
              isPSD ? 'bg-cyan-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            PSD (Welch)
          </button>
          <button
            onClick={() => setPlotMode('fft')}
            className={`px-2.5 py-1 rounded transition-colors ${
              !isPSD ? 'bg-cyan-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            FFT Spectrum
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs mb-1">
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block">Occupied BW (99%)</span>
          <span className="text-cyan-300 font-semibold text-sm">
            {(characteristics.occupied_bandwidth_hz / 1000).toFixed(1)} kHz
          </span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block">Dominant Frequency</span>
          <span className="text-emerald-300 font-semibold text-sm">
            {(characteristics.dominant_frequency_hz / 1000).toFixed(1)} kHz
          </span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block">-3dB Bandwidth</span>
          <span className="text-amber-300 font-semibold text-sm">
            {(characteristics.bandwidth_3db_hz / 1000).toFixed(1)} kHz
          </span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block">Spectral Flatness</span>
          <span className="text-purple-300 font-semibold text-sm">
            {characteristics.spectral_flatness.toFixed(3)}
          </span>
        </div>
      </div>

      <Plot
        data={[
          {
            x: xVals,
            y: yVals,
            type: 'scatter',
            mode: 'lines',
            name: isPSD ? 'PSD (dB/Hz)' : 'FFT Mag (dB)',
            line: { color: '#0EA5E9', width: 1.5 }
          }
        ]}
        layout={{
          autosize: true,
          height: 240,
          margin: { l: 45, r: 20, t: 10, b: 35 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: '#0B0F19',
          font: { color: '#94A3B8', size: 10 },
          xaxis: { title: 'Baseband Frequency (kHz)', gridcolor: '#1E293B' },
          yaxis: { title: isPSD ? 'Power Density (dB/Hz)' : 'Magnitude (dB)', gridcolor: '#1E293B' }
        }}
        useResizeHandler
        className="w-full"
        config={{ responsive: true, displayModeBar: true }}
      />
    </div>
  );
};
