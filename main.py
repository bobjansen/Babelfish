#!/usr/bin/env python3
"""Babelfish - Speak to your chess engine.

A chess analysis tool that uses Stockfish via MCP to provide context-rich
analysis of chess positions and games.
"""

import asyncio
import sys
from babelfish.mcp_server import run_server
from babelfish.chess_analyzer import ChessAnalyzer


def demo_analysis():
    """Run a demo analysis to test the chess analyzer."""
    analyzer = ChessAnalyzer()

    print("🐟 Babelfish Chess Analyzer Demo")
    print("================================")

    # Starting position
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"\nAnalyzing starting position:")
    print(f"FEN: {starting_fen}")

    try:
        analysis = analyzer.analyze_position(starting_fen)
        explanation = analyzer.get_position_explanation(starting_fen)

        print(f"Best move: {analysis['best_move']}")
        print(f"Evaluation: {analysis['evaluation']}")
        print(f"Explanation: {explanation}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Stockfish is installed on your system")
        print("Ubuntu/Debian: sudo apt install stockfish")
        print("macOS: brew install stockfish")
        return False

    return True


async def run_mcp_server():
    """Run the MCP server for integration with other tools."""
    try:
        print("🐟 Starting Babelfish MCP Server...", file=sys.stderr)
        await run_server()
    except Exception as e:
        print(f"❌ MCP Server error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        raise


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # Run as MCP server
        asyncio.run(run_mcp_server())
    else:
        # Run demo
        if demo_analysis():
            print("\n✅ Demo completed successfully!")
            print("\nTo use Babelfish as an MCP server, run:")
            print("python main.py --mcp")
        else:
            print("\n❌ Demo failed. Please check Stockfish installation.")
            sys.exit(1)


if __name__ == "__main__":
    main()
