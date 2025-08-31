#!/usr/bin/env python3
"""Babelfish Chess Coach MCP Server - Comprehensive Chess Analysis for Players."""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.types import TextContent, Tool
from babelfish.chess_analyzer import ChessAnalyzer
import chess


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
                description="🎯 Get comprehensive analysis of any chess position. Just provide a FEN and get: evaluation, best moves, tactical themes, strategic advice, and common plans. Perfect for studying positions from your games.",
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
                description="🔍 Evaluate a specific move in a position. Provide a FEN and a move to see if it's good, bad, or best. Get tactical and positional feedback, plus better alternatives if the move isn't optimal.",
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
                description="⚡ Find tactical opportunities in a position. Discovers checks, captures, threats, pins, forks, skewers, and other tactical motifs. Great for tactical training and finding winning combinations.",
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
                description="📚 Analyze opening positions and get strategic guidance. Learn opening principles, typical plans, piece development priorities, and common continuations from any opening position.",
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
                description="🏁 Get expert guidance for endgame positions. Learn winning techniques, drawing methods, key squares, pawn breakthroughs, and piece coordination in the endgame.",
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
            response += f"""

**📚 Opening Principles:**
• Develop pieces toward the center
• Control central squares (e4, e5, d4, d5)
• Castle early for king safety
• Don't move the same piece twice without reason"""

        elif phase == "Middlegame":
            response += f"""

**⚔️ Middlegame Strategy:**
• Look for tactical opportunities (pins, forks, skewers)
• Improve piece coordination and activity
• Create weaknesses in opponent's position
• Consider pawn breaks and space advantage"""

        else:  # Endgame
            response += f"""

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

        # Analyze position after move
        after_analysis = analyzer.analyze_position(after_fen, depth)

        # Compare evaluations
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

        # Flip evaluation if it was black to move
        if "b" in fen:
            after_eval = -after_eval

        eval_change = after_eval - before_eval

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
• Before: {before_eval/100:+.1f} → After: {after_eval/100:+.1f}

**Engine's Assessment:**"""

        if move == best_move:
            response += f"\n✅ This is the engine's top choice!"
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

        response += f"""

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
            response += f"""

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
                response += f"\n🎯 **Major Tactical Opportunity!**"
                response += f"\nEvaluation: {cp_value/100:+.1f} pawns"
            elif abs(cp_value) > 150:
                response += f"\n⚡ **Tactical Advantage Available**"
                response += f"\nEvaluation: {cp_value/100:+.1f} pawns"
            else:
                response += f"\n🔍 **No Major Tactics Found**"
                response += f"\nPosition is relatively balanced: {cp_value/100:+.1f}"

        response += f"""

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
        response += f"""

**🧠 Common Tactical Motifs to Look For:**
• **Pins**: Attack a piece that can't move without exposing a more valuable piece
• **Forks**: Attack two or more pieces simultaneously
• **Skewers**: Force a valuable piece to move, exposing a less valuable one
• **Discovered attacks**: Move one piece to reveal an attack from another
• **Double attacks**: Attack two targets at once
• **Deflection**: Force a defending piece away from its duty"""

        if eval_info["type"] != "mate" and abs(cp_value) < 100:
            response += f"""

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

        response = f"""📚 **Opening Analysis**

**Position Info:**
• Move {move_number}, {to_move} to move
• Evaluation: {analysis['evaluation']['value']/100:+.1f if analysis['evaluation']['type'] == 'cp' else 'Mate!'} pawns"""

        if moves_played:
            response += f"\n• Opening line: {' '.join(moves_played[:8])}{'...' if len(moves_played) > 8 else ''}"

        response += f"""

**🎯 Recommended Moves:**"""

        for i, move_info in enumerate(analysis["top_moves"][:3], 1):
            move = move_info["Move"]
            cp = move_info.get("Centipawn", 0)
            response += f"\n{i}. **{move}** ({cp/100:+.1f})"

        # Opening principles based on move number
        if move_number <= 5:
            response += f"""

**🏗️ Early Opening Principles (Moves 1-5):**
• **Development**: Bring knights and bishops into active squares
• **Center Control**: Fight for central squares (e4, e5, d4, d5)
• **King Safety**: Castle early to protect your king
• **Avoid**: Moving the same piece twice, bringing queen out too early"""

        elif move_number <= 10:
            response += f"""

**⚔️ Opening Development (Moves 6-10):**
• **Complete development**: Get all minor pieces active
• **Castle if you haven't**: King safety is priority
• **Connect rooks**: Clear the back rank
• **Central pawn breaks**: Look for d4/d5 or e4/e5 advances"""

        else:
            response += f"""

**🌟 Opening to Middlegame Transition:**
• **Piece improvement**: Optimize piece placement
• **Pawn structure**: Consider pawn breaks and weaknesses
• **Planning**: Identify strategic goals and piece coordination
• **Tactics**: Stay alert for tactical opportunities"""

        # Add piece development analysis
        piece_analysis = analyze_piece_development(board)
        response += f"""

**🎭 Piece Activity Assessment:**"""
        for color, info in piece_analysis.items():
            response += f"\n• **{color}**: {info['developed']}/8 pieces developed"
            if info["suggestions"]:
                response += f" | Next: {', '.join(info['suggestions'])}"

        response += f"""

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
            response += f"""

**♔ King and Pawn Endgame:**
• **Opposition**: Control key squares to restrict opponent's king
• **Key squares**: Calculate which squares your king must reach
• **Pawn promotion**: Support your pawn's advance to the 8th rank
• **Stalemate tricks**: Be careful not to stalemate in winning positions"""

        elif "K+Q vs K" in material_balance:
            response += f"""

**♕ Queen vs King Endgame:**
• **Centralize your king**: Bring it up to help the queen
• **Cut off escape**: Use queen to limit opponent king's mobility
• **Avoid stalemate**: Give the opponent king legal moves
• **Basic checkmate**: Learn the systematic mating technique"""

        elif "K+R vs K" in material_balance:
            response += f"""

**♖ Rook vs King Endgame:**
• **Cut off the king**: Use rook to confine opponent to edge
• **Box method**: Systematically reduce the king's space
• **Avoid stalemate**: Keep opponent's king mobile until mate
• **King activity**: Your king must participate in the mating attack"""

        else:
            response += f"""

**🎓 General Endgame Principles:**
• **King activity**: The king becomes a fighting piece
• **Passed pawns**: Create and advance them with king support
• **Piece coordination**: Work pieces together harmoniously
• **Calculate precisely**: Endgames reward accurate calculation"""

        # Add practical guidance
        response += f"""

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


if __name__ == "__main__":
    asyncio.run(main())
