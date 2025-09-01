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
            "get_principal_variation": self._get_principal_variation,
            "suggest_move": self._suggest_move,
            "find_tactical_motifs": self._find_tactical_motifs,
            "evaluate_move_quality": self._evaluate_move_quality,
            "analyze_endgame": self._analyze_endgame,
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

    def _get_principal_variation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get the engine's principal variation from a position."""
        try:
            fen = arguments.get("fen")
            depth = arguments.get("depth", 20)
            max_moves = arguments.get("max_moves", 10)

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            pv_result = self.chess_analyzer.get_principal_variation(fen, depth, max_moves)
            
            formatted_response = f"""🐟 **Principal Variation Analysis**

**Starting Position:** {fen}

**Best Line ({pv_result['total_moves']} moves):** {' '.join(pv_result['pv_moves'])}

**Move-by-Move Analysis:**"""

            for i, move_analysis in enumerate(pv_result['pv_analysis'][:5], 1):  # Show first 5 moves
                move = move_analysis['move_san']
                eval_info = move_analysis['evaluation']
                
                if eval_info['type'] == 'cp':
                    eval_text = f"{eval_info['value']/100:+.1f}"
                elif eval_info['type'] == 'mate':
                    eval_text = f"Mate in {abs(eval_info['value'])}"
                else:
                    eval_text = "N/A"
                
                formatted_response += f"\n{i}. {move} → {eval_text}"

            if len(pv_result['pv_analysis']) > 5:
                formatted_response += f"\n\n*Showing first 5 moves of {len(pv_result['pv_analysis'])} analyzed*"

            formatted_response += f"\n\n*Analysis depth: {depth}, Max moves: {max_moves}*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting principal variation: {str(e)}")]

    def _suggest_move(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Suggest the best move for a position with explanation."""
        try:
            fen = arguments.get("fen")
            depth = arguments.get("depth", 18)

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            analysis = self.chess_analyzer.analyze_position(fen, depth)
            explanation = self.chess_analyzer.get_position_explanation(fen)

            eval_info = analysis["evaluation"]
            if eval_info["type"] == "cp":
                eval_text = f"{eval_info['value']/100:+.1f} pawns"
                if eval_info["value"] > 0:
                    eval_text += " (White advantage)"
                elif eval_info["value"] < 0:
                    eval_text += " (Black advantage)"
                else:
                    eval_text = "Equal position"
            elif eval_info["type"] == "mate":
                moves = eval_info["value"]
                side = "White" if moves > 0 else "Black"
                eval_text = f"Mate in {abs(moves)} for {side}"
            else:
                eval_text = "Unknown evaluation"

            formatted_response = f"""🐟 **Move Suggestion**

**Position:** {fen}

**Recommended Move:** {analysis['best_move'] or 'No legal moves'}

**Position Evaluation:** {eval_text}

**Why this move:** {explanation}

**Alternative Moves:**"""

            for i, move_info in enumerate(analysis["top_moves"][:3], 1):
                move = move_info["Move"]
                centipawn = move_info.get("Centipawn")
                if centipawn is not None:
                    cp_text = f"{centipawn/100:+.1f}"
                    diff = centipawn - (eval_info.get("value", 0) if eval_info["type"] == "cp" else 0)
                    if abs(diff) > 10:  # Significant difference
                        cp_text += f" ({diff/100:+.1f} from best)"
                else:
                    cp_text = "N/A"
                formatted_response += f"\n{i}. {move} ({cp_text})"

            formatted_response += f"\n\n*Analysis depth: {depth}*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error suggesting move: {str(e)}")]

    def _find_tactical_motifs(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze position for tactical motifs."""
        try:
            fen = arguments.get("fen")
            depth = arguments.get("depth", 15)

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            analysis = self.chess_analyzer.analyze_position(fen, depth)
            
            # Analyze top moves for tactical patterns
            tactical_moves = []
            eval_info = analysis["evaluation"]
            base_eval = eval_info.get("value", 0) if eval_info["type"] == "cp" else 0

            for move_info in analysis["top_moves"][:5]:
                centipawn = move_info.get("Centipawn")
                if centipawn is not None:
                    improvement = centipawn - base_eval
                    if improvement > 100:  # Significant improvement suggests tactics
                        tactical_moves.append({
                            "move": move_info["Move"],
                            "improvement": improvement,
                            "evaluation": centipawn
                        })

            formatted_response = f"""🐟 **Tactical Analysis**

**Position:** {fen}

**Current Evaluation:** {base_eval/100:+.1f} pawns

**Tactical Opportunities:**"""

            if tactical_moves:
                for i, tactical in enumerate(tactical_moves, 1):
                    move = tactical["move"]
                    improvement = tactical["improvement"]
                    formatted_response += f"\n{i}. **{move}** - Improves position by {improvement/100:+.1f} pawns"
                
                formatted_response += "\n\n**Possible Tactical Motifs:**"
                if any(t["improvement"] > 300 for t in tactical_moves):
                    formatted_response += "\n• **Major tactical shot** - Large material gain or mate threat"
                if any(200 < t["improvement"] <= 300 for t in tactical_moves):
                    formatted_response += "\n• **Tactical combination** - Winning material or strong attack"
                if any(100 < t["improvement"] <= 200 for t in tactical_moves):
                    formatted_response += "\n• **Tactical improvement** - Small material gain or positional advantage"
            else:
                formatted_response += "\n• No immediate tactical opportunities found"
                formatted_response += "\n• Position appears to be positional in nature"
                formatted_response += "\n• Focus on improving piece coordination and pawn structure"

            formatted_response += f"\n\n*Analysis depth: {depth}*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error finding tactical motifs: {str(e)}")]

    def _evaluate_move_quality(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Evaluate the quality of a specific move."""
        try:
            fen = arguments.get("fen")
            move = arguments.get("move")
            depth = arguments.get("depth", 16)

            if not fen or not move:
                return [TextContent(type="text", text="❌ Error: FEN position and move are required")]

            # Analyze the position before the move
            analysis_before = self.chess_analyzer.analyze_position(fen, depth)
            
            # Find the move in the top moves list to get its evaluation
            move_found = False
            move_eval_cp = None
            
            for move_info in analysis_before["top_moves"]:
                if move_info["Move"] == move:
                    move_eval_cp = move_info.get("Centipawn")
                    move_found = True
                    break
            
            if not move_found:
                # Move not in top moves, might be legal but bad - try to validate it
                import chess
                try:
                    board = chess.Board(fen)
                    chess_move = board.parse_san(move)
                    # Move is legal but not in top moves - it's probably very bad
                    return [TextContent(type="text", text=f"⚠️ Move '{move}' is legal but not among the engine's top moves (likely very poor move)")]
                except:
                    return [TextContent(type="text", text=f"❌ Error: Invalid move '{move}' for the given position")]

            # Compare evaluations properly
            eval_before = analysis_before["evaluation"]
            
            if eval_before["type"] == "cp" and move_eval_cp is not None:
                eval_before_cp = eval_before["value"]  # Current position evaluation
                eval_move_cp = move_eval_cp            # What position will be after this move
                
                # Calculate change (should be <= 0 for any legal move)
                change = eval_move_cp - eval_before_cp
                
                # Get best move info from the original position  
                best_move = analysis_before["best_move"]
                best_move_eval = analysis_before["top_moves"][0].get("Centipawn", eval_before_cp) if analysis_before["top_moves"] else eval_before_cp
                
                # Determine move quality based on how much evaluation dropped
                move_quality = "Excellent"
                if change <= -200:
                    move_quality = "Blunder"
                elif change <= -100:
                    move_quality = "Mistake"  
                elif change <= -50:
                    move_quality = "Inaccuracy"
                elif change <= -10:
                    move_quality = "Good"
                else:
                    move_quality = "Excellent"  # Very close to best
                
                # Calculate loss compared to best move
                best_move_loss = best_move_eval - eval_move_cp
                
                formatted_response = f"""🐟 **Move Quality Evaluation**

**Position:** {fen}
**Move Played:** {move}

**Move Quality:** {move_quality}
**Evaluation Change:** {change/100:+.1f} pawns

**Before Move:** {eval_before_cp/100:+.1f} pawns
**After Move:** {eval_move_cp/100:+.1f} pawns

**Best Move:** {best_move}  
**Best Move Would Give:** {best_move_eval/100:+.1f} pawns
**Loss vs Best Move:** {best_move_loss/100:.1f} pawns"""

                if move_quality in ["Blunder", "Mistake"]:
                    formatted_response += f"\n\n**Improvement:** Consider {best_move} instead"
                elif move_quality == "Inaccuracy":
                    formatted_response += f"\n\n**Note:** {best_move} would be slightly better"
                else:
                    formatted_response += f"\n\n**Analysis:** Your move is close to the best option!"

            else:
                # Handle mate evaluations
                formatted_response = f"""🐟 **Move Quality Evaluation**

**Position:** {fen}
**Move Played:** {move}

**Before Move:** {eval_before}
**After Move:** {eval_after}

**Note:** Position involves mate threats - analysis is complex"""

            formatted_response += f"\n\n*Analysis depth: {depth}*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error evaluating move quality: {str(e)}")]

    def _analyze_endgame(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Specialized endgame analysis."""
        try:
            fen = arguments.get("fen")
            depth = arguments.get("depth", 25)

            if not fen:
                return [TextContent(type="text", text="❌ Error: FEN position is required")]

            # Count pieces to determine if it's an endgame
            import chess
            board = chess.Board(fen)
            piece_count = len([p for p in board.piece_map().values()])
            
            if piece_count > 12:
                return [TextContent(type="text", text="❌ Warning: This appears to be a middlegame position (>12 pieces). Use 'analyze_position' for middlegame analysis.")]

            analysis = self.chess_analyzer.analyze_position(fen, depth)
            explanation = self.chess_analyzer.get_position_explanation(fen)

            # Try to get principal variation for endgame planning
            try:
                pv_result = self.chess_analyzer.get_principal_variation(fen, depth, 8)
                pv_line = ' '.join(pv_result['pv_moves'][:6])  # Show first 6 moves
            except:
                pv_line = "Unable to calculate"

            eval_info = analysis["evaluation"]
            if eval_info["type"] == "cp":
                eval_text = f"{eval_info['value']/100:+.1f} pawns"
                if abs(eval_info["value"]) < 50:
                    result_prediction = "Likely draw with accurate play"
                elif eval_info["value"] > 200:
                    result_prediction = "White should win with accurate technique"
                elif eval_info["value"] < -200:
                    result_prediction = "Black should win with accurate technique"
                else:
                    advantage_side = "White" if eval_info["value"] > 0 else "Black"
                    result_prediction = f"{advantage_side} has winning chances"
            elif eval_info["type"] == "mate":
                moves = eval_info["value"]
                side = "White" if moves > 0 else "Black"
                eval_text = f"Mate in {abs(moves)} for {side}"
                result_prediction = f"{side} wins by force"
            else:
                eval_text = "Unknown evaluation"
                result_prediction = "Unable to determine outcome"

            formatted_response = f"""🐟 **Endgame Analysis**

**Position:** {fen}
**Piece Count:** {piece_count} pieces

**Evaluation:** {eval_text}
**Outcome Prediction:** {result_prediction}

**Best Move:** {analysis['best_move'] or 'No legal moves'}
**Explanation:** {explanation}

**Recommended Continuation:** {pv_line}

**Endgame Principles:**"""

            # Add endgame-specific advice based on material
            if piece_count <= 6:
                formatted_response += "\n• King activity is crucial in simple endgames"
                formatted_response += "\n• Centralize your king when possible"
                
            if any(piece.piece_type == chess.PAWN for piece in board.piece_map().values()):
                formatted_response += "\n• Push passed pawns when safe"
                formatted_response += "\n• Use your king to support pawn advancement"
                
            if any(piece.piece_type in [chess.ROOK, chess.QUEEN] for piece in board.piece_map().values()):
                formatted_response += "\n• Keep heavy pieces active"
                formatted_response += "\n• Cut off the enemy king when possible"

            formatted_response += f"\n\n*Deep analysis depth: {depth}*"

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error analyzing endgame: {str(e)}")]
