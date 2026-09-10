import React from 'react';
import { Activity, Radio, History, Database, Cpu, Info, Zap, Menu } from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<Props> = ({ activeTab, setActiveTab }) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'analyze', label: 'Analyze Signal', icon: Radio },
    { id: 'history', label: 'Signal History', icon: History },
    { id: 'dataset', label: 'Dataset / Training', icon: Database },
    { id: 'model', label: 'Model Info', icon: Cpu },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 py-4 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Main Navigation Bar - Pill Shaped */}
        <nav className="backdrop-blur-xl bg-black/40 border border-white/15 rounded-full px-6 py-3.5 flex items-center justify-between gap-8 shadow-2xl hover:border-white/25 transition-all duration-300">
          {/* Brand */}
          <div 
            onClick={() => setActiveTab('dashboard')} 
            className="flex items-center gap-2 cursor-pointer shrink-0 group"
          >
            <div className="relative h-9 w-9 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center group-hover:bg-white/15 transition-all">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-sm text-white tracking-wide font-mono hidden sm:inline">SIGNALFUSION</span>
          </div>

          {/* Desktop Navigation Items */}
          <div className="hidden lg:flex items-center gap-1">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-white/15 text-white border border-white/30'
                      : 'text-white/70 hover:text-white hover:bg-white/10 border border-transparent'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setActiveTab('analyze')}
              className="bg-white/90 hover:bg-white text-black font-semibold text-xs px-4 py-2 rounded-full transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2 group whitespace-nowrap"
            >
              <Radio className="h-3.5 w-3.5 group-hover:rotate-12 transition-transform" />
              <span className="hidden sm:inline">Analyze</span>
            </button>
            
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-white/15 text-white transition-all"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </nav>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="mt-3 backdrop-blur-xl bg-black/40 border border-white/15 rounded-2xl px-4 py-3 max-w-6xl mx-auto">
          <nav className="flex flex-col gap-2">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileOpen(false);
                  }}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-white/15 text-white border border-white/30'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
};
