"""MCP server for Babelfish chess analysis."""

import json
import sys
import traceback
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import TextContent, Tool
from .chess_analyzer import ChessAnalyzer


def create_server():
    """Create and configure the MCP server."""
    server = Server("babelfish")
    analyzer = ChessAnalyzer()

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        print("📋 Listing available tools...", file=sys.stderr)
        return [
            Tool(
                name="analyze_position",
                description="Analyze a chess position using Stockfish engine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis depth (default: 15)",
                            "default": 15,
                        },
                    },
                    "required": ["fen"],
                },
            ),
            Tool(
                name="analyze_game",
                description="Analyze a complete chess game move by move",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "moves": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of moves in standard algebraic notation",
                        }
                    },
                    "required": ["moves"],
                },
            ),
            Tool(
                name="explain_position",
                description="Get a human-readable explanation of a chess position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation",
                        }
                    },
                    "required": ["fen"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        print(f"🔧 Tool called: {name} with args: {arguments}", file=sys.stderr)
        try:
            if name == "analyze_position":
                fen = arguments.get("fen")
                depth = arguments.get("depth", 15)

                if not fen:
                    return [
                        TextContent(type="text", text="Error: FEN position is required")
                    ]

                analysis = analyzer.analyze_position(fen, depth)
                explanation = analyzer.get_position_explanation(fen)

                result = {"analysis": analysis, "explanation": explanation}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "analyze_game":
                moves = arguments.get("moves", [])

                if not moves:
                    return [
                        TextContent(type="text", text="Error: Moves list is required")
                    ]

                analyses = analyzer.analyze_game(moves)

                summary = {"total_moves": len(moves), "game_analysis": analyses}

                return [TextContent(type="text", text=json.dumps(summary, indent=2))]

            elif name == "explain_position":
                fen = arguments.get("fen")

                if not fen:
                    return [
                        TextContent(type="text", text="Error: FEN position is required")
                    ]

                explanation = analyzer.get_position_explanation(fen)

                return [TextContent(type="text", text=explanation)]
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            print(f"❌ Tool error: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def run_server():
    """Run the MCP server."""
    try:
        print("🔧 Creating MCP server...", file=sys.stderr)
        server = create_server()

        print("🔧 Initializing stdio transport...", file=sys.stderr)
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            print("🔧 Starting server...", file=sys.stderr)
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="babelfish",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        print(f"❌ run_server error: {e}", file=sys.stderr)

        traceback.print_exc(file=sys.stderr)
        raise
