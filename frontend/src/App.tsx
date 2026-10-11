import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, LifeBuoy, BookOpen, 
  Search, BarChart3, Settings, LogOut, ShieldCheck, User 
} from 'lucide-react';
import { OverviewView } from './components/OverviewView';
import { WorkspaceView } from './components/WorkspaceView';
import { KnowledgeBaseView } from './components/KnowledgeBaseView';
import { InspectorView } from './components/InspectorView';
import { EvaluationView } from './components/EvaluationView';
import { SettingsView } from './components/SettingsView';
import { api, DashboardStats, Ticket, DocumentItem } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'workspace' | 'knowledge' | 'inspector' | 'evaluation' | 'settings'>('overview');
  const [user, setUser] = useState<any | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  // Login form state
  const [email, setEmail] = useState('agent@madadai.com');
  const [password, setPassword] = useState('password123');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  useEffect(() => {
    checkAuthAndLoad();
  }, []);

  const checkAuthAndLoad = async () => {
    try {
      if (api.getToken()) {
        const u = await api.getMe();
        setUser(u);
        loadPlatformData();
      } else {
        // Auto-login seeded agent for instant live development experience
        handleLoginSubmit();
      }
    } catch {
      handleLoginSubmit();
    }
  };

  const handleLoginSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoggingIn(true);
    setAuthError(null);
    try {
      const data = await api.login(email, password);
      setUser(data.user);
      loadPlatformData();
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const loadPlatformData = async () => {
    try {
      const [s, t, d] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.getTickets().catch(() => []),
        api.getDocuments().catch(() => []),
      ]);
      setStats(s);
      setTickets(t);
      setDocuments(d);
      if (t.length > 0 && !selectedTicket) {
        setSelectedTicket(t[0]);
      }
    } catch (e) {
      console.error('Error loading data:', e);
    }
  };

  const handleLogout = () => {
    api.setToken(null);
    setUser(null);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-black text-white tracking-tight">MadadAI</h1>
              <p className="text-xs text-slate-400">AI Customer Support Resolution Platform</p>
            </div>
          </div>

          {authError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {authError}
            </div>
          )}

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Agent Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-600/30 cursor-pointer disabled:opacity-50"
            >
              {isLoggingIn ? 'Authenticating...' : 'Sign In to Agent Portal'}
            </button>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
              Seed Agent: <code className="text-blue-400">agent@madadai.com</code> / Password: <code className="text-blue-400">password123</code>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 bg-slate-900/80 border-r border-slate-800/80 p-5 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 px-2 mb-8">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-white">MadadAI</span>
              <span className="block text-[10px] uppercase font-bold tracking-widest text-blue-400">Resolution OS</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" /> Overview Dashboard
            </button>

            <button
              onClick={() => setActiveTab('workspace')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'workspace'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <LifeBuoy className="w-4 h-4" /> Support Workspace
            </button>

            <button
              onClick={() => setActiveTab('knowledge')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'knowledge'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-4 h-4" /> Knowledge Base
            </button>

            <button
              onClick={() => setActiveTab('inspector')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'inspector'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Search className="w-4 h-4" /> Retrieval Inspector
            </button>

            <button
              onClick={() => setActiveTab('evaluation')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'evaluation'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-4 h-4" /> Evaluation & Benchmarks
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'settings'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Settings className="w-4 h-4" /> Settings & Config
            </button>
          </nav>
        </div>

        {/* User Card */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 font-bold text-xs">
                {user.full_name?.charAt(0) || 'A'}
              </div>
              <div className="truncate">
                <div className="text-xs font-semibold text-white truncate">{user.full_name}</div>
                <div className="text-[10px] text-slate-400 truncate">{user.role}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-8 overflow-y-auto">
        {activeTab === 'overview' && (
          <OverviewView 
            stats={stats} 
            tickets={tickets} 
            onSelectTicket={setSelectedTicket} 
            onNavigate={(tab: any) => setActiveTab(tab)} 
          />
        )}
        {activeTab === 'workspace' && (
          <WorkspaceView 
            tickets={tickets} 
            selectedTicket={selectedTicket} 
            onSelectTicket={setSelectedTicket} 
          />
        )}
        {activeTab === 'knowledge' && (
          <KnowledgeBaseView 
            documents={documents} 
            onRefreshDocuments={loadPlatformData} 
          />
        )}
        {activeTab === 'inspector' && <InspectorView />}
        {activeTab === 'evaluation' && <EvaluationView />}
        {activeTab === 'settings' && <SettingsView />}
      </main>
    </div>
  );
}

export default App;
