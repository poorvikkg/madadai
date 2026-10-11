import React, { useState } from 'react';
import { 
  Upload, FileText, Trash2, CheckCircle2, 
  AlertCircle, RefreshCw, FileUp, Database
} from 'lucide-react';
import { DocumentItem, api } from '../services/api';

interface KnowledgeBaseProps {
  documents: DocumentItem[];
  onRefreshDocuments: () => void;
}

export const KnowledgeBaseView: React.FC<KnowledgeBaseProps> = ({ 
  documents, 
  onRefreshDocuments 
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('policy');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title) return;
    setIsUploading(true);
    setUploadError(null);
    try {
      await api.uploadDocument(file, title, category);
      setTitle('');
      setFile(null);
      onRefreshDocuments();
    } catch (err: any) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document and all its indexed chunks?')) return;
    try {
      await api.deleteDocument(docId);
      onRefreshDocuments();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Upload Box */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-2 mb-4">
          <FileUp className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-bold text-white">Ingest Knowledge Base Document</h2>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          Upload PDF, Markdown, or Plain Text support manuals. Text will be cleaned, split into 384-dimension vector chunks, and stored in pgvector with stable chunk IDs.
        </p>

        {uploadError && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>{uploadError}</span>
          </div>
        )}

        <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Document Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. UPI Reconciliation Standard Operating Procedure"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="policy">Policy / Terms</option>
              <option value="faq">FAQ / Knowledge Base</option>
              <option value="historical_ticket">Historical Ticket Solution</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Select File (PDF, TXT, MD)</label>
            <input
              type="file"
              required
              accept=".pdf,.txt,.md,.markdown"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-400 file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"
            />
          </div>

          <div className="md:col-span-3 flex justify-end">
            <button
              type="submit"
              disabled={isUploading}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-md shadow-blue-600/30 flex items-center gap-2 cursor-pointer"
            >
              <Upload className={`w-4 h-4 ${isUploading ? 'animate-bounce' : ''}`} />
              {isUploading ? 'Ingesting & Vectorizing...' : 'Ingest Document'}
            </button>
          </div>
        </form>
      </div>

      {/* Indexed Documents Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white">Indexed Documents</h3>
            <p className="text-xs text-slate-400">Manage indexed policies and inspect chunking status</p>
          </div>
          <button
            onClick={onRefreshDocuments}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/60 uppercase font-semibold text-slate-400 border-b border-slate-700">
              <tr>
                <th className="py-3 px-4">Title & Source</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Type / Size</th>
                <th className="py-3 px-4">Chunks</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No documents indexed yet.
                  </td>
                </tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{d.title}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{d.filename}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 uppercase tracking-wider text-[10px]">
                        {d.doc_category}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="uppercase text-blue-400 font-semibold">{d.file_type}</span> &bull; {(d.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-slate-200">
                      {d.total_chunks} chunks
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold uppercase text-[10px] ${
                        d.status === 'indexed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        d.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        'bg-amber-500/10 text-amber-400'
                      }`}>
                        {d.status === 'indexed' && <CheckCircle2 className="w-3 h-3" />}
                        {d.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(d.id)}
                        className="p-1.5 rounded-md hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-all cursor-pointer"
                        title="Delete document and chunks"
                      >
                        <Trash2 className="w-4 h-4" />
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
