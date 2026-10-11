import React, { useEffect, useState } from 'react';
import { Settings, ShieldAlert, Cpu, Server, Database, Key } from 'lucide-react';
import { api } from '../services/api';

export const SettingsView: React.FC = () => {
  const [config, setConfig] = useState<any | null>(null);

  useEffect(() => {
    api.getSettingsStatus().then(setConfig).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl">
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-2 mb-2">
          <Settings className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-bold text-white">System & Engine Configuration</h2>
        </div>
        <p className="text-xs text-slate-400">
          Operational engine settings, embedding models, LLM grounding policies, and cache configuration.
        </p>

        {config && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-slate-300">
                <Cpu className="w-4 h-4 text-blue-400" /> Embedding Engine
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Provider:</span> <strong className="text-white uppercase">{config.embedding_provider}</strong>
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Model:</span> <strong className="text-white">{config.embedding_model}</strong>
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Vector Dimension:</span> <strong className="text-blue-400 font-mono">{config.vector_dimension}</strong>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-slate-300">
                <Server className="w-4 h-4 text-purple-400" /> LLM Generation Engine
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Provider:</span> <strong className="text-white uppercase">{config.llm_provider}</strong>
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Model:</span> <strong className="text-white">{config.llm_model}</strong>
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Reranker:</span> <strong className="text-white uppercase">{config.reranker_provider}</strong>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-slate-300">
                <Database className="w-4 h-4 text-emerald-400" /> Cache & Limits
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Redis Status:</span> 
                <strong className={config.redis_connected ? 'text-emerald-400' : 'text-amber-400'}>
                  {config.redis_connected ? 'Connected' : 'In-Memory Pass-through'}
                </strong>
              </div>
              <div className="text-slate-400 flex justify-between">
                <span>Max Upload Size:</span> <strong className="text-white">{config.max_upload_size_mb} MB</strong>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-slate-300">
                <Key className="w-4 h-4 text-amber-400" /> Security Controls
              </div>
              <div className="text-slate-400">
                <span>API Secrets:</span> Protected in <code className="text-slate-300 bg-slate-900 px-1 py-0.5 rounded">.env</code>
              </div>
              <div className="text-slate-400">
                <span>Execution Mode:</span> Human-in-the-Loop Required
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
