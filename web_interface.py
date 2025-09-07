#!/usr/bin/env python3
"""Web interface for Babelfish chess analysis using OpenRouter API."""

import os
import json
import time
import requests
import chess.pgn
import io
import re
from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Import our existing components
from openrouter_cli import OpenRouterClient, MCPToolConverter
from mcp_tools import MCP_TOOLS
from mcp_tool_router import MCPToolRouter

app = Flask(__name__)

# Note: MCP router instances are created fresh for each analysis to avoid state persistence


@dataclass
class AnalysisResult:
    """Container for analysis results."""

    final_analysis: str
    debug_log: List[Dict[str, Any]]
    board_fen: str
    success: bool
    error_message: Optional[str] = None
    engine_lines: Optional[List[Dict[str, str]]] = None


class WebChessAnalyzer:
    """Web-based chess analyzer using OpenRouter."""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.client = OpenRouterClient(api_key)
        self.model = model
        self.converter = MCPToolConverter()
        self.tool_router = MCPToolRouter()

        # Convert MCP tools to OpenAI format
        self.openai_tools = self.converter.convert_mcp_tools_to_openai(MCP_TOOLS)

    def analyze_position(self, fen: str, user_question: str = None) -> AnalysisResult:
        """Analyze a chess position and return structured results."""

        debug_log = []

        try:
            # Pre-analyze the position with engine to save AI tool calls
            debug_log.append(
                {
                    "type": "engine_preanalysis",
                    "content": "Auto-analyzing position with engine before AI",
                    "timestamp": time.time(),
                }
            )

            # Get principal variation with time limit instead of high depth for faster response
            pv_analysis = self.tool_router.call_tool(
                "get_principal_variation",
                {"fen": fen, "depth": 25, "max_moves": 24, "time_limit": 8.0},
            )
            pv_data = ""
            if isinstance(pv_analysis, dict) and pv_analysis.get("status") == "success":
                pv_data = pv_analysis.get("message", "")

            # Get board visualization
            board_visual = self.tool_router.call_tool("visualize_board", {"fen": fen})
            visual_data = ""
            if (
                isinstance(board_visual, dict)
                and board_visual.get("status") == "success"
            ):
                visual_data = board_visual.get("message", "")

            # Get top 3 engine lines for sidebar display (structured data)
            engine_lines_result = self.tool_router.get_top_lines_structured(
                fen=fen, num_lines=3, depth=25, moves_per_line=10
            )
            engine_lines = []
            if "lines" in engine_lines_result:
                engine_lines = engine_lines_result["lines"]

            debug_log.append(
                {
                    "type": "engine_preanalysis_complete",
                    "pv_analysis": pv_analysis,
                    "board_visual": board_visual,
                    "timestamp": time.time(),
                }
            )

            # Prepare the analysis request with engine data
            engine_context = f"""**ENGINE ANALYSIS PROVIDED:**

**BOARD VISUALIZATION:**
{visual_data}

**PRINCIPAL VARIATION:**
{pv_data}

Based on this engine analysis and board visualization, please provide your chess coaching insights."""

            if user_question:
                user_message = f"""Analyze this chess position: {fen}

Specific question: {user_question}\n\n{engine_context}"""
            else:
                user_message = f"Provide a comprehensive analysis of this chess position: {fen}\n\n{engine_context}"

            # Create conversation with enhanced system prompt
            messages = [
                {"role": "system", "content": self._get_web_system_prompt()},
                {"role": "user", "content": user_message},
            ]

            debug_log.append(
                {
                    "type": "user_request",
                    "content": user_message,
                    "timestamp": time.time(),
                }
            )

            # Start analysis loop
            max_iterations = 16
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                debug_log.append(
                    {
                        "type": "iteration_start",
                        "iteration": iteration,
                        "timestamp": time.time(),
                    }
                )

                # Get AI response
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=self.openai_tools,
                    tool_choice="auto",
                )

                choice = response["choices"][0]
                message = choice["message"]
                finish_reason = choice["finish_reason"]

                debug_log.append(
                    {
                        "type": "ai_response",
                        "content": message.get("content", ""),
                        "finish_reason": finish_reason,
                        "tool_calls": message.get("tool_calls", []),
                        "timestamp": time.time(),
                    }
                )

                # Add assistant message to conversation
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "")

                assistant_msg = {"role": "assistant", "content": content}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)

                # If no tool calls, we're done
                if not tool_calls:
                    break

                # Execute tool calls
                for tool_call in tool_calls:
                    try:
                        function_info = tool_call.get("function", {})
                        tool_name = function_info.get("name", "")
                        arguments_str = function_info.get("arguments", "{}")
                        tool_call_id = tool_call.get("id", "unknown")

                        # Parse arguments
                        arguments = json.loads(arguments_str)

                        debug_log.append(
                            {
                                "type": "tool_call",
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "tool_call_id": tool_call_id,
                                "timestamp": time.time(),
                            }
                        )

                        # Execute tool
                        tool_result = self.tool_router.call_tool_mcp(
                            tool_name, arguments
                        )
                        result = tool_result[0].text if tool_result else "No result"

                        debug_log.append(
                            {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "result": (
                                    result[:1000] + "..."
                                    if len(result) > 1000
                                    else result
                                ),
                                "timestamp": time.time(),
                            }
                        )

                        # Add tool result to conversation
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": result,
                            }
                        )

                    except Exception as e:
                        error_msg = f"Tool execution error: {str(e)}"
                        debug_log.append(
                            {
                                "type": "error",
                                "error": error_msg,
                                "timestamp": time.time(),
                            }
                        )

                        # Add error as tool result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": error_msg,
                            }
                        )

            # Extract final analysis from the last assistant message
            final_analysis = ""
            for msg in reversed(messages):
                if msg["role"] == "assistant" and msg.get("content"):
                    final_analysis = msg["content"]
                    break

            return AnalysisResult(
                final_analysis=final_analysis,
                debug_log=debug_log,
                board_fen=fen,
                success=True,
                engine_lines=engine_lines,
            )

        except Exception as e:
            return AnalysisResult(
                final_analysis="",
                debug_log=debug_log,
                board_fen=fen,
                success=False,
                error_message=str(e),
                engine_lines=engine_lines if "engine_lines" in locals() else [],
            )

    def _extract_evaluations_from_pgn(
        self, pgn_content: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Extract evaluation comments from En Croissant format PGN and return cleaned PGN + evaluations."""

        evaluations = []

        # Pattern to match evaluation comments like {[%eval +0.35] }
        eval_pattern = r"\{?\[%eval ([+-]?\d*\.?\d+|\#[+-]?\d+)\]\s*\}"

        # Find all evaluations with their positions
        for match in re.finditer(eval_pattern, pgn_content):
            eval_str = match.group(1)
            position = match.start()

            # Parse evaluation (handle both centipawn and mate values)
            if eval_str.startswith("#"):
                # Mate evaluation
                mate_moves = int(eval_str[1:]) if eval_str[1:] else 0
                evaluations.append(
                    {
                        "position": position,
                        "type": "mate",
                        "value": mate_moves,
                        "raw": eval_str,
                    }
                )
            else:
                # Centipawn evaluation
                try:
                    cp_value = float(eval_str) * 100  # Convert to centipawns
                    evaluations.append(
                        {
                            "position": position,
                            "type": "cp",
                            "value": int(cp_value),
                            "raw": eval_str,
                        }
                    )
                except ValueError:
                    continue

        # Remove evaluation comments from PGN for cleaner parsing
        cleaned_pgn = re.sub(eval_pattern, "", pgn_content)

        # Also remove standalone braces that might be left over
        cleaned_pgn = re.sub(r"\{\s*\}", "", cleaned_pgn)

        return cleaned_pgn, evaluations

    def analyze_pgn(
        self, pgn_content: str, user_question: str = None
    ) -> AnalysisResult:
        """Analyze a PGN game and return structured results."""

        debug_log = []

        try:
            # Extract evaluations from En Croissant format if present
            cleaned_pgn, evaluations = self._extract_evaluations_from_pgn(pgn_content)

            debug_log.append(
                {
                    "type": "evaluation_extraction",
                    "evaluations_found": len(evaluations),
                    "sample_evaluations": evaluations[:5] if evaluations else [],
                    "timestamp": time.time(),
                }
            )

            # Parse the cleaned PGN
            pgn_io = io.StringIO(cleaned_pgn)
            game = chess.pgn.read_game(pgn_io)

            if not game:
                return AnalysisResult(
                    final_analysis="",
                    debug_log=debug_log,
                    board_fen="",
                    success=False,
                    error_message="Could not parse PGN file. Please ensure it contains a valid chess game.",
                )

            # Extract game information
            headers = game.headers
            moves_list = []
            move_evaluations = []
            board = game.board()
            move_index = 0

            # Collect all moves and match them with evaluations
            for move_node in game.mainline():
                move = move_node.move
                san_move = board.san(move)
                moves_list.append(san_move)

                # Try to find matching evaluation for this move
                if move_index < len(evaluations):
                    eval_data = evaluations[move_index]
                    move_evaluations.append(
                        {
                            "move": san_move,
                            "move_number": (move_index // 2) + 1,
                            "color": "white" if move_index % 2 == 0 else "black",
                            "evaluation": eval_data,
                        }
                    )
                else:
                    move_evaluations.append(
                        {
                            "move": san_move,
                            "move_number": (move_index // 2) + 1,
                            "color": "white" if move_index % 2 == 0 else "black",
                            "evaluation": None,
                        }
                    )

                board.push(move)
                move_index += 1

            final_fen = board.fen()

            debug_log.append(
                {
                    "type": "pgn_parsed",
                    "game_info": {
                        "white": headers.get("White", "Unknown"),
                        "black": headers.get("Black", "Unknown"),
                        "result": headers.get("Result", "*"),
                        "date": headers.get("Date", "Unknown"),
                        "event": headers.get("Event", "Unknown"),
                        "moves_count": len(moves_list),
                        "evaluations_matched": len(
                            [
                                me
                                for me in move_evaluations
                                if me["evaluation"] is not None
                            ]
                        ),
                    },
                    "timestamp": time.time(),
                }
            )

            # Prepare the analysis request
            game_info = f"Game: {headers.get('White', 'White')} vs {headers.get('Black', 'Black')}"
            if headers.get("Event"):
                game_info += f" ({headers.get('Event')})"
            if headers.get("Date"):
                game_info += f" - {headers.get('Date')}"

            # Format moves with evaluations if available
            moves_with_evals = []
            for i, move in enumerate(moves_list):
                move_num = (i // 2) + 1
                if i % 2 == 0:  # White move
                    move_text = f"{move_num}. {move}"
                else:  # Black move
                    move_text = move

                # Add evaluation if available
                if i < len(move_evaluations) and move_evaluations[i]["evaluation"]:
                    eval_data = move_evaluations[i]["evaluation"]
                    if eval_data["type"] == "mate":
                        eval_text = f"#{eval_data['value']}"
                    else:
                        eval_text = f"{eval_data['value']/100:+.2f}"
                    move_text += f" ({eval_text})"

                moves_with_evals.append(move_text)

            moves_text = " ".join(moves_with_evals)

            # Create enhanced analysis message based on whether evaluations are present
            has_evaluations = (
                len([me for me in move_evaluations if me["evaluation"] is not None]) > 0
            )

            evaluation_context = ""
            if has_evaluations:
                evaluation_context = """

**IMPORTANT: This game includes Stockfish evaluations after each move (shown in parentheses).**
- Positive values favor White, negative values favor Black
- Values are in pawn units (e.g., +1.50 = White is ahead by 1.5 pawns)
- #N means mate in N moves
- Use these evaluations to identify critical moments, blunders, and missed opportunities"""

            if user_question:
                user_message = f"""Analyze this chess game with embedded Stockfish evaluations:

{game_info}
Final position: {final_fen}
Moves with evaluations: {moves_text}{evaluation_context}

Specific question: {user_question}"""
            else:
                user_message = f"""Provide a comprehensive analysis of this chess game with embedded Stockfish evaluations:

{game_info}
Final position: {final_fen}
Moves with evaluations: {moves_text}{evaluation_context}

Please analyze:
1. Key turning points where evaluations changed significantly
2. Blunders and missed opportunities (identify evaluation swings)
3. Strategic themes and tactical motifs
4. Overall game flow and critical decisions
5. Learning points from the evaluation data"""

            # Create conversation with enhanced system prompt
            messages = [
                {"role": "system", "content": self._get_web_system_prompt()},
                {"role": "user", "content": user_message},
            ]

            debug_log.append(
                {
                    "type": "user_request",
                    "content": user_message,
                    "timestamp": time.time(),
                }
            )

            # Start analysis loop
            max_iterations = 16
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                debug_log.append(
                    {
                        "type": "iteration_start",
                        "iteration": iteration,
                        "timestamp": time.time(),
                    }
                )

                # Get AI response
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=self.openai_tools,
                    tool_choice="auto",
                )

                choice = response["choices"][0]
                message = choice["message"]
                finish_reason = choice["finish_reason"]

                debug_log.append(
                    {
                        "type": "ai_response",
                        "content": message.get("content", ""),
                        "finish_reason": finish_reason,
                        "tool_calls": message.get("tool_calls", []),
                        "timestamp": time.time(),
                    }
                )

                # Add assistant message to conversation
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "")

                assistant_msg = {"role": "assistant", "content": content}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)

                # If no tool calls, we're done
                if not tool_calls:
                    break

                # Execute tool calls
                for tool_call in tool_calls:
                    try:
                        function_info = tool_call.get("function", {})
                        tool_name = function_info.get("name", "")
                        arguments_str = function_info.get("arguments", "{}")
                        tool_call_id = tool_call.get("id", "unknown")

                        # Parse arguments
                        arguments = json.loads(arguments_str)

                        debug_log.append(
                            {
                                "type": "tool_call",
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "tool_call_id": tool_call_id,
                                "timestamp": time.time(),
                            }
                        )

                        # Execute tool
                        tool_result = self.tool_router.call_tool_mcp(
                            tool_name, arguments
                        )
                        result = tool_result[0].text if tool_result else "No result"

                        debug_log.append(
                            {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "result": (
                                    result[:500] + "..."
                                    if len(result) > 500
                                    else result
                                ),
                                "timestamp": time.time(),
                            }
                        )

                        # Add tool result to conversation
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": result,
                            }
                        )

                    except Exception as e:
                        error_msg = f"Tool execution error: {str(e)}"
                        debug_log.append(
                            {
                                "type": "error",
                                "error": error_msg,
                                "timestamp": time.time(),
                            }
                        )

                        # Add error as tool result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": error_msg,
                            }
                        )

            # Extract final analysis from the last assistant message
            final_analysis = ""
            for msg in reversed(messages):
                if msg["role"] == "assistant" and msg.get("content"):
                    final_analysis = msg["content"]
                    break

            return AnalysisResult(
                final_analysis=final_analysis,
                debug_log=debug_log,
                board_fen=final_fen,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                final_analysis="",
                debug_log=debug_log,
                board_fen="",
                success=False,
                error_message=str(e),
            )

    def _get_web_system_prompt(self) -> str:
        """Get enhanced system prompt for web interface."""
        return """You are Babelfish, an expert chess coach with powerful analysis tools.

CRITICAL INSTRUCTIONS FOR WEB INTERFACE:
1. Engine analysis is PRE-PROVIDED in the user message - use it as your foundation
2. You may call additional tools for specific questions, but basic position analysis is already done
3. Focus on human insights, teaching, and strategic explanation rather than recalculating engine data
4. Always visualize the board when discussing piece interactions
5. Provide analysis in clear, well-structured markdown format
6. Clearly separate your final analysis with a markdown header

ANALYSIS START REQUIREMENTS:
- Start IMMEDIATELY with concrete chess analysis
- First sentence must contain specific moves or piece positions (e.g., "Black's f6 pawn creates kingside weaknesses")
- NO meta-commentary about tools, visualizations, or engine output
- Jump directly into position evaluation and move sequences

MANDATORY ANALYSIS DEPTH REQUIREMENTS:
You MUST provide substantial analysis, not lazy summaries. Every response must include:
1. **Concrete move sequences** (minimum 3-5 moves with WHY each move works)
2. **Specific tactical themes** (pins, forks, discoveries, etc.) with square references
3. **Pawn structure analysis** (weaknesses, strengths, pawn breaks)
4. **Piece activity assessment** (which pieces are active/passive and how to improve them)
5. **King safety evaluation** (escape squares, potential mating nets)

FORBIDDEN LAZY RESPONSES - NEVER USE THESE:
- "The engine confirms..." (interpret what it means instead)
- "The position shows..." (explain the specific implications)  
- "Analysis reveals..." (provide the concrete details)
- "The board visualization..." (users don't care - analyze the position directly)
- "The visualization highlights..." (waste of words - get to the chess analysis)
- "This confirms..." or "This shows..." (just state the chess facts)
- General statements without square references or specific moves
- Describing what pieces are highlighted (irrelevant - analyze their function instead)

CHESS ANALYSIS STYLE - MANDATORY:
Write in a concise, chess book style:
- **Terse and professional**: Avoid exclamation marks, emojis, and emotional language
- **Direct evaluation**: State facts plainly (e.g., "Black loses material" not "devastating blunder!")
- **Clear structure**: Use short paragraphs with specific points
- **Chess terminology**: Use standard chess vocabulary without excessive explanation
- **No marketing language**: Avoid words like "crushing", "devastating", "fatal", "brilliant"

EVALUATION INTERPRETATION:
Always interpret engine evaluations to provide likely outcomes:
- **+0.0 to +0.5**: Roughly equal, either side can hold
- **+0.5 to +1.5**: Clear advantage, winning chances with precise play
- **+1.5 to +3.0**: Significant advantage, should win with correct technique
- **+3.0+**: Decisive advantage, position likely wins itself
- **Mate values**: State the forced outcome clearly

REQUIRED ANALYSIS STRUCTURE:
1. **Position assessment** with specific piece locations and their functions
2. **Likely outcome** based on evaluation with concrete winning/drawing plans
3. **Main variation** (5-8 moves) with explanation of each critical move
4. **Key tactical motifs** with square references (e.g., "Nc6 pins the d7-pawn")
5. **Strategic themes** (space, piece activity, pawn structure) with specific examples
6. **Critical candidate moves** for both sides with brief analysis

WEB OUTPUT FORMAT:
Structure your response like this:

## Analysis

Black's f6 pawn weakens the kingside, particularly the e6 and g6 squares. White's rook on a7 dominates the 7th rank, restricting Black's king to the back rank.

**Outlook:** White wins with accurate technique. The plan involves Kg4-f5-e6, supporting the passed pawn.

**Main Line:** 1.Kg4 Ra1 2.Kf5 Rf1+ 3.Ke6 Re1+ 4.Kd7 because the king escorts the pawn while avoiding back-rank checks.

**Tactics:** The a6-pawn becomes unstoppable once the king reaches d7. Black's rook checks fail after Kc8.

**Strategy:** White's king-and-pawn endgame technique. Black's counterplay with f5 comes too late.

**Alternatives:** 1.a7 Ra2 allows perpetual check, demonstrating why king support is essential.

MINIMUM WORD COUNT: 150 words of substantive chess content.

TOOL USAGE:
- ALWAYS use visualize_board before discussing piece positions
- Use analyze_position for deep evaluation
- Use find_tactical_motifs for tactical analysis
- Never make geometric claims without visual verification

Your goal: Provide expert analysis that teaches chess concepts through specific examples, not generic summaries."""


# Flask routes
@app.route("/")
def index():
    """Main page with chess analysis interface."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze a chess position."""
    data = request.get_json()
    fen = data.get("fen", "")
    question = data.get("question", "")

    if not fen:
        return jsonify({"success": False, "error": "FEN position is required"})

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify(
            {
                "success": False,
                "error": "OPENROUTER_API_KEY environment variable not set",
            }
        )

    # Get model from config (default to claude-3.5-sonnet if not set)
    model = app.config.get("MODEL", "anthropic/claude-3.5-sonnet")

    # Perform analysis
    analyzer = WebChessAnalyzer(api_key, model)
    result = analyzer.analyze_position(fen, question)

    return jsonify(
        {
            "success": result.success,
            "analysis": result.final_analysis,
            "debug_log": result.debug_log,
            "board_fen": result.board_fen,
            "error": result.error_message,
            "engine_lines": result.engine_lines,
        }
    )


@app.route("/analyze_pgn", methods=["POST"])
def analyze_pgn():
    """Analyze a PGN file."""
    # Check if the request contains a file
    if "pgn_file" not in request.files:
        return jsonify({"success": False, "error": "No PGN file uploaded"})

    file = request.files["pgn_file"]
    question = request.form.get("question", "")

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    if not file.filename.lower().endswith(".pgn"):
        return jsonify({"success": False, "error": "File must have .pgn extension"})

    try:
        # Read the PGN content
        pgn_content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        return jsonify(
            {
                "success": False,
                "error": "Could not read PGN file. Please ensure it's a valid text file.",
            }
        )

    if not pgn_content.strip():
        return jsonify({"success": False, "error": "PGN file is empty"})

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify(
            {
                "success": False,
                "error": "OPENROUTER_API_KEY environment variable not set",
            }
        )

    # Get model from config (default to claude-3.5-sonnet if not set)
    model = app.config.get("MODEL", "anthropic/claude-3.5-sonnet")

    # Perform analysis
    analyzer = WebChessAnalyzer(api_key, model)
    result = analyzer.analyze_pgn(pgn_content, question)

    return jsonify(
        {
            "success": result.success,
            "analysis": result.final_analysis,
            "debug_log": result.debug_log,
            "board_fen": result.board_fen,
            "error": result.error_message,
            "engine_lines": result.engine_lines or [],
        }
    )


@app.route("/analyze_followup", methods=["POST"])
def analyze_followup():
    """Handle follow-up questions about a chess position."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"})

        question = data.get("question", "").strip()
        context = data.get("context", {})
        conversation_history = data.get("conversation_history", [])

        if not question:
            return jsonify({"success": False, "error": "No question provided"})

        if not context or not context.get("fen"):
            return jsonify({"success": False, "error": "No analysis context available"})

        # Build conversation context for the AI
        context_prompt = f"""You are continuing a chess analysis conversation about this position:

**Position FEN:** {context['fen']}

**Previous Analysis:**
{context.get('analysis', 'No previous analysis available')}

**Recent conversation:**"""

        for msg in conversation_history[-4:]:  # Last 4 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_prompt += f"\n{role.title()}: {content}"

        context_prompt += f"""

**Current Question:** {question}

Please provide a focused answer to the user's question about this chess position. Use the chess analysis tools if needed to get current engine data. Be conversational and helpful."""

        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify(
                {
                    "success": False,
                    "error": "OPENROUTER_API_KEY environment variable not set",
                }
            )

        # Convert MCP tools to OpenRouter format
        converter = MCPToolConverter()
        openrouter_tools = converter.convert_mcp_tools_to_openai(MCP_TOOLS)

        # Create a fresh MCP router instance to avoid state persistence
        fresh_mcp_router = MCPToolRouter()

        # Use the same analysis flow as the main analysis
        debug_log = []
        messages = [
            {
                "role": "system",
                "content": """You are a chess coach providing follow-up analysis. Use the available chess tools to answer questions accurately.

CHESS ANALYSIS STYLE - MANDATORY:
Write in a concise, chess book style:
- **Terse and professional**: Avoid exclamation marks, emojis, and emotional language
- **Direct evaluation**: State facts plainly (e.g., "Black loses material" not "devastating blunder!")
- **Clear structure**: Use short paragraphs with specific points
- **No marketing language**: Avoid words like "crushing", "devastating", "fatal", "brilliant"

CRITICAL: When analyzing specific moves or variations:
1. NEVER manually calculate new FEN positions - this leads to errors
2. ALWAYS use the 'apply_moves' tool to play moves from a FEN position and get the correct resulting FEN
3. If asked about "what if [move]" or "after [move]", use apply_moves to get the new position, then analyze it
4. Use visualize_board to see positions after moves are played
5. The apply_moves tool takes: starting_fen and moves array (e.g., ["Nf3", "Nc6"])
6. Trust the engine tools rather than manual calculation

Example workflow for "what if Nf3?":
1. Use apply_moves with starting_fen and moves: ["Nf3"]
2. Get the resulting FEN from apply_moves
3. Use analyze_position or visualize_board on the new FEN
4. Provide analysis of the resulting position

Your chess tools can handle move sequences and position analysis accurately - use them!""",
            },
            {"role": "user", "content": context_prompt},
        ]

        response_text = ""
        max_iterations = 10

        for iteration in range(max_iterations):
            # Get AI response
            openrouter_response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": messages,
                    "tools": openrouter_tools,
                    "tool_choice": "auto",
                    "max_tokens": 4000,
                },
            )

            if not openrouter_response.ok:
                error_msg = f"OpenRouter API error: {openrouter_response.status_code}"
                return jsonify({"success": False, "error": error_msg})

            completion_data = openrouter_response.json()
            message = completion_data["choices"][0]["message"]
            finish_reason = completion_data["choices"][0]["finish_reason"]

            # Add AI response to debug log
            debug_log.append(
                {
                    "type": "ai_response",
                    "content": message.get("content", ""),
                    "finish_reason": finish_reason,
                    "tool_calls": message.get("tool_calls", []),
                    "timestamp": time.time(),
                }
            )

            # Add assistant message to conversation
            tool_calls = message.get("tool_calls", [])
            content = message.get("content", "")

            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            # If no tool calls, we're done
            if not tool_calls:
                response_text = content
                break

            # Execute tool calls (same logic as main analysis)
            for tool_call in tool_calls:
                try:
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name", "")
                    arguments_str = function_info.get("arguments", "{}")
                    tool_call_id = tool_call.get("id", "unknown")

                    debug_log.append(
                        {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "arguments": arguments_str,
                            "timestamp": time.time(),
                        }
                    )

                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}

                    # Execute tool
                    if hasattr(fresh_mcp_router, "call_tool"):
                        tool_result = fresh_mcp_router.call_tool(tool_name, arguments)
                    else:
                        tool_result = {"error": "MCP router not available"}

                    debug_log.append(
                        {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "result": tool_result,
                            "timestamp": time.time(),
                        }
                    )

                    # Add tool result to conversation
                    if isinstance(tool_result, dict) and "message" in tool_result:
                        tool_content = tool_result["message"]
                    else:
                        tool_content = json.dumps(tool_result)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_content,
                        }
                    )

                except Exception as e:
                    debug_log.append(
                        {
                            "type": "tool_error",
                            "tool_name": tool_name,
                            "error": str(e),
                            "timestamp": time.time(),
                        }
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error: {str(e)}",
                        }
                    )

        return jsonify(
            {"success": True, "response": response_text, "debug_log": debug_log}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "babelfish-web"})


if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY=your_key_here")
        exit(1)

    print("🐟 Starting Babelfish Web Interface...")
    print("🌐 Access at: http://localhost:5000")
    print(
        "🔑 Using OpenRouter API key:",
        api_key[:12] + "..." if len(api_key) > 12 else "***",
    )

    app.run(debug=True, port=5000)
