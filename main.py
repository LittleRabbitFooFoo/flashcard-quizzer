"""CLI entry point for the Flashcard Quizzer.

Usage:
    python main.py --mode sequential --file data/glossary.json
    python main.py -m adaptive -f data/python_basics.json --stats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import ui
from quiz_engine import QuizEngine, QuizModeFactory
from utils.file_handler import FlashcardLoadError, load_flashcards


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Quiz yourself on a deck of flashcards loaded from a JSON file.",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="file",
        required=True,
        help="Path to the flashcard JSON file.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        dest="mode",
        default="sequential",
        choices=["sequential", "random", "adaptive"],
        help="Quiz mode to use (default: sequential).",
    )
    parser.add_argument(
        "--stats",
        dest="stats_file",
        nargs="?",
        const="stats.json",
        default=None,
        help="Write the session summary as JSON to this path (default: stats.json).",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """Parse arguments, run a quiz session, and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cards = load_flashcards(args.file)
        mode = QuizModeFactory.create(args.mode, cards)
    except (FlashcardLoadError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Loaded {len(cards)} card(s) from '{args.file}' in {args.mode} mode.")
    print('Type "exit" or press Ctrl+C at any time to quit.\n')

    engine = QuizEngine(mode)
    try:
        stats = engine.run(ui.ask_answer, ui.report_feedback)
    except KeyboardInterrupt:
        stats = engine.stats
        print("\nExiting quiz. Thanks for playing!")

    ui.show_stats(stats)

    if args.stats_file:
        Path(args.stats_file).write_text(
            json.dumps(
                {
                    "total_questions": stats.total_questions,
                    "correct": stats.correct,
                    "accuracy": stats.accuracy,
                    "missed_terms": stats.missed_terms,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Stats written to {args.stats_file}")

    return 0


if __name__ == "__main__":
    sys.exit(run())
