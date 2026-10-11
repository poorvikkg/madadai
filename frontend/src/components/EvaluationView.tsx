import React, { useState } from 'react';
import { Play, CheckCircle2, TrendingUp, Cpu, Gauge } from 'lucide-react';
import { api } from '../services/api';

export const EvaluationView: React.FC = () => {
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    try {
      const res = await api.runEvaluation();
      setEvalResult(res);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white mb-1">RAG Retrieval Benchmark & Evaluation</h2>
            <p className="text-xs text-slate-400">
              Run real empirical queries against the active knowledge base. Compares Keyword (FTS), Semantic (pgvector), and Hybrid (RRF) across Recall@K, MRR, and actual measured latency.
            </p>
          </div>
          <button
            onClick={handleRunEvaluation}
            disabled={isRunning}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-md shadow-blue-600/30 flex items-center gap-2 cursor-pointer shrink-0"
          >
            <Play className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
            {isRunning ? 'Benchmarking Retrieval...' : 'Execute Evaluation Run'}
          </button>
        </div>
      </div>

      {evalResult && (
        <div className="space-y-6">
          {/* Metrics comparison cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {evalResult.strategies_compared.map((st: any) => (
              <div 
                key={st.strategy} 
                className={`p-6 rounded-2xl border shadow-xl backdrop-blur-md ${
                  st.strategy === 'hybrid_rrf'
                    ? 'bg-blue-950/40 border-blue-500/40'
                    : 'bg-slate-900/80 border-slate-800'
                }`}
              >
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    {st.strategy === 'hybrid_rrf' ? 'Hybrid RRF (Recommended)' : st.strategy.toUpperCase()}
                  </span>
                  {st.strategy === 'hybrid_rrf' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                      Best Overall
                    </span>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Recall @ 1:</span>
                    <span className="font-mono font-bold text-white">{(st.recall_at_1 * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Recall @ 3:</span>
                    <span className="font-mono font-bold text-white">{(st.recall_at_3 * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Recall @ 5:</span>
                    <span className="font-mono font-bold text-emerald-400">{(st.recall_at_5 * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">MRR (Mean Reciprocal Rank):</span>
                    <span className="font-mono font-bold text-blue-400">{st.mrr.toFixed(3)}</span>
                  </div>
                  <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-xs">
                    <span className="text-slate-400">Mean Latency:</span>
                    <span className="font-mono font-semibold text-slate-300">{st.mean_latency_ms} ms</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Test queries evaluated */}
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
            <h3 className="text-sm font-bold text-white mb-4">Empirical Test Query Breakdown</h3>
            <div className="space-y-3">
              {evalResult.sample_evaluations.map((sample: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-2">
                  <div className="font-semibold text-slate-200">Query: "{sample.query}"</div>
                  <div className="flex flex-wrap gap-4 text-slate-400">
                    <span>
                      Semantic Rank: <strong className="text-slate-200">{sample.strategy_ranks.semantic ?? 'Not found'}</strong>
                    </span>
                    <span>
                      Keyword Rank: <strong className="text-slate-200">{sample.strategy_ranks.keyword ?? 'Not found'}</strong>
                    </span>
                    <span>
                      Hybrid Rank: <strong className="text-blue-400">{sample.strategy_ranks.hybrid_rrf ?? 'Not found'}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
