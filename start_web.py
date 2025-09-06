#!/usr/bin/env python3
"""Startup script for Babelfish web interface."""

import os
import sys
import argparse
from web_interface import app


def main():
    """Start the Babelfish web interface."""

    parser = argparse.ArgumentParser(
        description="Babelfish Chess Analysis Web Interface"
    )
    parser.add_argument(
        "--model",
        default="anthropic/claude-3.5-sonnet",
        help="OpenRouter model to use (default: anthropic/claude-3.5-sonnet)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the web server on (default: 5000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the web server to (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    print("🐟 Babelfish Chess Analysis Web Interface")
    print("=" * 45)

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print()
        print("To get started:")
        print("1. Get an API key from https://openrouter.ai/")
        print("2. Set the environment variable:")
        print("   export OPENROUTER_API_KEY=your_key_here")
        print("3. Run this script again")
        print()
        print("Usage examples:")
        print(
            "  python start_web.py                                    # Default model"
        )
        print(
            "  python start_web.py --model anthropic/claude-3-haiku   # Different model"
        )
        print(
            "  python start_web.py --port 8080                        # Different port"
        )
        return 1

    print(f"🔑 Using API key: {api_key[:12]}...")
    print(f"🤖 Using model: {args.model}")
    print()
    print("🌐 Starting web server...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print("🛑 Press Ctrl+C to stop")
    print()
    print("Features available:")
    print("  • Interactive chess board")
    print(f"  • AI analysis with {args.model} and Stockfish (16 threads)")
    print("  • Analysis tab: Human-readable insights")
    print("  • Debug tab: Full AI reasoning log")
    print("  • Board visualization with tactical highlighting")
    print()

    # Set model for the web interface
    app.config["MODEL"] = args.model

    try:
        app.run(debug=False, port=args.port, host=args.host)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Babelfish web interface...")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
