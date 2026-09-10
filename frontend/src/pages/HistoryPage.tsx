import React, { useEffect, useState } from 'react';
import { History, Search } from 'lucide-react';
import { fetchAnalysisHistory, fetchHistoryDetail } from '../services/api';
import type { HistoryRecord, SignalAnalysisReport } from '../types/signal';

interface Props {
  onLoadReport: (report: SignalAnalysisReport) => void;
  setActiveTab: (tab: string) => void;
}

export const HistoryPage: React.FC<Props> = ({ onLoadReport, setActiveTab }) => {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysisHistory()
      .then(setRecords)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = records.filter(r =>
    r.filename.toLowerCase().includes(search.toLowerCase()) ||
    r.modulation.toLowerCase().includes(search.toLowerCase()) ||
    r.format.toLowerCase().includes(search.toLowerCase())
  );

  const handleOpenRecord = async (id: number) => {
    try {
      const report = await fetchHistoryDetail(id);
      onLoadReport(report);
      setActiveTab('analyze');
    } catch (err) {
      alert('Failed to load history record.');
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/15 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="h-6 w-6 text-white/80" /> Historical Analysis Archive
          </h1>
          <p className="text-xs text-white/60">
            View past signal intelligence analysis records stored in local SQLite database.
          </p>
        </div>

        <div className="relative w-64">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-white/40" />
          <input
            type="text"
            placeholder="Search filename or modulation..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-white/50 focus:outline-none focus:border-white/40"
          />
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/5 text-white/70 uppercase font-mono text-[10px] border-b border-white/15">
              <tr>
                <th className="p-3">ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Filename</th>
                <th className="p-3">Format</th>
                <th className="p-3">Modulation</th>
                <th className="p-3">Confidence</th>
                <th className="p-3">FEC Status</th>
                <th className="p-3">SNR</th>
                <th className="p-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10 text-white/80">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-4 text-center text-white/50">
                    {loading ? 'Loading history records...' : 'No historical analysis records found.'}
                  </td>
                </tr>
              ) : (
                filtered.map(rec => (
                  <tr key={rec.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-mono text-white/60">#{rec.id}</td>
                    <td className="p-3 font-mono text-white/70">
                      {new Date(rec.timestamp).toLocaleDateString()} {new Date(rec.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="p-3 font-mono text-white font-semibold">{rec.filename}</td>
                    <td className="p-3">{rec.format}</td>
                    <td className="p-3 font-semibold text-white">{rec.modulation}</td>
                    <td className="p-3">{rec.confidence}%</td>
                    <td className="p-3">{rec.fec_scheme}</td>
                    <td className="p-3">{rec.snr_db} dB</td>
                    <td className="p-3">
                      <button
                        onClick={() => handleOpenRecord(rec.id)}
                        className="bg-white/10 hover:bg-white/15 text-white border border-white/20 px-2.5 py-1 rounded text-[11px] transition-colors"
                      >
                        View Report
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
