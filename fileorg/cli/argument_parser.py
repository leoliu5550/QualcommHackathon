# fileorg/cli/argument_parser.py
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fileorg", description="AI File Organizer - Command Line Interface")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === organize ===
    organize_parser = subparsers.add_parser("organize", help="Organize files (scan → parse → classify → execute)")
    organize_parser.add_argument("--path", "-p", required=True, metavar="DIR", help="Root directory to organize")
    organize_parser.add_argument("--output", "-o", required=True, metavar="DIR", help="Output directory for organized files")
    organize_parser.add_argument("--preview", "-d", action="store_true", help="Preview mode; does not actually move files")
    organize_parser.add_argument("--model", default="default-llm", help="Specify the LLM model to use")
    organize_parser.add_argument("--char-limit", type=int, default=500, metavar="N", help="Character limit for file content")

    # === restore ===
    restore_parser = subparsers.add_parser("restore", help="Restore previously organized files")
    restore_parser.add_argument("--manifest", "-m", required=True, metavar="FILE", help="Path to the manifest file for restoration")

    return parser
