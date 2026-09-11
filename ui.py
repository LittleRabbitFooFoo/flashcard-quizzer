"""Terminal presentation: prompts, colored feedback, and the stats summary."""

from typing import Optional

from models import Flashcard
from quiz_engine import SessionStats

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

EXIT_COMMANDS = {"exit", "quit"}


def ask_answer(card: Flashcard) -> Optional[str]:
    """Prompt the user for an answer to `card`.

    Returns None if the user typed an exit command or interrupted with
    Ctrl+C/Ctrl+D, signalling that the quiz loop should stop gracefully.
    """
    try:
        response = input(f"{BOLD}Q:{RESET} {card.front}\n> ")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting quiz. Thanks for playing!")
        return None

    if response.strip().lower() in EXIT_COMMANDS:
        print("Exiting quiz. Thanks for playing!")
        return None
    return response


def report_feedback(card: Flashcard, correct: bool) -> None:
    """Print colored immediate feedback for one answered card."""
    if correct:
        print(f"{GREEN}Correct!{RESET}\n")
    else:
        print(f"{RED}Incorrect.{RESET} The answer was: {card.back}\n")


def show_stats(stats: SessionStats) -> None:
    """Print the end-of-session summary table."""
    print(f"{BOLD}Session Summary{RESET}")
    print("-" * 40)
    print(f"Total Questions : {stats.total_questions}")
    print(f"Accuracy        : {stats.accuracy:.1f}%")
    if stats.missed_terms:
        print("Missed Terms    :")
        for term in stats.missed_terms:
            print(f"  - {term}")
    else:
        print("Missed Terms    : none")
    print("-" * 40)
