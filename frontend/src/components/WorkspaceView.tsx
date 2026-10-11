import React, { useState, useEffect } from 'react';
import { 
  Sparkles, CheckCircle, XCircle, AlertTriangle, 
  ExternalLink, ShieldCheck, UserCheck, RefreshCw, Send,
  FileCheck2, DollarSign
} from 'lucide-react';
import { Ticket, ResolutionRecommendation, ReviewItem, api } from '../services/api';

interface WorkspaceProps {
  tickets: Ticket[];
  selectedTicket: Ticket | null;
  onSelectTicket: (ticket: Ticket) => void;
}

export const WorkspaceView: React.FC<WorkspaceProps> = ({ 
  tickets, 
  selectedTicket, 
  onSelectTicket 
}) => {
  const [recommendation, setRecommendation] = useState<ResolutionRecommendation | null>(null);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [activeCitation, setActiveCitation] = useState<any | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (selectedTicket) {
      loadRecommendationsAndReviews(selectedTicket.id);
    }
  }, [selectedTicket]);

  const loadRecommendationsAndReviews = async (ticketId: number) => {
    try {
      const recs = await api.getRecommendations(ticketId);
      if (recs && recs.length > 0) {
        setRecommendation(recs[0]);
        const revs = await api.getReviews(recs[0].id);
        setReviews(revs);
      } else {
        setRecommendation(null);
        setReviews([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async () => {
    if (!selectedTicket) return;
    setIsGenerating(true);
    try {
      const res = await api.generateResolution(selectedTicket.id);
      setRecommendation(res);
      setToastMessage("Grounded resolution generated successfully!");
      const revs = await api.getReviews(res.id);
      setReviews(revs);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReviewSubmit = async (decision: 'approved' | 'rejected') => {
    if (!recommendation) return;
    setIsSubmittingReview(true);
    try {
      const rev = await api.submitReview(recommendation.id, decision, reviewNotes);
      setReviews([rev, ...reviews]);
      setReviewNotes('');
      setToastMessage(`Decision recorded: ${decision.toUpperCase()}.`);
    } catch (err: any) {
      alert(`Review submission failed: ${err.message}`);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const order = selectedTicket?.order;
  const customer = selectedTicket?.customer;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toast */}
      {toastMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center justify-between text-sm shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Ticket Selection Bar */}
      <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin">
        {tickets.map((t) => (
          <button
            key={t.id}
            onClick={() => onSelectTicket(t)}
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border flex items-center gap-2 cursor-pointer ${
              selectedTicket?.id === t.id
                ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-500/20'
                : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
            }`}
          >
            <span>{t.ticket_number}</span>
            <span className="opacity-70 font-normal">| {t.customer?.full_name || 'Customer'}</span>
          </button>
        ))}
      </div>

      {selectedTicket ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Customer & Authoritative Facts */}
          <div className="lg:col-span-4 space-y-6">
            {/* Customer Query */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Customer Question</span>
                <span className="px-2.5 py-0.5 rounded-full text-xs bg-slate-800 text-slate-300 font-mono">
                  {selectedTicket.channel}
                </span>
              </div>
              <h2 className="text-base font-semibold text-white">{selectedTicket.subject}</h2>
              <div className="mt-3 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-sm text-slate-300 italic">
                "{selectedTicket.initial_question}"
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Customer: <strong className="text-slate-200">{customer?.full_name}</strong></span>
                <span>KYC: <strong className="text-emerald-400">{customer?.kyc_verified ? 'Verified' : 'Unverified'}</strong></span>
              </div>
            </div>

            {/* Authoritative Database Facts */}
            <div className="rounded-2xl bg-slate-900/80 border border-blue-900/40 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Authoritative DB Facts</span>
                </div>
                <span className="text-[10px] bg-blue-500/10 text-blue-300 px-2 py-0.5 rounded border border-blue-400/20">
                  PostgreSQL Verified
                </span>
              </div>

              {order ? (
                <div className="space-y-4 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Order Number:</span>
                      <span className="font-mono font-semibold text-white">{order.order_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Status:</span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        order.status === 'cancelled' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                        order.status === 'delivered' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        'bg-blue-500/20 text-blue-300'
                      }`}>
                        {order.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Order Total:</span>
                      <span className="font-mono font-bold text-emerald-400 text-sm">
                        {order.currency} {order.total_amount}
                      </span>
                    </div>
                    {order.cancellation_reason && (
                      <div className="pt-1.5 border-t border-slate-800 text-[11px] text-slate-300">
                        <span className="text-slate-400">Cancel Reason:</span> {order.cancellation_reason}
                      </div>
                    )}
                  </div>

                  {/* Payment Details */}
                  <div>
                    <span className="text-slate-400 font-semibold block mb-2">Payment Transactions:</span>
                    {order.payments && order.payments.length > 0 ? (
                      order.payments.map((p: any) => (
                        <div key={p.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 mb-2">
                          <div className="flex justify-between">
                            <span className="font-mono text-slate-300">{p.gateway}</span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-400">
                              {p.status}
                            </span>
                          </div>
                          <div className="flex justify-between text-slate-400">
                            <span>Txn ID:</span>
                            <span className="font-mono text-slate-300 truncate max-w-[150px]">{p.transaction_id}</span>
                          </div>
                          <div className="flex justify-between text-slate-400">
                            <span>Paid Amount:</span>
                            <span className="font-semibold text-white">{p.currency} {p.amount}</span>
                          </div>
                          <div className="flex justify-between text-slate-400">
                            <span>Refunded:</span>
                            <span className="text-slate-300">{p.currency} {p.refunded_amount || '0.00'}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-500 italic">No payments recorded</div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 text-xs italic">No order linked to this ticket.</div>
              )}
            </div>
          </div>

          {/* Right Column: AI Resolution & Human Review Decision */}
          <div className="lg:col-span-8 space-y-6">
            {/* Resolution Panel */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Grounded AI Resolution Recommendation</h3>
                    <p className="text-xs text-slate-400">Synthesized strictly from authoritative database facts & verified policies</p>
                  </div>
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs flex items-center gap-2 transition-all cursor-pointer shadow-md shadow-blue-600/30"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                  {isGenerating ? 'Synthesizing...' : recommendation ? 'Regenerate' : 'Generate Recommendation'}
                </button>
              </div>

              {recommendation ? (
                <div className="space-y-6 mt-6">
                  {/* Issue Summary */}
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Issue Summary</span>
                    <p className="text-sm text-slate-200 leading-relaxed">{recommendation.issue_summary}</p>
                  </div>

                  {/* Recommended Resolution */}
                  <div className="p-5 rounded-xl bg-blue-950/30 border border-blue-500/30 shadow-inner">
                    <div className="flex items-center gap-2 mb-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
                      <FileCheck2 className="w-4 h-4" /> Draft Customer Communication
                    </div>
                    <p className="text-sm text-slate-100 leading-relaxed whitespace-pre-line font-normal">
                      {recommendation.recommended_resolution}
                    </p>
                  </div>

                  {/* Step-by-Step Next Actions */}
                  <div>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Required Next Actions</span>
                    <div className="space-y-2">
                      {recommendation.action_steps.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800 text-xs text-slate-300">
                          <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 font-bold flex items-center justify-center shrink-0">
                            {idx + 1}
                          </span>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Citations & Evidence Passages */}
                  <div>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">
                      Supporting Policy Citations (Click to Inspect)
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {recommendation.citations.map((c) => (
                        <button
                          key={c.citation_id}
                          onClick={() => setActiveCitation(c)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition-all cursor-pointer ${
                            activeCitation?.citation_id === c.citation_id
                              ? 'bg-blue-600/30 border-blue-500 text-blue-200'
                              : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:border-slate-600'
                          }`}
                        >
                          <ExternalLink className="w-3.5 h-3.5 text-blue-400" />
                          <span>{c.citation_id}: {c.document_title} (p.{c.page_number || 1})</span>
                        </button>
                      ))}
                    </div>

                    {/* Active Citation Passage Modal/Card */}
                    {activeCitation && (
                      <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-blue-500/40 text-xs text-slate-300 animate-fadeIn">
                        <div className="flex justify-between items-center mb-2">
                          <strong className="text-blue-400 font-semibold">{activeCitation.document_title}</strong>
                          <button onClick={() => setActiveCitation(null)} className="text-slate-500 hover:text-white">&times;</button>
                        </div>
                        <p className="italic text-slate-400">"{activeCitation.passage_snippet}"</p>
                      </div>
                    )}
                  </div>

                  {/* Human Review Authorization Section */}
                  <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <UserCheck className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                          Human Review & Authorization
                        </span>
                      </div>
                      <span className="text-xs text-amber-400 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> Authorization required before execution
                      </span>
                    </div>

                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Add notes for audit logs (e.g., 'Checked Razorpay transaction ID, verified ₹2,000 deduction. Initiating 5-7 day payout')..."
                      rows={2}
                      className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />

                    <div className="flex items-center justify-end gap-3">
                      <button
                        onClick={() => handleReviewSubmit('rejected')}
                        disabled={isSubmittingReview}
                        className="px-4 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        <XCircle className="w-4 h-4" /> Reject Resolution
                      </button>
                      <button
                        onClick={() => handleReviewSubmit('approved')}
                        disabled={isSubmittingReview}
                        className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-emerald-600/30 cursor-pointer"
                      >
                        <CheckCircle className="w-4 h-4" /> Approve Resolution
                      </button>
                    </div>

                    {/* Past Review Audit Trail */}
                    {reviews.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-800 text-xs">
                        <span className="text-slate-400 font-semibold block mb-2">Audit Decision Trail:</span>
                        <div className="space-y-2">
                          {reviews.map((rev) => (
                            <div key={rev.id} className="p-2.5 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                              <div>
                                <span className={`font-bold uppercase text-[10px] px-1.5 py-0.5 rounded mr-2 ${
                                  rev.decision === 'approved' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                                }`}>
                                  {rev.decision}
                                </span>
                                <span className="text-slate-300">{rev.agent_notes || 'No notes provided'}</span>
                              </div>
                              <span className="text-[10px] text-slate-500">
                                {rev.agent_name || 'Agent'} &bull; {new Date(rev.created_at).toLocaleTimeString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="py-16 text-center text-slate-500 space-y-3">
                  <Sparkles className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm">Click "Generate Recommendation" to synthesize verified facts and citations.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="py-20 text-center text-slate-500">
          Select a support ticket to enter the resolution workspace.
        </div>
      )}
    </div>
  );
};
