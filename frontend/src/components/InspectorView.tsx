import React, { useState } from 'react';
import { Search, Layers, Zap, Filter, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

export const InspectorView: React.FC = () => {
  const [query, setQuery] = useState('cancelled order ₹2,000 refund');
  const [inspectData, setInspectData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'fused' | 'semantic' | 'keyword' | 'reranked'>('fused');

  const handleInspect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setIsLoading(true);
    try {
      const data = await api.inspectRetrieval(query, 5);
      setInspectData(data);
    } catch (err: any) {
      alert(`Retrieval inspection failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <h2 className="text-base font-bold text-white mb-1">Hybrid Retrieval Inspector & Explainability</h2>
        <p className="text-xs text-slate-400 mb-6">
          Compare PostgreSQL Full-Text Search scores with pgvector Cosine similarity, Reciprocal Rank Fusion (RRF), and candidate reranking.
        </p>

        <form onSubmit={handleInspect} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search test query..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-md shadow-blue-600/30 flex items-center gap-2 cursor-pointer"
          >
            {isLoading ? 'Running Hybrid Pipeline...' : 'Inspect Pipeline'}
          </button>
        </form>
      </div>

      {inspectData && (
        <div className="space-y-6">
          {/* Strategy Tabs */}
          <div className="flex border-b border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab('fused')}
              className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === 'fused'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Hybrid RRF Fusion ({inspectData.fused_candidates?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('semantic')}
              className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === 'semantic'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Semantic pgvector ({inspectData.semantic_candidates?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('keyword')}
              className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === 'keyword'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Keyword FTS ({inspectData.keyword_candidates?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('reranked')}
              className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === 'reranked'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Reranked Output ({inspectData.reranked_candidates?.length || 0})
            </button>
          </div>

          {/* Cards display */}
          <div className="grid grid-cols-1 gap-4">
            {activeTab === 'fused' &&
              inspectData.fused_candidates.map((c: any, idx: number) => (
                <div key={idx} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-xs">
                      #{idx + 1} {c.document_title} (Page {c.page_number || 1})
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-400/20 text-blue-400 text-[11px] font-mono font-bold">
                        RRF Score: {c.rrf_score}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
                    {c.content}
                  </p>
                  <div className="mt-3 flex gap-4 text-[11px] text-slate-500">
                    <span>Semantic Score: <strong className="text-slate-300">{c.semantic_score?.toFixed(4) ?? 'N/A'}</strong></span>
                    <span>Keyword Score: <strong className="text-slate-300">{c.keyword_score?.toFixed(4) ?? 'N/A'}</strong></span>
                  </div>
                </div>
              ))}

            {activeTab === 'semantic' &&
              inspectData.semantic_candidates.map((c: any, idx: number) => (
                <div key={idx} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-xs">#{idx + 1} {c.document_title}</span>
                    <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-400/20 text-purple-400 text-[11px] font-mono font-bold">
                      Cosine Sim: {c.semantic_score?.toFixed(4)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
                    {c.content}
                  </p>
                </div>
              ))}

            {activeTab === 'keyword' &&
              inspectData.keyword_candidates.map((c: any, idx: number) => (
                <div key={idx} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-xs">#{idx + 1} {c.document_title}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-400/20 text-emerald-400 text-[11px] font-mono font-bold">
                      FTS Rank: {c.keyword_score?.toFixed(4)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
                    {c.content}
                  </p>
                </div>
              ))}

            {activeTab === 'reranked' &&
              inspectData.reranked_candidates.map((c: any, idx: number) => (
                <div key={idx} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-xs">#{idx + 1} {c.document_title}</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-400/20 text-amber-400 text-[11px] font-mono font-bold">
                      Rerank Score: {c.rerank_score}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
                    {c.content}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};
