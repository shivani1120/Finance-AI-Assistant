import argparse
import json
from pathlib import Path

from app.core.config import get_settings
from app.evaluation.dataset import load_dataset
from app.evaluation.runner import evaluate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Finance RAG retrieval and answers")
    parser.add_argument("--dataset", type=Path, required=True, help="JSONL evaluation dataset")
    parser.add_argument("--output", type=Path, default=Path("evaluation/report.json"))
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument(
        "--answers",
        action="store_true",
        help="Also generate answers; this calls the configured LLM and may incur provider costs",
    )
    args = parser.parse_args()

    settings = get_settings()
    cases = load_dataset(args.dataset)
    top_k = args.top_k or settings.retrieval_top_k
    report = evaluate_dataset(
        cases,
        settings=settings,
        top_k=top_k,
        include_answers=args.answers,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(args.output), "summary": report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
