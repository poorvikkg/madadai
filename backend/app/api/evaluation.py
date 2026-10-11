import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.api_schemas import EvaluationRunResponse, RetrievalMetric
from app.services.retrieval_service import retrieval_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])

# Ground truth test cases for evaluation
BENCHMARK_CASES = [
    {
        "query": "Where is my refund for cancelled order?",
        "expected_keywords": ["refund", "cancellation", "days"],
        "expected_title": "Cancellation & Refund Policy"
    },
    {
        "query": "Damaged goods return window replacement",
        "expected_keywords": ["return", "damaged", "replacement"],
        "expected_title": "Damaged & Defective Items Policy"
    },
    {
        "query": "UPI payment deducted but transaction failed",
        "expected_keywords": ["deducted", "reversal", "banking"],
        "expected_title": "Payment Failure & Auto-Reversal Guidelines"
    },
    {
        "query": "Address change after order dispatch",
        "expected_keywords": ["shipping", "address", "courier"],
        "expected_title": "Shipping & Delivery Policy"
    }
]

@router.post("/run", response_model=EvaluationRunResponse)
def run_retrieval_evaluation(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    strategies = ["semantic", "keyword", "hybrid_rrf"]
    results_by_strategy = {s: {"recall_at_1": 0, "recall_at_3": 0, "recall_at_5": 0, "mrr": 0.0, "latency": []} for s in strategies}
    sample_evaluations = []

    total_queries = len(BENCHMARK_CASES)

    for case in BENCHMARK_CASES:
        query = case["query"]
        expected_title = case["expected_title"].lower()
        eval_sample = {"query": query, "strategy_ranks": {}}

        # 1. Semantic
        t0 = time.perf_counter()
        sem_res = retrieval_service.semantic_search(query, db, top_k=5)
        t_sem = (time.perf_counter() - t0) * 1000
        results_by_strategy["semantic"]["latency"].append(t_sem)
        _score_metrics("semantic", sem_res, expected_title, results_by_strategy, eval_sample)

        # 2. Keyword
        t0 = time.perf_counter()
        kw_res = retrieval_service.keyword_search(query, db, top_k=5)
        t_kw = (time.perf_counter() - t0) * 1000
        results_by_strategy["keyword"]["latency"].append(t_kw)
        _score_metrics("keyword", kw_res, expected_title, results_by_strategy, eval_sample)

        # 3. Hybrid
        t0 = time.perf_counter()
        hyb_res = retrieval_service.hybrid_search(query, db, top_k=5)
        t_hyb = (time.perf_counter() - t0) * 1000
        results_by_strategy["hybrid_rrf"]["latency"].append(t_hyb)
        _score_metrics("hybrid_rrf", hyb_res, expected_title, results_by_strategy, eval_sample)

        sample_evaluations.append(eval_sample)

    strategy_metrics: List[RetrievalMetric] = []
    for s_name, data in results_by_strategy.items():
        count = max(1, total_queries)
        strategy_metrics.append(RetrievalMetric(
            strategy=s_name,
            recall_at_1=round(data["recall_at_1"] / count, 4),
            recall_at_3=round(data["recall_at_3"] / count, 4),
            recall_at_5=round(data["recall_at_5"] / count, 4),
            mrr=round(data["mrr"] / count, 4),
            mean_latency_ms=round(sum(data["latency"]) / len(data["latency"]), 2) if data["latency"] else 0.0
        ))

    return EvaluationRunResponse(
        run_timestamp=datetime.utcnow(),
        total_queries=total_queries,
        strategies_compared=strategy_metrics,
        sample_evaluations=sample_evaluations
    )

def _score_metrics(strategy_name: str, candidates: List[Dict[str, Any]], expected_title: str, results_dict: dict, eval_sample: dict):
    found_rank = None
    for idx, cand in enumerate(candidates, start=1):
        cand_title = cand.get("document_title", "").lower()
        if expected_title in cand_title or any(w in cand.get("content", "").lower() for w in expected_title.split()):
            found_rank = idx
            break

    eval_sample["strategy_ranks"][strategy_name] = found_rank

    if found_rank:
        if found_rank <= 1:
            results_dict[strategy_name]["recall_at_1"] += 1
        if found_rank <= 3:
            results_dict[strategy_name]["recall_at_3"] += 1
        if found_rank <= 5:
            results_dict[strategy_name]["recall_at_5"] += 1
        results_dict[strategy_name]["mrr"] += (1.0 / found_rank)
