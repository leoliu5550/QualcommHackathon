# fileorg/cli/argument_parser.py
import argparse

from fileorg.cli.ports import OrganizeArgs, RestoreArgs


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface parser for the FileOrg application.

    This parser supports two main commands:
    1. `organize`: Scan, parse, classify, and optionally execute file organization.
    2. `restore`: Restore files from a previously created backup.

    Returns:
        argparse.ArgumentParser: Configured argument parser with subcommands and options.
    """
    parser = argparse.ArgumentParser(prog="fileorg", description="AI File Organizer - Command Line Interface")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === organize ===
    organize_parser = subparsers.add_parser("organize", help="Organize files (scan → parse → classify → execute)")
    organize_parser.add_argument("--path", "-p", required=True, metavar="DIR", help="Root directory to organize")
    organize_parser.add_argument("--preview", "-d", action="store_true", help="Preview mode; does not actually move files")
    organize_parser.add_argument("--model", default="default-llm", help="Specify the LLM model to use")
    organize_parser.add_argument("--char-limit", type=int, default=500, metavar="N", help="Character limit for file content")

    # === restore ===
    restore_parser = subparsers.add_parser("restore", help="Restore previously organized files")
    restore_parser.add_argument("--path", "-p", required=True, metavar="DIR", help="Root directory containing .backup folder")

    return parser


def parse_args_to_dataclass(args: argparse.Namespace):
    """Convert argparse.Namespace to corresponding dataclass based on command.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        OrganizeArgs | RestoreArgs: Dataclass representation of command arguments.
    """
    if args.command == "organize":
        return OrganizeArgs(path=args.path, preview=args.preview, model=args.model, char_limit=args.char_limit)
    elif args.command == "restore":
        return RestoreArgs(path=args.path)
    else:
        raise ValueError(f"Unknown command {args.command}")
