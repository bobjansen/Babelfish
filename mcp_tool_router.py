"""
MCP Tool Router - Chess Analysis Tool Dispatch
"""

import logging
import traceback
from typing import Dict, Any, Callable, List
from mcp.types import TextContent
from mcp_tools import MCP_TOOLS
from babelfish.chess_analyzer import ChessAnalyzer

logger = logging.getLogger(__name__)


def log_tool_error(error: Exception, tool_name: str, context: str = ""):
    """Log tool error with full traceback."""
    try:
        tb_str = traceback.format_exc()
        error_msg = f"Error in tool '{tool_name}' {context}: {str(error)}\n\nFull traceback:\n{tb_str}"
        logger.error(error_msg)
    except Exception as log_error:
        # Fallback if logging itself fails
        logger.error(f"Failed to log tool error: {log_error}")
        logger.error(f"Original error in {tool_name}: {error}")


class MCPToolRouter:
    """Routes MCP tool calls to chess analysis implementations."""

    def __init__(self, chess_analyzer: ChessAnalyzer = None):
        if chess_analyzer is None:
            # Import here to avoid circular imports and initialize if not provided
            chess_analyzer = ChessAnalyzer()

        self.chess_analyzer = chess_analyzer
        self.tools: Dict[str, Callable] = {}
        self._register_tools()

    def _register_tools(self):
        """Register all available chess analysis MCP tools."""
        self.tools = {
            "analyze_position": self._analyze_position,
            "analyze_game": self._analyze_game,
            "explain_position": self._explain_position,
        }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Route tool call to appropriate chess analysis implementation.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            Dict[str, Any] for backward compatibility with openrouter_cli.py
        """
        if tool_name not in self.tools:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        try:
            # Get the TextContent result
            text_results = self.tools[tool_name](arguments)

            # Convert to dict format for backward compatibility
            if text_results and len(text_results) > 0:
                return {
                    "status": "success",
                    "message": text_results[0].text,
                    "tool_name": tool_name
                }
            else:
                return {"status": "error", "message": "No result from tool"}

        except Exception as e:
            log_tool_error(e, tool_name, "during execution")
            return {"status": "error", "message": f"Tool execution failed: {str(e)}"}

    def call_tool_mcp(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP-compatible method that returns TextContent list.

        Use this method for proper MCP server implementations.
        """
        if tool_name not in self.tools:
            return [TextContent(type="text", text=f"❌ Unknown tool: {tool_name}")]

        try:
            return self.tools[tool_name](arguments)
        except Exception as e:
            log_tool_error(e, tool_name, "during execution")
            return [TextContent(type="text", text=f"❌ Tool execution failed: {str(e)}")]

    def get_available_tools(self) -> list:
        """Get list of available MCP tools."""
        return MCP_TOOLS

    # Chess analysis tool implementations
    def _analyze_position(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze a chess position using Stockfish engine."""
        try:
            fen = arguments.get("fen")
            depth = arguments.get("depth", 15)

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            # Validate FEN
            analysis = self.chess_analyzer.analyze_position(fen, depth)
            explanation = self.chess_analyzer.get_position_explanation(fen)

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
            else:
                eval_text = "Unknown evaluation"

            formatted_response = f"""🐟 **Chess Position Analysis**

**Position:** {fen}

**Evaluation:** {eval_text}
**Best Move:** {analysis['best_move'] or 'No legal moves'}

**Explanation:** {explanation}

**Top 3 Moves:**"""

            for i, move_info in enumerate(analysis["top_moves"][:3], 1):
                move = move_info["Move"]
                centipawn = move_info.get("Centipawn")
                cp_text = f"{centipawn/100:+.1f}" if centipawn is not None else "N/A"
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

    def _analyze_game(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze a complete chess game move by move."""
        try:
            moves = arguments.get("moves", [])
            depth = arguments.get("depth", 12)

            if not moves:
                return [TextContent(type="text", text="❌ Error: Moves list is required")]

            analyses = self.chess_analyzer.analyze_game(moves)

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
                formatted_response += f"\n*Showing last 5 moves of {len(analyses)} total*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error analyzing game: {str(e)}")]

    def _explain_position(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get a human-readable explanation of a chess position."""
        try:
            fen = arguments.get("fen")

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            explanation = self.chess_analyzer.get_position_explanation(fen)
            formatted_response = f"🐟 **Position Explanation**\n\n**FEN:** {fen}\n\n**Analysis:** {explanation}"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error explaining position: {str(e)}")]
