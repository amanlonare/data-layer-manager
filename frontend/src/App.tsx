import React, { useState, useRef } from 'react';
import {
  Search,
  Upload,
  Settings,
  Database,
  Cpu,
  Clock,
  ArrowRight,
  Filter,
  Layers,
  ChevronRight
} from 'lucide-react';
import { api } from './api';
import type { SearchResult } from './api';
import './App.css';

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [ingesting, setIngesting] = useState(false);
  const [progress, setProgress] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [limit, setLimit] = useState(10);
  const [strategy, setStrategy] = useState('hybrid');
  const [isSearching, setIsSearching] = useState(false);

  const handleIngestClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIngesting(true);
    setProgress(0);

    try {
      const response = await api.uploadFile(file);
      trackProgress(response.task_id);
    } catch (error) {
      console.error('File Upload failed:', error);
      setIngesting(false);
    } finally {
      // Clear input
      e.target.value = '';
    }
  };

  const trackProgress = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await api.getTaskStatus(taskId);
        setProgress(status.progress);
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          setTimeout(() => {
            setIngesting(false);
            setProgress(0);
          }, 1000);
        }
      } catch (e) {
        clearInterval(interval);
        setIngesting(false);
      }
    }, 1000);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const res = await api.search({ query, limit, strategy });
      setResults(res.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="dashboard-root">
      {/* Configuration Sidebar */}
      <aside className="sidebar-config">
        <header className="flex-center" style={{ gap: '0.75rem', justifyContent: 'flex-start' }}>
          <div className="flex-center" style={{ padding: '0.5rem', background: 'hsla(var(--primary), 0.1)', borderRadius: '8px', border: '1px solid hsla(var(--primary), 0.3)' }}>
            <Layers size={24} color="hsl(var(--primary))" />
          </div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', background: 'linear-gradient(to right, white, #666)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            DLM Panel
          </h1>
        </header>

        <nav className="flex-column" style={{ gap: '1.5rem' }}>
          <section className="config-group">
            <label className="section-label">
              <Filter size={12} /> Retrieval Strategy
            </label>
            <div className="flex-column" style={{ gap: '0.4rem' }}>
              {[
                { id: 'hybrid', label: 'Hybrid (Fused)', icon: <Layers size={14} /> },
                { id: 'pgvector', label: 'Postgres Vector', icon: <Database size={14} /> },
                { id: 'qdrant', label: 'Qdrant Vector', icon: <Cpu size={14} /> },
                { id: 'fts', label: 'Postgres Keyword', icon: <Search size={14} /> },
                { id: 'graph', label: 'Neo4j Graph', icon: <Filter size={14} /> }
              ].map(s => (
                <button
                  key={s.id}
                  onClick={() => setStrategy(s.id)}
                  className={`config-btn ${strategy === s.id ? 'active' : ''}`}
                  style={{ padding: '0.625rem 0.75rem' }}
                >
                  <div className="flex-center" style={{ gap: '0.75rem', justifyContent: 'flex-start' }}>
                    {s.icon}
                    <span style={{ fontSize: '0.8125rem' }}>{s.label}</span>
                  </div>
                  {strategy === s.id && <div className="status-dot" />}
                </button>
              ))}
            </div>
          </section>

          <section className="config-group">
            <label className="section-label">
              <Settings size={12} /> Result Limit
            </label>
            <div className="flex-column" style={{ gap: '0.75rem' }}>
              <input
                type="range" min="1" max="50"
                value={limit}
                onChange={e => setLimit(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'hsl(var(--primary))', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontFamily: 'monospace', color: 'hsl(var(--text-muted))' }}>
                <span>5</span>
                <span style={{ color: 'hsl(var(--primary))' }}>{limit} Chunks</span>
                <span>50</span>
              </div>
            </div>
          </section>
        </nav>

        <footer className="glass-panel" style={{ marginTop: 'auto', padding: '1rem', borderStyle: 'dashed', borderColor: 'hsla(var(--text-muted), 0.2)', backgroundColor: 'transparent' }}>
           <div className="section-label" style={{ marginBottom: '0.75rem' }}>
              <Database size={12} /> Services
           </div>
           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              {['PG', 'NQ', 'QD', 'RD'].map(s => (
                <div key={s} className="flex-center" style={{ justifyContent: 'flex-start', padding: '0.375rem', borderRadius: '4px', background: 'black', border: '1px solid hsla(var(--text-muted), 0.1)', gap: '0.5rem' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                  <span style={{ fontSize: '10px', fontFamily: 'monospace', color: 'hsl(var(--text-muted))' }}>{s} OK</span>
                </div>
              ))}
           </div>
        </footer>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Header / Ingestion Area */}
        <header className="glass-panel panel-header">
          <div>
             <h2 style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Upload size={24} color="hsl(var(--primary))" /> Ingestion Pipeline
             </h2>
             <p style={{ fontSize: '0.875rem', color: 'hsl(var(--text-muted))', marginTop: '0.25rem' }}>
               Upload and vectorize your knowledge base documents.
             </p>
          </div>

          <div className="flex-center" style={{ gap: '1rem' }}>
             {ingesting && (
                <div className="flex-column" style={{ alignItems: 'flex-end', gap: '0.25rem', minWidth: '150px' }}>
                  <div className="flex-center" style={{ gap: '0.5rem', fontSize: '0.75rem', fontFamily: 'monospace', textTransform: 'uppercase', color: 'hsl(var(--primary))' }}>
                    <Clock size={12} className="animate-spin" /> Processing...
                  </div>
                  <div style={{ width: '100%', height: '4px', background: 'hsla(var(--text-muted), 0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div
                      style={{ height: '100%', background: 'linear-gradient(to right, hsl(var(--primary)), hsla(var(--primary), 0.5))', width: `${progress}%`, transition: 'width 0.3s ease' }}
                    />
                  </div>
                </div>
             )}
             <input
               type="file"
               ref={fileInputRef}
               onChange={handleFileChange}
               style={{ display: 'none' }}
             />
             <button
               onClick={handleIngestClick}
               disabled={ingesting}
               className="btn-primary"
             >
               {ingesting ? 'Processing...' : 'New Ingestion'}
               {!ingesting && <ChevronRight size={16} />}
             </button>
          </div>
        </header>

        {/* Search Input Area */}
        <div className="search-wrapper">
          <div className="search-glow" />
          <form onSubmit={handleSearch}>
            <div className="search-input-group">
              <div className={`search-icon-box ${isSearching ? 'active' : ''}`}>
                 <Search size={24} className={isSearching ? 'animate-spin' : ''} />
              </div>
              <input
                type="text"
                placeholder="Ask your data anything..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                className="search-input"
              />
              <button
                type="submit"
                className="flex-center"
                style={{ height: '3.5rem', width: '3.5rem', borderRadius: '12px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'white' }}
                disabled={isSearching}
              >
                <ArrowRight size={24} />
              </button>
            </div>
          </form>
        </div>

        {/* Results Stream Area */}
        <div className="results-feed">
           {results.length > 0 ? (
             <>
                 {results.map((res) => (
                    <article key={res.id} className="result-card">
                       <header className="result-header">
                          <div className="score-badge">
                             <div className="score-icon">
                                <Cpu size={16} />
                             </div>
                             <span className="score-text">SIMILARITY: {(res.score * 100).toFixed(1)}%</span>
                          </div>
                          <div className="metadata-group">
                             {Object.entries(res.metadata || {}).map(([k, v]) => (
                                <span key={k} className="meta-tag">
                                   {k}: {String(v)}
                                </span>
                             ))}
                          </div>
                       </header>
                       <p className="result-text">"{res.content}"</p>
                    </article>
                 ))}
             </>
           ) : !isSearching && query && (
              <div className="flex-center" style={{ padding: '5rem', border: '2px dashed hsla(var(--text-muted), 0.1)', borderRadius: '24px', flexDirection: 'column', gap: '1rem', color: 'hsl(var(--text-muted))' }}>
                 <Settings size={48} style={{ opacity: 0.1 }} />
                 <p>No results found for this search configuration.</p>
              </div>
           )}
        </div>
      </main>
    </div>
  );
};

export default App;
