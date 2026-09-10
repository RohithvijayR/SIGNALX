import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import type { TimeChartData } from '../types/signal';

interface Props {
  chartData: TimeChartData;
}

export const TimeDomainChart: React.FC<Props> = ({ chartData }) => {
  const [showI, setShowI] = useState(true);
  const [showQ, setShowQ] = useState(true);
  const [showMag, setShowMag] = useState(true);
  const [showPhase, setShowPhase] = useState(false);

  const valid = useMemo(() => {
    // Safely extract arrays with defaults
    const timeArr = Array.isArray(chartData?.time) ? chartData.time : [];
    const iArr = Array.isArray(chartData?.i) ? chartData.i : [];
    const qArr = Array.isArray(chartData?.q) ? chartData.q : [];
    const magArr = Array.isArray(chartData?.magnitude) ? chartData.magnitude : [];
    const phaseArr = Array.isArray(chartData?.phase) ? chartData.phase : [];
    
    const count = Math.min(timeArr.length, iArr.length, qArr.length, magArr.length, phaseArr.length);
    const rows: Array<[number, number, number, number, number]> = [];
    
    for (let index = 0; index < count; index += 1) {
      const row = [timeArr[index], iArr[index], qArr[index], magArr[index], phaseArr[index]] as [number, number, number, number, number];
      // Only include rows where all values are finite numbers
      if (row.every(v => typeof v === 'number' && Number.isFinite(v))) {
        rows.push(row);
      }
    }
    
    return {
      time: rows.map(row => row[0]), 
      i: rows.map(row => row[1]), 
      q: rows.map(row => row[2]),
      magnitude: rows.map(row => row[3]), 
      phase: rows.map(row => row[4]),
      totalPoints: count,
      finitePoints: rows.length
    };
  }, [chartData]);
  const traces: any[] = [];

  if (showI && valid.i.length) {
    traces.push({
      x: valid.time,
      y: valid.i,
      type: 'scatter',
      mode: 'lines',
      name: 'In-phase (I)',
      line: { color: '#38BDF8', width: 1.5 }
    });
  }

  if (showQ && valid.q.length) {
    traces.push({
      x: valid.time,
      y: valid.q,
      type: 'scatter',
      mode: 'lines',
      name: 'Quadrature (Q)',
      line: { color: '#F472B6', width: 1.5 }
    });
  }

  if (showMag && valid.magnitude.length) {
    traces.push({
      x: valid.time,
      y: valid.magnitude,
      type: 'scatter',
      mode: 'lines',
      name: 'Magnitude |S|',
      line: { color: '#34D399', width: 2 }
    });
  }

  if (showPhase && valid.phase.length) {
    traces.push({
      x: valid.time,
      y: valid.phase,
      type: 'scatter',
      mode: 'lines',
      name: 'Phase (rad)',
      yaxis: 'y2',
      line: { color: '#FBBF24', width: 1, dash: 'dot' }
    });
  }

  return (
    <div className="glass-card flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-2">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400"></span> Time-Domain Waveform
        </h3>
        <div className="flex items-center gap-3 text-xs">
          <label className="flex items-center gap-1 cursor-pointer text-cyan-400">
            <input type="checkbox" checked={showI} onChange={e => setShowI(e.target.checked)} /> I
          </label>
          <label className="flex items-center gap-1 cursor-pointer text-pink-400">
            <input type="checkbox" checked={showQ} onChange={e => setShowQ(e.target.checked)} /> Q
          </label>
          <label className="flex items-center gap-1 cursor-pointer text-emerald-400">
            <input type="checkbox" checked={showMag} onChange={e => setShowMag(e.target.checked)} /> Magnitude
          </label>
          <label className="flex items-center gap-1 cursor-pointer text-amber-400">
            <input type="checkbox" checked={showPhase} onChange={e => setShowPhase(e.target.checked)} /> Phase
          </label>
        </div>
      </div>

      {valid.time.length > 0 ? <Plot
        key={`${valid.time.length}-${valid.time[0]}-${valid.time[valid.time.length - 1]}`}
        revision={valid.time.length}
        data={traces}
        layout={{
          autosize: true,
          height: 280,
          margin: { l: 45, r: 45, t: 10, b: 35 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: '#0B0F19',
          font: { color: '#94A3B8', size: 10 },
          xaxis: { title: 'Time (seconds)', gridcolor: '#1E293B' },
          yaxis: { title: 'Amplitude', gridcolor: '#1E293B' },
          yaxis2: showPhase ? {
            title: 'Phase (rad)',
            overlaying: 'y',
            side: 'right',
            gridcolor: 'transparent'
          } : undefined,
          legend: { orientation: 'h', x: 0, y: 1.15 }
        }}
        useResizeHandler
        className="w-full"
        config={{ responsive: true, displayModeBar: true }}
      /> : <div className="h-[280px] grid place-items-center text-xs text-amber-300 bg-slate-900/60 rounded flex flex-col gap-2 p-4">
        <div>No finite waveform samples were returned by the analysis.</div>
        {valid.totalPoints > 0 && valid.finitePoints === 0 && (
          <div className="text-[11px] text-slate-400">(Debug: Received {valid.totalPoints} points but all were filtered as non-finite)</div>
        )}
      </div>}
    </div>
  );
};
