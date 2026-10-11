import React from 'react';
import { 
  CheckCircle2, AlertCircle, Clock, FileText, 
  ArrowUpRight, ShieldCheck, Database, Cpu, Search
} from 'lucide-react';
import { DashboardStats, Ticket } from '../services/api';

interface OverviewProps {
  stats: DashboardStats | null;
  tickets: Ticket[];
  onSelectTicket: (ticket: Ticket) => void;
  onNavigate: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewProps> = ({ 
  stats, 
  tickets, 
  onSelectTicket, 
  onNavigate 
}) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900/60 via-slate-900 to-indigo-950 p-8 border border-blue-500/20 shadow-2xl backdrop-blur-xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/30 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            AI-Assisted Support Resolution Platform
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Authoritative Resolutions with Zero Hallucinations.
          </h1>
          <p className="mt-3 text-slate-300 text-base leading-relaxed">
            MadadAI unifies transactional order facts from PostgreSQL with company policies and pgvector retrieval, giving human agents verifiable, grounded recommendations before executing customer actions.
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <button
              onClick={() => onNavigate('workspace')}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all shadow-lg shadow-blue-600/30 flex items-center gap-2 cursor-pointer"
            >
              Resolve Pending Tickets <ArrowUpRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('inspector')}
              className="px-5 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm transition-all flex items-center gap-2 cursor-pointer"
            >
              <Search className="w-4 h-4 text-slate-400" /> Inspect Hybrid Retrieval
            </button>
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-blue-500/10 to-transparent pointer-events-none" />
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-md hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tickets</span>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">{stats?.total_tickets ?? '—'}</span>
            <span className="text-xs text-slate-400">logged</span>
          </div>
          <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% database backed
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-md hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Open Tickets</span>
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-300">{stats?.open_tickets ?? '—'}</span>
            <span className="text-xs text-slate-400">pending response</span>
          </div>
          <div className="mt-2 text-xs text-amber-400/90 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" /> Requires agent review
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-md hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Awaiting Review</span>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-purple-300">{stats?.awaiting_reviews ?? '—'}</span>
            <span className="text-xs text-slate-400">AI drafts</span>
          </div>
          <div className="mt-2 text-xs text-purple-400/90 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Zero automatic payouts
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-md hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Indexed Documents</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-300">{stats?.indexed_documents ?? '—'}</span>
            <span className="text-xs text-slate-400">policy manuals</span>
          </div>
          <div className="mt-2 text-xs text-emerald-400/90 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> pgvector 384-dim
          </div>
        </div>
      </div>

      {/* Live Ticket Worklist */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-bold text-white">Active Support Queries</h2>
            <p className="text-xs text-slate-400">Select any ticket to view verified business facts and AI-assisted resolution</p>
          </div>
          <button
            onClick={() => onNavigate('workspace')}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
          >
            Open workspace &rarr;
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/60 text-xs uppercase font-semibold text-slate-400 border-b border-slate-700">
              <tr>
                <th className="py-3 px-4">Ticket</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Subject & Question</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {tickets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No support tickets found. Check database or seed scripts.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-blue-400">
                      {t.ticket_number}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">{t.customer?.full_name || 'Customer'}</div>
                      <div className="text-xs text-slate-400">{t.customer?.email}</div>
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-semibold text-slate-200 truncate">{t.subject}</div>
                      <div className="text-xs text-slate-400 truncate mt-0.5">{t.initial_question}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-xs bg-slate-800 border border-slate-700 text-slate-300 uppercase tracking-wider">
                        {t.category}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wider ${
                        t.priority === 'high' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        t.priority === 'urgent' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                        'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}>
                        {t.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          onSelectTicket(t);
                          onNavigate('workspace');
                        }}
                        className="px-3 py-1.5 rounded-lg bg-blue-600/80 hover:bg-blue-500 text-white text-xs font-medium transition-all cursor-pointer shadow-sm"
                      >
                        Review Resolution
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
