#!/usr/bin/env python3
"""Shared chess utilities for board visualization and common functions."""

import chess
from typing import List, Dict, Any, Optional
from mcp.types import TextContent


def generate_ascii_board(board: chess.Board, flip: bool = False, show_coordinates: bool = True, highlight_pieces: List[str] = None) -> str:
    """Generate ASCII representation of chess board with various options.
    
    Args:
        board: Chess board object
        flip: Show from Black's perspective 
        show_coordinates: Show file/rank labels
        highlight_pieces: List of square names to highlight (e.g., ['e4', 'e5'])
        
    Returns:
        ASCII string representation of the board
    """
    if highlight_pieces is None:
        highlight_pieces = []
    
    # Define piece symbols
    piece_symbols = {
        chess.PAWN: ("♟", "♙"),
        chess.ROOK: ("♜", "♖"), 
        chess.KNIGHT: ("♞", "♘"),
        chess.BISHOP: ("♝", "♗"),
        chess.QUEEN: ("♛", "♕"),
        chess.KING: ("♚", "♔"),
    }

    # Build the board string
    board_lines = []
    
    # Add column headers if requested
    if show_coordinates:
        if flip:
            board_lines.append("    h  g  f  e  d  c  b  a")
        else:
            board_lines.append("    a  b  c  d  e  f  g  h")
            
    board_lines.append("  ┌──┬──┬──┬──┬──┬──┬──┬──┐")
    
    ranks = range(7, -1, -1) if not flip else range(8)
    
    for rank in ranks:
        rank_num = rank + 1
        line = f"{rank_num} │" if show_coordinates else "│"
        
        files = range(7, -1, -1) if flip else range(8)
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            square_name = chess.square_name(square)
            
            # Check if this square should be highlighted
            is_highlighted = square_name in highlight_pieces
            
            if piece is None:
                # Empty square
                if is_highlighted:
                    line += "██"  # Highlighted empty square
                else:
                    line += "  "  # Normal empty square
            else:
                # Piece on square
                symbol = piece_symbols[piece.piece_type][0 if piece.color else 1]
                if is_highlighted:
                    line += f"[{symbol}]"[0:2]  # Highlight piece (truncate to 2 chars)
                else:
                    line += f"{symbol} "
                    
            line += "│"
        
        if show_coordinates:
            line += f" {rank_num}"
        board_lines.append(line)
        
        # Add horizontal divider (except after last rank)
        if rank != (0 if not flip else 7):
            board_lines.append("  ├──┼──┼──┼──┼──┼──┼──┼──┤")
    
    board_lines.append("  └──┴──┴──┴──┴──┴──┴──┴──┘")
    
    # Add column headers at bottom if requested
    if show_coordinates:
        if flip:
            board_lines.append("    h  g  f  e  d  c  b  a")
        else:
            board_lines.append("    a  b  c  d  e  f  g  h")
            
    return "\n".join(board_lines)


def get_position_info(fen: str) -> Dict[str, Any]:
    """Extract detailed position information from FEN.
    
    Args:
        fen: Position in FEN notation
        
    Returns:
        Dictionary with position details
    """
    try:
        board = chess.Board(fen)
        fen_parts = fen.split()
        
        # Parse castling rights
        castling_rights = []
        if board.has_kingside_castling_rights(chess.WHITE):
            castling_rights.append("K")
        if board.has_queenside_castling_rights(chess.WHITE):
            castling_rights.append("Q")
        if board.has_kingside_castling_rights(chess.BLACK):
            castling_rights.append("k")
        if board.has_queenside_castling_rights(chess.BLACK):
            castling_rights.append("q")
        
        return {
            "board": board,
            "fen": fen,
            "turn": "White" if board.turn else "Black",
            "castling_rights": "".join(castling_rights) if castling_rights else "None",
            "en_passant": chess.square_name(board.ep_square) if board.ep_square else "None",
            "halfmove_clock": board.halfmove_clock,
            "fullmove_number": board.fullmove_number,
            "is_check": board.is_check(),
            "is_checkmate": board.is_checkmate(),
            "is_stalemate": board.is_stalemate(),
            "is_insufficient_material": board.is_insufficient_material(),
        }
    except Exception as e:
        raise ValueError(f"Invalid FEN notation: {str(e)}")


def create_board_visualization(
    fen: str,
    flip: bool = False, 
    show_coordinates: bool = True,
    highlight_pieces: List[str] = None,
    title: str = "Chess Board Visualization",
    include_position_info: bool = True
) -> str:
    """Create a complete board visualization with position information.
    
    Args:
        fen: Position in FEN notation
        flip: Show from Black's perspective
        show_coordinates: Show file/rank labels
        highlight_pieces: List of square names to highlight
        title: Title for the visualization
        include_position_info: Whether to include position details
        
    Returns:
        Formatted board visualization string
    """
    try:
        pos_info = get_position_info(fen)
        board = pos_info["board"]
        
        # Generate the ASCII board
        board_str = generate_ascii_board(
            board, flip, show_coordinates, highlight_pieces or []
        )
        
        # Build the response
        response_parts = [f"🐟 **{title}**", "", board_str]
        
        if include_position_info:
            response_parts.extend([
                "",
                "**Position Info:**",
                f"• **FEN:** {fen}",
                f"• **Turn:** {pos_info['turn']}",
                f"• **Castling Rights:** {pos_info['castling_rights']}",
                f"• **En Passant:** {pos_info['en_passant']}",
                f"• **Halfmove Clock:** {pos_info['halfmove_clock']}",
                f"• **Fullmove Number:** {pos_info['fullmove_number']}"
            ])
            
            # Add game status
            if pos_info["is_check"]:
                response_parts.append("• **Status:** Check!")
            elif pos_info["is_checkmate"]:
                response_parts.append("• **Status:** Checkmate!")
            elif pos_info["is_stalemate"]:
                response_parts.append("• **Status:** Stalemate!")
            elif pos_info["is_insufficient_material"]:
                response_parts.append("• **Status:** Insufficient material to mate")
                
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error visualizing board: {str(e)}"


def visualize_board_mcp_tool(arguments: Dict[str, Any]) -> List[TextContent]:
    """MCP tool implementation for board visualization.
    
    This is the shared implementation that both chess_coach_mcp and openrouter_cli can use.
    """
    fen = arguments.get("fen")
    flip = arguments.get("flip", False)
    show_coordinates = arguments.get("show_coordinates", True)
    highlight_pieces = arguments.get("highlight_pieces", [])
    
    if not fen:
        return [TextContent(type="text", text="❌ Error: FEN position is required")]
    
    try:
        visualization = create_board_visualization(
            fen=fen,
            flip=flip,
            show_coordinates=show_coordinates,
            highlight_pieces=highlight_pieces,
            title="Chess Board Visualization",
            include_position_info=True
        )
        return [TextContent(type="text", text=visualization)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error visualizing board: {str(e)}")]