const API_BASE = '/api/v1';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface Ticket {
  id: number;
  ticket_number: string;
  customer_id: number;
  order_id?: number;
  subject: string;
  initial_question: string;
  status: string;
  priority: string;
  category: string;
  channel: string;
  created_at: string;
  customer?: any;
  order?: any;
}

export interface DocumentItem {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  doc_category: string;
  status: string;
  total_chunks: number;
  error_message?: string;
  created_at: string;
  indexed_at?: string;
}

export interface Citation {
  citation_id: string;
  document_id: number;
  document_title: string;
  passage_snippet: string;
  page_number?: number;
}

export interface ResolutionRecommendation {
  id: number;
  ticket_id: number;
  issue_summary: string;
  verified_business_facts: {
    customer_name: string;
    customer_email: string;
    order_number?: string;
    order_status?: string;
    total_amount?: string;
    currency?: string;
    payments?: any[];
    cancellation_date?: string;
    authoritative_note: string;
  };
  recommended_resolution: string;
  action_steps: string[];
  citations: Citation[];
  uncertainties?: string;
  review_required: boolean;
  retrieved_chunk_ids: number[];
  created_at: string;
  generation_metadata: any;
}

export interface ReviewItem {
  id: number;
  recommendation_id: number;
  agent_id?: number;
  agent_name?: string;
  decision: 'approved' | 'rejected' | 'modified';
  agent_notes?: string;
  modified_resolution?: string;
  created_at: string;
}

export interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  awaiting_reviews: number;
  indexed_documents: number;
}

class ApiService {
  private token: string | null = localStorage.getItem('madadai_token');

  setToken(t: string | null) {
    this.token = t;
    if (t) localStorage.setItem('madadai_token', t);
    else localStorage.removeItem('madadai_token');
  }

  getToken(): string | null {
    return this.token;
  }

  private headers() {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      h['Authorization'] = `Bearer ${this.token}`;
    }
    return h;
  }

  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: this.headers() });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/dashboard/stats`, { headers: this.headers() });
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  }

  async getTickets(): Promise<Ticket[]> {
    const res = await fetch(`${API_BASE}/business/tickets`, { headers: this.headers() });
    if (!res.ok) throw new Error('Failed to fetch tickets');
    return res.json();
  }

  async getTicket(id: number): Promise<Ticket> {
    const res = await fetch(`${API_BASE}/business/tickets/${id}`, { headers: this.headers() });
    if (!res.ok) throw new Error('Failed to fetch ticket');
    return res.json();
  }

  async getDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents/`, { headers: this.headers() });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  }

  async uploadDocument(file: File, title: string, category: string): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('category', category);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: {
        ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {})
      },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  }

  async deleteDocument(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  }

  async generateResolution(ticketId: number): Promise<ResolutionRecommendation> {
    const res = await fetch(`${API_BASE}/resolution/generate/${ticketId}`, {
      method: 'POST',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
      throw new Error(err.detail || 'Generation failed');
    }
    return res.json();
  }

  async getRecommendations(ticketId: number): Promise<ResolutionRecommendation[]> {
    const res = await fetch(`${API_BASE}/resolution/recommendations/${ticketId}`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
  }

  async submitReview(recId: number, decision: 'approved' | 'rejected' | 'modified', notes: string): Promise<ReviewItem> {
    const res = await fetch(`${API_BASE}/resolution/review/${recId}`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ decision, agent_notes: notes }),
    });
    if (!res.ok) throw new Error('Failed to submit review');
    return res.json();
  }

  async getReviews(recId: number): Promise<ReviewItem[]> {
    const res = await fetch(`${API_BASE}/resolution/reviews/${recId}`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to fetch reviews');
    return res.json();
  }

  async inspectRetrieval(query: string, topK: number = 5): Promise<any> {
    const res = await fetch(`${API_BASE}/retrieval/inspect?q=${encodeURIComponent(query)}&top_k=${topK}`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to inspect retrieval');
    return res.json();
  }

  async runEvaluation(): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluation/run`, {
      method: 'POST',
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to run evaluation');
    return res.json();
  }

  async getSettingsStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/status`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Failed to fetch settings status');
    return res.json();
  }
}

export const api = new ApiService();
