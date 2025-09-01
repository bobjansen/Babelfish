#!/usr/bin/env python3
"""Babelfish MCP Server - Chess Analysis Tools."""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.types import TextContent, Tool
from babelfish.chess_analyzer import ChessAnalyzer
from mcp_tools import MCP_TOOLS

async def main():
    # Create server
    server = Server("babelfish")
    analyzer = ChessAnalyzer()

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available chess analysis tools."""
        return MCP_TOOLS

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle chess analysis tool calls."""
        try:
            if name == "analyze_position":
                fen = arguments.get("fen")
                depth = arguments.get("depth", 15)

                if not fen:
                    return [
                        TextContent(
                            type="text", text="❌ Error: FEN position is required"
                        )
                    ]

                # Validate FEN
                try:
                    analysis = analyzer.analyze_position(fen, depth)
                    explanation = analyzer.get_position_explanation(fen)

                    # Format the response nicely
                    {
                        "position": {
                            "fen": fen,
                            "evaluation": analysis["evaluation"],
                            "best_move": analysis["best_move"],
                            "top_moves": analysis["top_moves"],
                        },
                        "analysis": {
                            "explanation": explanation,
                            "depth_analyzed": depth,
                        },
                    }

                    # Create a formatted text response
                    eval_info = analysis["evaluation"]
                    if eval_info["type"] == "cp":
                        eval_text = f"{eval_info['value']/100:.1f} pawns"
                        if eval_info["value"] > 0:
                            eval_text = f"+{eval_text} (White advantage)"
                        elif eval_info["value"] < 0:
                            eval_text = f"{eval_text} (Black advantage)"
                        else:
                            eval_text = "Equal position"
                    elif eval_info["type"] == "mate":
                        moves = eval_info["value"]
                        side = "White" if moves > 0 else "Black"
                        eval_text = f"Mate in {abs(moves)} for {side}"

                    formatted_response = f"""🐟 **Chess Position Analysis**

**Position:** {fen}

**Evaluation:** {eval_text}
**Best Move:** {analysis['best_move'] or 'No legal moves'}

**Explanation:** {explanation}

**Top 3 Moves:**"""

                    for i, move_info in enumerate(analysis["top_moves"][:3], 1):
                        move = move_info["Move"]
                        centipawn = move_info["Centipawn"]
                        cp_text = (
                            f"{centipawn/100:+.1f}" if centipawn is not None else "N/A"
                        )
                        formatted_response += f"\n{i}. {move} ({cp_text})"

                    formatted_response += f"\n\n*Analysis depth: {depth}*"

                    return [TextContent(type="text", text=formatted_response)]

                except Exception as e:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Error analyzing position: {str(e)}\n\nPlease check that the FEN notation is valid.",
                        )
                    ]

            elif name == "analyze_game":
                moves = arguments.get("moves", [])
                depth = arguments.get("depth", 12)

                if not moves:
                    return [
                        TextContent(
                            type="text", text="❌ Error: Moves list is required"
                        )
                    ]

                try:
                    analyses = analyzer.analyze_game(moves)

                    formatted_response = f"🐟 **Chess Game Analysis**\n\n**Total Moves:** {len(moves)}\n**Analysis Depth:** {depth}\n\n"

                    for analysis in analyses[-5:]:  # Show last 5 moves
                        move_num = analysis["move_number"]
                        move = analysis["move"]
                        eval_info = analysis["evaluation"]

                        if eval_info["type"] == "cp":
                            eval_text = f"{eval_info['value']/100:+.1f}"
                        elif eval_info["type"] == "mate":
                            moves_to_mate = eval_info["value"]
                            eval_text = f"Mate in {abs(moves_to_mate)}"
                        else:
                            eval_text = "Unknown"

                        formatted_response += f"**{move_num}.** {move} → {eval_text}\n"

                    if len(analyses) > 5:
                        formatted_response += (
                            f"\n*Showing last 5 moves of {len(analyses)} total*"
                        )

                    return [TextContent(type="text", text=formatted_response)]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"❌ Error analyzing game: {str(e)}"
                        )
                    ]

            elif name == "explain_position":
                fen = arguments.get("fen")

                if not fen:
                    return [
                        TextContent(
                            type="text", text="❌ Error: FEN position is required"
                        )
                    ]

                try:
                    explanation = analyzer.get_position_explanation(fen)
                    formatted_response = f"🐟 **Position Explanation**\n\n**FEN:** {fen}\n\n**Analysis:** {explanation}"

                    return [TextContent(type="text", text=formatted_response)]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"❌ Error explaining position: {str(e)}"
                        )
                    ]

            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
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


if __name__ == "__main__":
    asyncio.run(main())
