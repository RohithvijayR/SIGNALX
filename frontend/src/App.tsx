import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { DemoBar } from './components/DemoBar';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { HistoryPage } from './pages/HistoryPage';
import { DatasetPage } from './pages/DatasetPage';
import { ModelInfoPage } from './pages/ModelInfoPage';
import { AboutPage } from './pages/AboutPage';
import { generateSyntheticSignal } from './services/api';
import type { SignalAnalysisReport } from './types/signal';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [currentReport, setCurrentReport] = useState<SignalAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSelectDemo = async (demoId: string) => {
    setIsLoading(true);
    setActiveTab('analyze');

    let mod = 'QPSK';
    let snr = 15.0;
    let fec = 'Convolutional';
    let interleaver = '16x16 Matrix';

    if (demoId === 'BPSK') {
      mod = 'BPSK';
      snr = 12.0;
      fec = 'None';
      interleaver = 'None';
    } else if (demoId === '16QAM') {
      mod = '16QAM';
      snr = 20.0;
      fec = 'Reed-Solomon';
      interleaver = '8x32 Block';
    } else if (demoId === '2FSK') {
      mod = '2FSK';
      snr = 10.0;
      fec = 'Convolutional';
      interleaver = 'None';
    } else if (demoId === 'PAIRED') {
      mod = 'QPSK';
      snr = 18.0;
      fec = 'Convolutional';
      interleaver = '16x16 Matrix';
    }

    try {
      const report = await generateSyntheticSignal({
        modulation: mod,
        snr_db: snr,
        fec_scheme: fec,
        interleaving_pattern: interleaver,
        sample_rate: 1000000.0
      });
      setCurrentReport(report);
    } catch (err) {
      alert('Failed to load demo signal.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <DemoBar onSelectDemo={handleSelectDemo} isLoading={isLoading} />

      <main className="flex-1 w-full overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {activeTab === 'dashboard' && (
            <DashboardPage setActiveTab={setActiveTab} onSelectDemo={handleSelectDemo} />
          )}

          {activeTab === 'analyze' && (
            <AnalyzePage
              currentReport={currentReport}
              setCurrentReport={setCurrentReport}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />
          )}

          {activeTab === 'history' && (
            <HistoryPage
              onLoadReport={report => setCurrentReport(report)}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'dataset' && (
            <DatasetPage
              onLoadReport={report => setCurrentReport(report)}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'model' && <ModelInfoPage />}

          {activeTab === 'about' && <AboutPage />}
        </div>
      </main>

      <footer className="bg-black/60 border-t border-white/15 py-4 text-center text-xs text-white/50 font-mono">
        SIGNALFUSION — AI-Driven IQ & WAV Signal Intelligence Platform | NTRO SIH 2026 PS 26147
      </footer>
    </div>
  );
}

export default App;
