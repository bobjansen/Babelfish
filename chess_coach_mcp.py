#!/usr/bin/env python3
"""Babelfish Chess Coach MCP Server - Comprehensive Chess Analysis for Players."""

import asyncio
import chess
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.types import TextContent, Tool
from babelfish.chess_analyzer import ChessAnalyzer


async def main():
    # Create server
    server = Server("babelfish-coach")
    analyzer = ChessAnalyzer()

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available chess coaching tools."""
        return [
            Tool(
                name="analyze_position",
                description="Analyze a chess position in FEN notation. Returns engine evaluation (in centipawns or mate distance), top 3 best moves with evaluations, strategic guidance based on game phase (opening/middlegame/endgame), and human-readable position explanation. Use this for comprehensive position assessment.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation (copy from chess.com, lichess, or any chess app)",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis strength: 10=fast, 15=standard, 20=deep (default: 15)",
                            "default": 15,
                            "minimum": 5,
                            "maximum": 25,
                        },
                    },
                    "required": ["fen"],
                },
            ),
            Tool(
                name="evaluate_move",
                description="Evaluate the quality of a specific move in a given position. Takes a FEN and a move in algebraic notation, returns move rating (Excellent/Good/Questionable/Bad/Blunder), evaluation change in centipawns, comparison with engine's preferred move, and alternative suggestions. Use this to assess if a particular move is strong or weak.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The position before the move (FEN notation)",
                        },
                        "move": {
                            "type": "string",
                            "description": "The move to evaluate in algebraic notation (e.g., 'Nf3', 'exd5', 'O-O')",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis depth (default: 15)",
                            "default": 15,
                            "minimum": 10,
                            "maximum": 20,
                        },
                    },
                    "required": ["fen", "move"],
                },
            ),
            Tool(
                name="find_tactics",
                description="Identify tactical opportunities and patterns in a chess position. Analyzes position with high depth (18) to find forced sequences, mate threats, major tactical advantages, and tactical motifs. Returns evaluation assessment, key tactical moves with move types (capture, check, promotion), and educational guidance on common tactical patterns. Use when position may contain tactical elements.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The position to analyze for tactics (FEN notation)",
                        }
                    },
                    "required": ["fen"],
                },
            ),
            Tool(
                name="opening_analysis",
                description="Analyze early-game positions (typically moves 1-15) and provide opening-specific guidance. Returns position evaluation, recommended moves, opening principles based on move number, piece development assessment for both sides, and strategic advice. Optionally accepts moves_played array to help identify opening line. Use for positions in the opening phase of the game.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The opening position to analyze (FEN notation)",
                        },
                        "moves_played": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The moves that led to this position (optional, helps with opening identification)",
                            "default": [],
                        },
                    },
                    "required": ["fen"],
                },
            ),
            Tool(
                name="endgame_guidance",
                description="Analyze endgame positions (few pieces remaining) with specialized endgame techniques. Uses deep analysis (depth 20), identifies material imbalance, provides endgame-specific guidance based on piece configuration (K+P vs K, K+Q vs K, etc.), and gives practical endgame principles. Use for positions with limited material where endgame technique is important.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The endgame position to analyze (FEN notation)",
                        }
                    },
                    "required": ["fen"],
                },
            ),
            Tool(
                name="explore_moves",
                description="Test multiple candidate moves in a position and compare their outcomes. Takes a FEN and array of moves in algebraic notation, validates each move's legality, calculates resulting positions and evaluations, rates move quality, identifies move properties (captures, checks, promotions), and ranks moves by strength. Essential for testing chess ideas before making conclusions. Use this when you want to explore multiple move options and see their actual consequences.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The starting position (FEN notation)",
                        },
                        "candidate_moves": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of moves to try in algebraic notation (e.g., ['Nf3', 'e4', 'O-O', 'd4']). Include 3-5 candidate moves to explore.",
                            "minItems": 1,
                            "maxItems": 8,
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis depth for each resulting position (default: 12)",
                            "default": 12,
                            "minimum": 8,
                            "maximum": 18,
                        },
                    },
                    "required": ["fen", "candidate_moves"],
                },
            ),
            Tool(
                name="analyze_variations",
                description="Analyze multiple-move sequences (variations) from a position. Takes a FEN and array of move sequences, where each sequence is 2-4 moves deep. Shows how each variation develops, the final evaluations, and key tactical/positional themes. Perfect for understanding opening lines, tactical sequences, or strategic plans. Use this when you need to see how move sequences play out over multiple moves.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The starting position (FEN notation)",
                        },
                        "variations": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "A sequence of moves (2-4 moves) in algebraic notation",
                            },
                            "description": "List of move sequences to analyze (e.g., [['e4', 'e5'], ['d4', 'd5'], ['Nf3', 'Nf6', 'Bg5']]). Each variation should be 2-4 moves long.",
                            "minItems": 1,
                            "maxItems": 6,
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis depth for final positions (default: 15)",
                            "default": 15,
                            "minimum": 10,
                            "maximum": 20,
                        },
                    },
                    "required": ["fen", "variations"],
                },
            ),
            Tool(
                name="apply_moves",
                description="CRITICAL TOOL: Apply moves to a FEN position to get the correct resulting FEN. Takes a starting FEN and list of moves in algebraic notation, validates each move's legality, and returns the accurate final position. ALWAYS use this tool instead of trying to calculate FEN positions manually - chess position calculation is extremely error-prone and leads to incorrect analysis. This tool is essential for accurate move sequences and position analysis.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "starting_fen": {
                            "type": "string",
                            "description": "The starting chess position in FEN notation",
                        },
                        "moves": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of moves to apply in standard algebraic notation (e.g., ['e4', 'e5', 'Nf3', 'Nc6']). Each move will be validated and applied sequentially.",
                            "minItems": 1,
                            "maxItems": 20,
                        },
                        "show_progression": {
                            "type": "boolean",
                            "description": "Whether to show the position after each move (default: false, only shows final position)",
                            "default": False,
                        },
                    },
                    "required": ["starting_fen", "moves"],
                },
            ),
            Tool(
                name="list_legal_moves",
                description="Generate a complete list of all legal moves in a chess position. Takes a FEN and returns all possible moves in standard algebraic notation, categorized by move type (captures, checks, castling, en passant, promotions, quiet moves). Essential for understanding what moves are actually possible before suggesting or analyzing moves. Use this when you need to know all available options in a position.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation",
                        },
                        "categorize": {
                            "type": "boolean",
                            "description": "Whether to categorize moves by type (captures, checks, etc.) or just return a simple list (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["fen"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle chess coaching tool calls."""
        try:
            if name == "analyze_position":
                return await analyze_position_comprehensive(arguments, analyzer)
            elif name == "evaluate_move":
                return await evaluate_specific_move(arguments, analyzer)
            elif name == "find_tactics":
                return await find_tactical_opportunities(arguments, analyzer)
            elif name == "opening_analysis":
                return await analyze_opening_position(arguments, analyzer)
            elif name == "endgame_guidance":
                return await provide_endgame_guidance(arguments, analyzer)
            elif name == "explore_moves":
                return await explore_candidate_moves(arguments, analyzer)
            elif name == "analyze_variations":
                return await analyze_variations(arguments, analyzer)
            elif name == "apply_moves":
                return await apply_moves_to_fen(arguments, analyzer)
            elif name == "list_legal_moves":
                return await list_legal_moves(arguments, analyzer)
            else:
                return [TextContent(type="text", text="❌ Unknown tool")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {str(e)}")]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="babelfish-coach",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


async def analyze_position_comprehensive(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Provide comprehensive position analysis for chess players."""
    fen = arguments.get("fen")
    depth = arguments.get("depth", 15)

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    try:
        # Get basic analysis
        analysis = analyzer.analyze_position(fen, depth)
        explanation = analyzer.get_position_explanation(fen)

        # Determine game phase
        board = chess.Board(fen)
        piece_count = len([p for p in board.piece_map().values()])

        if piece_count <= 10:
            phase = "Endgame"
        elif piece_count <= 20:
            phase = "Middlegame"
        else:
            phase = "Opening"

        # Format comprehensive analysis
        eval_info = analysis["evaluation"]
        if eval_info["type"] == "cp":
            eval_text = f"{eval_info['value']/100:+.1f} pawns"
            if abs(eval_info["value"]) < 50:
                eval_desc = "Equal position"
            elif eval_info["value"] > 300:
                eval_desc = "Winning advantage for White"
            elif eval_info["value"] < -300:
                eval_desc = "Winning advantage for Black"
            elif eval_info["value"] > 100:
                eval_desc = "Clear advantage for White"
            elif eval_info["value"] < -100:
                eval_desc = "Clear advantage for Black"
            else:
                eval_desc = "Slight advantage"
        else:
            moves = eval_info["value"]
            side = "White" if moves > 0 else "Black"
            eval_text = f"Mate in {abs(moves)}"
            eval_desc = f"Forced mate for {side}"

        response = f"""🎯 **Comprehensive Position Analysis**

**Position Overview:**
• Game Phase: {phase}
• Evaluation: {eval_text} ({eval_desc})
• To Move: {"White" if "w" in fen else "Black"}

**📊 Engine Analysis:**
{explanation}

**🎲 Best Moves & Plans:**"""

        for i, move_info in enumerate(analysis["top_moves"][:3], 1):
            move = move_info["Move"]
            cp = move_info.get("Centipawn")
            cp_text = f"{cp/100:+.1f}" if cp is not None else "0.00"

            if i == 1:
                response += f"\n**{i}. {move}** ({cp_text}) ← Engine's top choice"
            else:
                response += f"\n{i}. {move} ({cp_text})"

        # Add strategic guidance based on position
        if phase == "Opening":
            response += """

**📚 Opening Principles:**
• Develop pieces toward the center
• Control central squares (e4, e5, d4, d5)
• Castle early for king safety
• Don't move the same piece twice without reason"""

        elif phase == "Middlegame":
            response += """

**⚔️ Middlegame Strategy:**
• Look for tactical opportunities (pins, forks, skewers)
• Improve piece coordination and activity
• Create weaknesses in opponent's position
• Consider pawn breaks and space advantage"""

        else:  # Endgame
            response += """

**🏁 Endgame Technique:**
• Activate your king - it's a strong piece in the endgame
• Create passed pawns and support their advance
• Use opposition and key squares in pawn endings
• Centralize pieces and coordinate them"""

        response += f"\n\n*Analysis depth: {depth} • Powered by Stockfish*"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Analysis error: {str(e)}")]


async def evaluate_specific_move(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Evaluate a specific move and provide feedback."""
    fen = arguments.get("fen")
    move = arguments.get("move")
    depth = arguments.get("depth", 15)

    if not fen or not move:
        return [
            TextContent(
                type="text", text="❌ Please provide both FEN position and move"
            )
        ]

    try:
        # Analyze position before move
        before_analysis = analyzer.analyze_position(fen, depth)

        # Try to make the move
        board = chess.Board(fen)
        try:
            chess_move = board.parse_san(move)
            board.push(chess_move)
            after_fen = board.fen()
        except:
            return [TextContent(type="text", text=f"❌ Invalid move: {move}")]

        # Get engine's assessment of the move from top_moves if available
        move_centipawn = None
        for move_info in before_analysis["top_moves"]:
            if move_info["Move"] == move:
                move_centipawn = move_info.get("Centipawn")
                break

        if move_centipawn is not None:
            # Use the engine's direct evaluation of this move
            best_centipawn = before_analysis["top_moves"][0].get("Centipawn", 0)
            eval_change = move_centipawn - best_centipawn

            # For display purposes
            before_display = best_centipawn / 100
            after_display = move_centipawn / 100
        else:
            # Fallback: analyze the position after the move
            after_analysis = analyzer.analyze_position(after_fen, depth)

            before_eval = (
                before_analysis["evaluation"]["value"]
                if before_analysis["evaluation"]["type"] == "cp"
                else 0
            )
            after_eval = (
                after_analysis["evaluation"]["value"]
                if after_analysis["evaluation"]["type"] == "cp"
                else 0
            )

            # Calculate from moving player's perspective
            if "b" in fen:  # Black to move
                eval_change = before_eval - after_eval  # Black wants more negative
                before_display = -before_eval / 100
                after_display = -after_eval / 100
            else:  # White to move
                eval_change = after_eval - before_eval  # White wants more positive
                before_display = before_eval / 100
                after_display = after_eval / 100

        # Get engine's top choice
        best_move = before_analysis["best_move"]
        top_moves = before_analysis["top_moves"]

        # Rate the move
        if abs(eval_change) < 20:
            rating = "Excellent"
            emoji = "🟢"
        elif abs(eval_change) < 50:
            rating = "Good"
            emoji = "🔵"
        elif abs(eval_change) < 100:
            rating = "Questionable"
            emoji = "🟡"
        elif abs(eval_change) < 200:
            rating = "Bad"
            emoji = "🟠"
        else:
            rating = "Blunder"
            emoji = "🔴"

        response = f"""🔍 **Move Evaluation: {move}**

**Rating: {emoji} {rating}**
• Evaluation change: {eval_change/100:+.1f} pawns
• Engine evaluation: {before_display:+.1f} → {after_display:+.1f}

**Engine's Assessment:**"""

        if move == best_move:
            response += "\n✅ This is the engine's top choice!"
        else:
            response += f"\n💡 Engine prefers: **{best_move}**"

            # Show why the engine's move is better
            for move_info in top_moves:
                if move_info["Move"] == move:
                    player_cp = move_info.get("Centipawn", 0)
                    best_cp = top_moves[0].get("Centipawn", 0)
                    if "b" in fen:  # Black to move
                        diff = player_cp - best_cp
                    else:
                        diff = best_cp - player_cp
                    response += f"\n• Your move: {player_cp/100:+.1f}, Best: {best_cp/100:+.1f} (difference: {diff/100:.1f})"
                    break

        response += """

**📚 Alternative Moves:**"""
        for i, move_info in enumerate(top_moves[:3], 1):
            alt_move = move_info["Move"]
            cp = move_info.get("Centipawn", 0)
            if alt_move == move:
                response += f"\n{i}. **{alt_move}** ({cp/100:+.1f}) ← Your move"
            else:
                response += f"\n{i}. {alt_move} ({cp/100:+.1f})"

        # Add tactical/positional feedback
        if rating in ["Bad", "Blunder"]:
            response += """

**🚨 Improvement Tips:**
• Look for tactical motifs (pins, forks, discovered attacks)
• Consider your opponent's threats before moving
• Ensure piece safety and coordination
• Ask: "What does this move accomplish?"""

        response += f"\n\n*Analysis depth: {depth}*"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Evaluation error: {str(e)}")]


async def find_tactical_opportunities(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Find tactical opportunities in the position."""
    fen = arguments.get("fen")

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    try:
        # Analyze with high depth for tactics
        analysis = analyzer.analyze_position(fen, depth=18)

        board = chess.Board(fen)
        to_move = "White" if board.turn else "Black"

        # Check for immediate tactics
        best_move = analysis["best_move"]
        eval_info = analysis["evaluation"]

        response = f"""⚡ **Tactical Analysis**

**Position for {to_move} to move**"""

        # Check if there's a forced mate
        if eval_info["type"] == "mate":
            moves_to_mate = abs(eval_info["value"])
            if eval_info["value"] > 0:
                response += f"\n🎯 **MATE FOUND!** White mates in {moves_to_mate}"
            else:
                response += f"\n🎯 **MATE FOUND!** Black mates in {moves_to_mate}"
            response += f"\nKey move: **{best_move}**"

        else:
            # Look for significant evaluation swings indicating tactics
            cp_value = eval_info["value"]
            if abs(cp_value) > 300:
                response += "\n🎯 **Major Tactical Opportunity!**"
                response += f"\nEvaluation: {cp_value/100:+.1f} pawns"
            elif abs(cp_value) > 150:
                response += "\n⚡ **Tactical Advantage Available**"
                response += f"\nEvaluation: {cp_value/100:+.1f} pawns"
            else:
                response += "\n🔍 **No Major Tactics Found**"
                response += f"\nPosition is relatively balanced: {cp_value/100:+.1f}"

        response += """

**🎲 Key Moves to Consider:**"""

        for i, move_info in enumerate(analysis["top_moves"][:3], 1):
            move = move_info["Move"]
            cp = move_info.get("Centipawn", 0)

            # Try to identify move type
            board_copy = chess.Board(fen)
            try:
                chess_move = board_copy.parse_san(move)

                move_type = ""
                if board_copy.is_capture(chess_move):
                    move_type += "capture "
                if board_copy.gives_check(chess_move):
                    move_type += "check "
                if chess_move.promotion:
                    move_type += "promotion "

                response += f"\n{i}. **{move}** ({cp/100:+.1f}) {move_type}"
            except:
                response += f"\n{i}. **{move}** ({cp/100:+.1f})"

        # Add tactical motif guidance
        response += """

**🧠 Common Tactical Motifs to Look For:**
• **Pins**: Attack a piece that can't move without exposing a more valuable piece
• **Forks**: Attack two or more pieces simultaneously
• **Skewers**: Force a valuable piece to move, exposing a less valuable one
• **Discovered attacks**: Move one piece to reveal an attack from another
• **Double attacks**: Attack two targets at once
• **Deflection**: Force a defending piece away from its duty"""

        if eval_info["type"] != "mate" and abs(cp_value) < 100:
            response += """

**💡 Tactical Training Tips:**
• Calculate concrete variations, don't just rely on intuition
• Always check for opponent's counter-tactics
• Look for forcing moves: checks, captures, threats
• Practice tactical puzzles to sharpen your pattern recognition"""

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Tactical analysis error: {str(e)}")]


async def analyze_opening_position(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Analyze opening positions and provide strategic guidance."""
    fen = arguments.get("fen")
    moves_played = arguments.get("moves_played", [])

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    try:
        analysis = analyzer.analyze_position(fen, depth=12)

        board = chess.Board(fen)
        move_number = board.fullmove_number
        to_move = "White" if board.turn else "Black"

        # Format evaluation properly
        eval_info = analysis["evaluation"]
        if eval_info["type"] == "cp":
            eval_text = f"{eval_info['value']/100:+.1f} pawns"
        else:
            moves = eval_info["value"]
            side = "White" if moves > 0 else "Black"
            eval_text = f"Mate in {abs(moves)} for {side}"

        response = f"""📚 **Opening Analysis**

**Position Info:**
• Move {move_number}, {to_move} to move
• Evaluation: {eval_text}"""

        if moves_played:
            response += f"\n• Opening line: {' '.join(moves_played[:8])}{'...' if len(moves_played) > 8 else ''}"

        response += """

**🎯 Recommended Moves:**"""

        for i, move_info in enumerate(analysis["top_moves"][:3], 1):
            move = move_info["Move"]
            cp = move_info.get("Centipawn", 0)
            response += f"\n{i}. **{move}** ({cp/100:+.1f})"

        # Opening principles based on move number
        if move_number <= 5:
            response += """

**🏗️ Early Opening Principles (Moves 1-5):**
• **Development**: Bring knights and bishops into active squares
• **Center Control**: Fight for central squares (e4, e5, d4, d5)
• **King Safety**: Castle early to protect your king
• **Avoid**: Moving the same piece twice, bringing queen out too early"""

        elif move_number <= 10:
            response += """

**⚔️ Opening Development (Moves 6-10):**
• **Complete development**: Get all minor pieces active
• **Castle if you haven't**: King safety is priority
• **Connect rooks**: Clear the back rank
• **Central pawn breaks**: Look for d4/d5 or e4/e5 advances"""

        else:
            response += """

**🌟 Opening to Middlegame Transition:**
• **Piece improvement**: Optimize piece placement
• **Pawn structure**: Consider pawn breaks and weaknesses
• **Planning**: Identify strategic goals and piece coordination
• **Tactics**: Stay alert for tactical opportunities"""

        # Add piece development analysis
        piece_analysis = analyze_piece_development(board)
        response += """

**🎭 Piece Activity Assessment:**"""
        for color, info in piece_analysis.items():
            response += f"\n• **{color}**: {info['developed']}/8 pieces developed"
            if info["suggestions"]:
                response += f" | Next: {', '.join(info['suggestions'])}"

        response += """

**💡 Strategic Tips:**
• Control key squares with pieces, not just pawns
• Develop with purpose - each move should improve your position
• Don't rush attacks without proper preparation
• Study master games from this opening structure"""

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Opening analysis error: {str(e)}")]


async def provide_endgame_guidance(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Provide endgame guidance and technique."""
    fen = arguments.get("fen")

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    try:
        analysis = analyzer.analyze_position(
            fen, depth=20
        )  # Deep analysis for endgames

        board = chess.Board(fen)
        piece_count = len(
            [p for p in board.piece_map().values() if p.piece_type != chess.KING]
        )

        eval_info = analysis["evaluation"]
        if eval_info["type"] == "cp":
            eval_text = f"{eval_info['value']/100:+.1f} pawns"
        else:
            moves = eval_info["value"]
            side = "White" if moves > 0 else "Black"
            eval_text = f"Mate in {abs(moves)} for {side}"

        response = f"""🏁 **Endgame Guidance**

**Position Assessment:**
• Material: {piece_count} pieces on board (excluding kings)
• Evaluation: {eval_text}
• Best move: **{analysis['best_move']}**

**🎯 Key Moves:**"""

        for i, move_info in enumerate(analysis["top_moves"][:3], 1):
            move = move_info["Move"]
            cp = move_info.get("Centipawn", 0)
            response += f"\n{i}. **{move}** ({cp/100:+.1f})"

        # Endgame-specific guidance based on material
        material_balance = analyze_endgame_material(board)

        if "K+P vs K" in material_balance:
            response += """

**♔ King and Pawn Endgame:**
• **Opposition**: Control key squares to restrict opponent's king
• **Key squares**: Calculate which squares your king must reach
• **Pawn promotion**: Support your pawn's advance to the 8th rank
• **Stalemate tricks**: Be careful not to stalemate in winning positions"""

        elif "K+Q vs K" in material_balance:
            response += """

**♕ Queen vs King Endgame:**
• **Centralize your king**: Bring it up to help the queen
• **Cut off escape**: Use queen to limit opponent king's mobility
• **Avoid stalemate**: Give the opponent king legal moves
• **Basic checkmate**: Learn the systematic mating technique"""

        elif "K+R vs K" in material_balance:
            response += """

**♖ Rook vs King Endgame:**
• **Cut off the king**: Use rook to confine opponent to edge
• **Box method**: Systematically reduce the king's space
• **Avoid stalemate**: Keep opponent's king mobile until mate
• **King activity**: Your king must participate in the mating attack"""

        else:
            response += """

**🎓 General Endgame Principles:**
• **King activity**: The king becomes a fighting piece
• **Passed pawns**: Create and advance them with king support
• **Piece coordination**: Work pieces together harmoniously
• **Calculate precisely**: Endgames reward accurate calculation"""

        # Add practical guidance
        response += """

**💪 Practical Tips:**
• **Opposition**: In pawn endings, try to get the opposition
• **Active pieces**: Keep pieces active and centralized
• **Pawn structure**: Consider pawn majority and weaknesses
• **Time management**: Use remaining time to calculate accurately

**📚 Study Recommendations:**
• Practice basic checkmates (Q+K vs K, R+K vs K)
• Learn key pawn endings and theoretical positions
• Study rook endgames - they're the most common
• Master piece vs pawn endings for practical play"""

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Endgame analysis error: {str(e)}")]


def analyze_piece_development(board: chess.Board) -> dict:
    """Analyze piece development for both sides."""
    result = {}

    for color in [chess.WHITE, chess.BLACK]:
        color_name = "White" if color == chess.WHITE else "Black"
        developed = 0
        suggestions = []

        # Check knights
        knights = board.pieces(chess.KNIGHT, color)
        for knight_square in knights:
            if color == chess.WHITE:
                if knight_square not in [chess.B1, chess.G1]:
                    developed += 1
                elif knight_square == chess.B1:
                    suggestions.append("Nc3 or Nd2")
                elif knight_square == chess.G1:
                    suggestions.append("Nf3 or Ne2")
            else:
                if knight_square not in [chess.B8, chess.G8]:
                    developed += 1
                elif knight_square == chess.B8:
                    suggestions.append("Nc6 or Nd7")
                elif knight_square == chess.G8:
                    suggestions.append("Nf6 or Ne7")

        # Check bishops
        bishops = board.pieces(chess.BISHOP, color)
        for bishop_square in bishops:
            if color == chess.WHITE:
                if bishop_square not in [chess.C1, chess.F1]:
                    developed += 1
            else:
                if bishop_square not in [chess.C8, chess.F8]:
                    developed += 1

        result[color_name] = {
            "developed": developed,
            "suggestions": suggestions[:2],  # Limit suggestions
        }

    return result


def analyze_endgame_material(board: chess.Board) -> str:
    """Analyze material balance for endgame classification."""
    white_pieces = []
    black_pieces = []

    for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))

        if white_count > 0:
            white_pieces.extend([chess.piece_name(piece_type).upper()] * white_count)
        if black_count > 0:
            black_pieces.extend([chess.piece_name(piece_type).upper()] * black_count)

    # Simple material description
    if len(white_pieces) == 1 and len(black_pieces) == 0 and white_pieces[0] == "P":
        return "K+P vs K"
    elif len(white_pieces) == 1 and len(black_pieces) == 0 and white_pieces[0] == "Q":
        return "K+Q vs K"
    elif len(white_pieces) == 1 and len(black_pieces) == 0 and white_pieces[0] == "R":
        return "K+R vs K"
    elif len(black_pieces) == 1 and len(white_pieces) == 0 and black_pieces[0] == "P":
        return "K vs K+P"
    elif len(black_pieces) == 1 and len(white_pieces) == 0 and black_pieces[0] == "Q":
        return "K vs K+Q"
    elif len(black_pieces) == 1 and len(white_pieces) == 0 and black_pieces[0] == "R":
        return "K vs K+R"
    else:
        return f"Complex endgame ({len(white_pieces)+len(black_pieces)} pieces)"


async def explore_candidate_moves(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Explore multiple candidate moves and their resulting positions."""
    fen = arguments.get("fen")
    candidate_moves = arguments.get("candidate_moves", [])
    depth = arguments.get("depth", 12)

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    if not candidate_moves:
        return [
            TextContent(
                type="text", text="❌ Please provide candidate moves to explore"
            )
        ]

    try:
        board = chess.Board(fen)
        to_move = "White" if board.turn else "Black"

        # First analyze the starting position
        start_analysis = analyzer.analyze_position(fen, depth)
        start_eval = (
            start_analysis["evaluation"]["value"]
            if start_analysis["evaluation"]["type"] == "cp"
            else 0
        )

        response = f"""🧪 **Move Exploration Results**

**Starting Position ({to_move} to move):**
• Evaluation: {start_eval/100:+.1f} pawns
• Engine's top choice: **{start_analysis['best_move']}**

**🔍 Candidate Move Analysis:**"""

        move_results = []

        for i, move in enumerate(candidate_moves, 1):
            try:
                # Create a copy of the board to test the move
                test_board = board.copy()

                # Try to parse and make the move
                try:
                    chess_move = test_board.parse_san(move)

                    # Check if move is legal
                    if chess_move not in test_board.legal_moves:
                        response += f"\n\n**{i}. {move}** ❌ ILLEGAL MOVE"
                        continue

                    # First try to get evaluation from engine's top_moves analysis
                    move_centipawn = None
                    for move_info in start_analysis["top_moves"]:
                        if move_info["Move"] == move:
                            move_centipawn = move_info.get("Centipawn")
                            break

                    if move_centipawn is not None:
                        # Use engine's direct evaluation
                        best_centipawn = start_analysis["top_moves"][0].get(
                            "Centipawn", 0
                        )
                        eval_change = move_centipawn - best_centipawn
                        result_eval = move_centipawn
                    else:
                        # Fallback: analyze the position after making the move
                        test_board.push(chess_move)
                        resulting_fen = test_board.fen()
                        result_analysis = analyzer.analyze_position(
                            resulting_fen, depth
                        )
                        result_eval = (
                            result_analysis["evaluation"]["value"]
                            if result_analysis["evaluation"]["type"] == "cp"
                            else 0
                        )

                        # Calculate evaluation change from moving player's perspective
                        if not board.turn:  # Black to move
                            eval_change = start_eval - (
                                -result_eval
                            )  # Black wants more negative
                        else:  # White to move
                            eval_change = (
                                result_eval - start_eval
                            )  # White wants more positive

                    # Always get the resulting FEN and analysis for display
                    if move_centipawn is not None:
                        test_board.push(chess_move)
                        resulting_fen = test_board.fen()
                        # Get analysis for the engine response
                        result_analysis = analyzer.analyze_position(
                            resulting_fen, depth
                        )

                    # Determine move quality
                    if abs(eval_change) < 25:
                        quality = "🟢 Excellent"
                    elif abs(eval_change) < 60:
                        quality = "🔵 Good"
                    elif abs(eval_change) < 120:
                        quality = "🟡 Questionable"
                    elif abs(eval_change) < 250:
                        quality = "🟠 Poor"
                    else:
                        quality = "🔴 Blunder"

                    # Check for special move properties
                    move_properties = []
                    if board.is_capture(chess_move):
                        captured_piece = board.piece_at(chess_move.to_square)
                        move_properties.append(
                            f"captures {chess.piece_name(captured_piece.piece_type) if captured_piece else 'piece'}"
                        )
                    if board.gives_check(chess_move):
                        move_properties.append("gives check")
                    if chess_move.promotion:
                        move_properties.append(
                            f"promotes to {chess.piece_name(chess_move.promotion)}"
                        )
                    if test_board.is_checkmate():
                        move_properties.append("CHECKMATE!")
                    elif test_board.is_stalemate():
                        move_properties.append("stalemate")

                    move_info = {
                        "move": move,
                        "quality": quality,
                        "eval_change": eval_change,
                        "result_eval": result_eval,
                        "properties": move_properties,
                        "resulting_fen": resulting_fen,
                        "engine_response": result_analysis["best_move"],
                    }
                    move_results.append(move_info)

                    # Add to response
                    props_text = (
                        f" ({', '.join(move_properties)})" if move_properties else ""
                    )
                    response += f"\n\n**{i}. {move}** {quality}{props_text}"
                    response += f"\n• Evaluation: {start_eval/100:+.1f} → {result_eval/100:+.1f} (change: {eval_change/100:+.1f})"
                    response += f"\n• After this move, engine suggests: **{result_analysis['best_move']}**"
                    response += f"\n• Resulting FEN: `{resulting_fen}`"

                except ValueError as ve:
                    response += f"\n\n**{i}. {move}** ❌ INVALID MOVE - {str(ve)}"
                except Exception as me:
                    response += f"\n\n**{i}. {move}** ❌ ERROR - {str(me)}"

            except Exception as e:
                response += f"\n\n**{i}. {move}** ❌ ANALYSIS ERROR - {str(e)}"

        # Add summary and recommendations
        if move_results:
            # Sort moves by evaluation
            move_results.sort(
                key=lambda x: -x["eval_change"] if board.turn else x["eval_change"]
            )

            response += """

**📊 Summary & Recommendations:**

**Best Moves (by engine evaluation):**"""

            for i, move_info in enumerate(move_results[:3], 1):
                response += f"\n{i}. **{move_info['move']}** ({move_info['eval_change']/100:+.1f})"

            # Compare with engine's original suggestion
            engine_choice = start_analysis["best_move"]
            user_tested_engine_choice = any(
                move_info["move"] == engine_choice for move_info in move_results
            )

            if not user_tested_engine_choice and engine_choice:
                response += f"""

**💡 Engine's Top Choice:** {engine_choice} (not tested in your candidates)
Consider exploring the engine's suggestion to see why it's preferred."""

            # Add learning insights
            response += """

**🧠 Chess Learning Insights:**
• Compare evaluations to understand which moves improve your position
• Look for moves that create immediate threats or solve problems
• Notice patterns: captures, checks, and development often score well
• Use resulting FENs to analyze deeper if needed"""

        response += (
            f"\n\n*Analysis depth: {depth} • {len(candidate_moves)} moves explored*"
        )

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Move exploration error: {str(e)}")]


async def list_legal_moves(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """List all legal moves in a chess position."""
    fen = arguments.get("fen")
    categorize = arguments.get("categorize", True)

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    try:
        board = chess.Board(fen)
        to_move = "White" if board.turn else "Black"

        # Get all legal moves
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            return [
                TextContent(
                    type="text",
                    text=f"🚫 **No Legal Moves Available**\n\nPosition: {fen}\nResult: {'Checkmate' if board.is_checkmate() else 'Stalemate'}",
                )
            ]

        # Convert UCI moves to SAN
        san_moves = [board.san(move) for move in legal_moves]

        if not categorize:
            # Simple list format
            response = f"""📋 **Legal Moves ({to_move} to move)**

**Position:** {fen}

**All Legal Moves ({len(san_moves)} total):**
{', '.join(sorted(san_moves))}"""

        else:
            # Categorized format
            categories = {
                "captures": [],
                "checks": [],
                "castling": [],
                "en_passant": [],
                "promotions": [],
                "quiet_moves": [],
            }

            for move in legal_moves:
                san_move = board.san(move)

                # Categorize the move
                if board.is_capture(move):
                    categories["captures"].append(san_move)
                elif board.gives_check(move):
                    categories["checks"].append(san_move)
                elif (
                    move.from_square == chess.E1
                    and move.to_square in [chess.G1, chess.C1]
                    and board.piece_at(chess.E1)
                    and board.piece_at(chess.E1).piece_type == chess.KING
                ):
                    categories["castling"].append(san_move)
                elif (
                    move.from_square == chess.E8
                    and move.to_square in [chess.G8, chess.C8]
                    and board.piece_at(chess.E8)
                    and board.piece_at(chess.E8).piece_type == chess.KING
                ):
                    categories["castling"].append(san_move)
                elif board.is_en_passant(move):
                    categories["en_passant"].append(san_move)
                elif move.promotion:
                    categories["promotions"].append(san_move)
                else:
                    categories["quiet_moves"].append(san_move)

            response = f"""📋 **Legal Moves Analysis ({to_move} to move)**

**Position:** {fen}
**Total Legal Moves:** {len(san_moves)}

**📊 Moves by Category:**"""

            # Add each category if it has moves
            if categories["captures"]:
                response += f"\n\n**⚔️ Captures ({len(categories['captures'])}):**\n{', '.join(sorted(categories['captures']))}"

            if categories["checks"]:
                response += f"\n\n**👑 Checks ({len(categories['checks'])}):**\n{', '.join(sorted(categories['checks']))}"

            if categories["castling"]:
                response += f"\n\n**🏰 Castling ({len(categories['castling'])}):**\n{', '.join(sorted(categories['castling']))}"

            if categories["en_passant"]:
                response += f"\n\n**🎯 En Passant ({len(categories['en_passant'])}):**\n{', '.join(sorted(categories['en_passant']))}"

            if categories["promotions"]:
                response += f"\n\n**👑 Promotions ({len(categories['promotions'])}):**\n{', '.join(sorted(categories['promotions']))}"

            if categories["quiet_moves"]:
                response += f"\n\n**🚶 Quiet Moves ({len(categories['quiet_moves'])}):**\n{', '.join(sorted(categories['quiet_moves']))}"

            # Add summary statistics
            response += f"""

**📈 Move Statistics:**
• Forcing moves (captures + checks): {len(categories['captures']) + len(categories['checks'])}
• Positional moves (quiet + castling): {len(categories['quiet_moves']) + len(categories['castling'])}
• Special moves (en passant + promotions): {len(categories['en_passant']) + len(categories['promotions'])}"""

            # Add tactical insights if applicable
            if len(categories["captures"]) > 5:
                response += "\n• ⚡ Many capture options available - tactical position"
            elif len(categories["checks"]) > 2:
                response += "\n• 👑 Multiple check options - aggressive possibilities"
            elif len(categories["quiet_moves"]) > 20:
                response += "\n• 🌊 Many quiet moves - open, flexible position"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Legal moves error: {str(e)}")]


async def apply_moves_to_fen(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Apply a sequence of moves to a FEN position to get the correct resulting FEN."""
    starting_fen = arguments.get("starting_fen")
    moves = arguments.get("moves", [])
    show_progression = arguments.get("show_progression", False)

    if not starting_fen:
        return [
            TextContent(type="text", text="❌ Please provide a starting FEN position")
        ]

    if not moves:
        return [TextContent(type="text", text="❌ Please provide moves to apply")]

    try:
        # Validate starting FEN
        try:
            board = chess.Board(starting_fen)
        except Exception as fen_error:
            return [
                TextContent(
                    type="text", text=f"❌ Invalid starting FEN: {str(fen_error)}"
                )
            ]

        response = f"""⚙️ **Move Application Results**

**Starting Position:**
• FEN: `{starting_fen}`
• To Move: {"White" if board.turn else "Black"}"""

        if show_progression:
            response += "\n\n**📍 Move-by-Move Progression:**"

        position_history = [starting_fen]
        current_board = board.copy()

        for i, move in enumerate(moves, 1):
            try:
                # Parse and validate the move
                try:
                    chess_move = current_board.parse_san(move)
                except Exception as parse_error:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Invalid move notation '{move}' at position {i}: {str(parse_error)}\n\n**Valid moves in this position:** {', '.join([current_board.san(legal_move) for legal_move in list(current_board.legal_moves)[:10]])}{'...' if len(list(current_board.legal_moves)) > 10 else ''}",
                        )
                    ]

                # Check if move is legal
                if chess_move not in current_board.legal_moves:
                    legal_moves_list = [
                        current_board.san(legal_move)
                        for legal_move in list(current_board.legal_moves)
                    ]
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Illegal move '{move}' at position {i}\n\n**Legal moves available:** {', '.join(legal_moves_list[:15])}{'...' if len(legal_moves_list) > 15 else ''}",
                        )
                    ]

                # Make the move
                current_board.push(chess_move)
                new_fen = current_board.fen()
                position_history.append(new_fen)

                # Show progression if requested
                if show_progression:
                    to_move_after = "White" if current_board.turn else "Black"
                    move_info = ""

                    # Add move details
                    if current_board.is_check():
                        move_info += " (Check)"
                    if current_board.is_checkmate():
                        move_info += " (CHECKMATE)"
                    elif current_board.is_stalemate():
                        move_info += " (Stalemate)"

                    response += f"\n\n**{i}. {move}**{move_info}"
                    response += f"\n• FEN: `{new_fen}`"
                    response += f"\n• To Move: {to_move_after}"

            except Exception as move_error:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ Error applying move '{move}' at position {i}: {str(move_error)}",
                    )
                ]

        # Final position summary
        final_fen = position_history[-1]
        final_to_move = "White" if current_board.turn else "Black"

        # Check for game ending conditions
        game_status = ""
        if current_board.is_checkmate():
            winner = (
                "Black" if current_board.turn else "White"
            )  # Opposite of current turn
            game_status = f"\n• **Game Status:** CHECKMATE - {winner} wins!"
        elif current_board.is_stalemate():
            game_status = "\n• **Game Status:** STALEMATE - Draw"
        elif current_board.is_check():
            game_status = f"\n• **Game Status:** {final_to_move} is in CHECK"
        elif current_board.is_insufficient_material():
            game_status = "\n• **Game Status:** Insufficient material - Draw"
        elif current_board.is_seventyfive_moves():
            game_status = "\n• **Game Status:** 75-move rule - Draw"
        elif current_board.is_fivefold_repetition():
            game_status = "\n• **Game Status:** 5-fold repetition - Draw"

        response += f"""

**✅ FINAL POSITION:**
• **Moves Applied:** {' '.join(moves)}
• **Final FEN:** `{final_fen}`
• **To Move:** {final_to_move}
• **Move Count:** {current_board.fullmove_number}{game_status}"""

        # Add some quick analysis of the final position
        try:
            quick_analysis = analyzer.analyze_position(final_fen, depth=10)
            eval_info = quick_analysis["evaluation"]

            if eval_info["type"] == "cp":
                eval_text = f"{eval_info['value']/100:+.1f} pawns"
            else:
                moves_to_mate = eval_info["value"]
                side = "White" if moves_to_mate > 0 else "Black"
                eval_text = f"Mate in {abs(moves_to_mate)} for {side}"

            response += f"""
• **Evaluation:** {eval_text}
• **Best Move:** {quick_analysis['best_move'] or 'None (game over)'}"""

        except Exception:
            # Don't fail the whole tool if quick analysis fails
            pass

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Move application error: {str(e)}")]


async def analyze_variations(
    arguments: dict, analyzer: ChessAnalyzer
) -> list[TextContent]:
    """Analyze multiple-move sequences (variations) from a position."""
    fen = arguments.get("fen")
    variations = arguments.get("variations", [])
    depth = arguments.get("depth", 15)

    if not fen:
        return [TextContent(type="text", text="❌ Please provide a FEN position")]

    if not variations:
        return [
            TextContent(type="text", text="❌ Please provide variations to analyze")
        ]

    try:
        board = chess.Board(fen)
        to_move = "White" if board.turn else "Black"

        # Analyze the starting position
        start_analysis = analyzer.analyze_position(fen, depth)
        start_eval = (
            start_analysis["evaluation"]["value"]
            if start_analysis["evaluation"]["type"] == "cp"
            else 0
        )

        response = f"""🌟 **Variation Analysis**

**Starting Position ({to_move} to move):**
• Evaluation: {start_eval/100:+.1f} pawns
• Best single move: **{start_analysis['best_move']}**

**🎯 Multi-Move Sequence Analysis:**"""

        variation_results = []

        for var_idx, variation in enumerate(variations, 1):
            if not variation or len(variation) < 2:
                response += f"\n\n**Variation {var_idx}: {' '.join(variation) if variation else 'Empty'}**\n❌ Each variation must have at least 2 moves"
                continue

            if len(variation) > 4:
                response += f"\n\n**Variation {var_idx}: {' '.join(variation[:4])}...** \n⚠️ Only analyzing first 4 moves"
                variation = variation[:4]

            try:
                # Play out the variation move by move
                test_board = board.copy()
                move_evaluations = []
                move_fens = []
                valid = True

                current_eval = start_eval
                move_fens.append(fen)

                for move_num, move in enumerate(variation):
                    try:
                        chess_move = test_board.parse_san(move)

                        if chess_move not in test_board.legal_moves:
                            response += f"\n\n**Variation {var_idx}: {' '.join(variation)}**\n❌ Illegal move: {move} (move {move_num + 1})"
                            valid = False
                            break

                        # Make the move
                        test_board.push(chess_move)
                        resulting_fen = test_board.fen()
                        move_fens.append(resulting_fen)

                        # Analyze the resulting position
                        pos_analysis = analyzer.analyze_position(resulting_fen, depth)
                        pos_eval = (
                            pos_analysis["evaluation"]["value"]
                            if pos_analysis["evaluation"]["type"] == "cp"
                            else 0
                        )

                        # Calculate evaluation change
                        eval_change = pos_eval - current_eval
                        current_eval = pos_eval

                        move_evaluations.append(
                            {
                                "move": move,
                                "move_number": move_num + 1,
                                "evaluation": pos_eval,
                                "eval_change": eval_change,
                                "fen": resulting_fen,
                                "analysis": pos_analysis,
                            }
                        )

                    except Exception as move_error:
                        response += f"\n\n**Variation {var_idx}: {' '.join(variation)}**\n❌ Error on move {move}: {str(move_error)}"
                        valid = False
                        break

                if not valid:
                    continue

                # Calculate overall variation assessment
                final_eval = move_evaluations[-1]["evaluation"]
                total_change = final_eval - start_eval

                # Determine variation quality
                if abs(total_change) < 30:
                    var_quality = "🟢 Balanced"
                elif total_change > 100:
                    var_quality = (
                        "🔵 Good for White"
                        if board.turn
                        else "🔵 Good for current player"
                    )
                elif total_change < -100:
                    var_quality = (
                        "🟡 Good for Black" if board.turn else "🟡 Good for opponent"
                    )
                elif abs(total_change) < 100:
                    var_quality = "🟡 Slight advantage"
                else:
                    var_quality = "🔴 Major advantage shift"

                variation_results.append(
                    {
                        "variation": variation,
                        "final_eval": final_eval,
                        "total_change": total_change,
                        "quality": var_quality,
                        "move_evaluations": move_evaluations,
                    }
                )

                # Format the variation analysis
                response += (
                    f"\n\n**Variation {var_idx}: {' '.join(variation)}** {var_quality}"
                )
                response += f"\n• Final evaluation: {start_eval/100:+.1f} → {final_eval/100:+.1f} (net: {total_change/100:+.1f})"

                # Show move-by-move progression
                response += "\n• **Move progression:**"
                current_display_eval = start_eval

                for i, move_eval in enumerate(move_evaluations):
                    move_change = move_eval["eval_change"]

                    # Adjust evaluation display based on whose turn it was
                    if (i % 2) == 0:  # Move made by starting player
                        display_eval = move_eval["evaluation"]
                    else:  # Move made by opponent
                        display_eval = move_eval["evaluation"]

                    response += f"\n  {i+1}. {move_eval['move']}: {current_display_eval/100:+.1f} → {display_eval/100:+.1f} ({move_change/100:+.1f})"
                    current_display_eval = display_eval

                # Show the final position's top moves
                final_analysis = move_evaluations[-1]["analysis"]
                response += f"\n• **After variation, best continuation:** {final_analysis['best_move']}"

                # Show final position FEN for further analysis
                final_fen = move_evaluations[-1]["fen"]
                response += f"\n• **Final FEN:** `{final_fen}`"

            except Exception as var_error:
                response += f"\n\n**Variation {var_idx}: {' '.join(variation)}**\n❌ Analysis error: {str(var_error)}"

        # Add summary and comparison
        if variation_results:
            response += "\n\n**📊 Variation Comparison:**"

            # Sort by final evaluation (from current player's perspective)
            if board.turn:  # White to move - higher is better
                sorted_variations = sorted(
                    variation_results, key=lambda x: x["final_eval"], reverse=True
                )
            else:  # Black to move - lower is better
                sorted_variations = sorted(
                    variation_results, key=lambda x: x["final_eval"]
                )

            response += f"\n\n**Best to Worst (for {to_move}):**"
            for i, var_result in enumerate(sorted_variations, 1):
                var_moves = " ".join(var_result["variation"])
                response += f"\n{i}. **{var_moves}** ({var_result['final_eval']/100:+.1f}, {var_result['total_change']/100:+.1f})"

            # Strategic insights
            response += "\n\n**🧠 Strategic Insights:**"

            best_var = sorted_variations[0]
            worst_var = sorted_variations[-1] if len(sorted_variations) > 1 else None

            eval_diff = abs(
                best_var["final_eval"]
                - (worst_var["final_eval"] if worst_var else start_eval)
            )

            if eval_diff > 200:
                response += f"\n• **Major difference** between variations ({eval_diff/100:.1f} pawns) - choice is critical"
            elif eval_diff > 100:
                response += "\n• **Significant difference** between variations - careful evaluation needed"
            else:
                response += (
                    "\n• **Similar outcomes** - multiple good options available"
                )

            # Identify patterns
            forcing_variations = sum(
                1
                for var in variation_results
                if any("x" in move or "+" in move for move in var["variation"])
            )
            if forcing_variations > 0:
                response += f"\n• **{forcing_variations} variation(s)** contain forcing moves (captures/checks)"

            # Opening vs tactical nature
            if len(variation_results[0]["variation"]) <= 3 and all(
                abs(var["total_change"]) < 150 for var in variation_results
            ):
                response += "\n• **Positional variations** - focus on development and structure"
            elif any(abs(var["total_change"]) > 200 for var in variation_results):
                response += (
                    "\n• **Tactical variations** - concrete calculation is essential"
                )

        response += "\n\n**💡 Multi-Move Analysis Benefits:**"
        response += "\n• See how plans develop over multiple moves"
        response += "\n• Compare strategic vs tactical approaches"
        response += "\n• Understand position transformation patterns"
        response += "\n• Use final FENs for deeper analysis if needed"

        response += f"\n\n*Analyzed {len(variations)} variation(s) at depth {depth}*"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Variation analysis error: {str(e)}")]


if __name__ == "__main__":
    asyncio.run(main())
