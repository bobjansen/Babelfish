#!/usr/bin/env python3
"""Test board visualization for clear FEN understanding."""

import asyncio
from chess_coach_mcp import visualize_board_position

# The position where LLM made errors
fen = "8/4k1p1/2p5/4K3/8/3P4/6P1/8 w - - 0 1"

print("🎨 TESTING BOARD VISUALIZATION")
print("=" * 50)
print(f"FEN: {fen}")
print("This should make the position much clearer for LLM understanding")

async def test_visualization():
    arguments = {
        "fen": fen,
        "show_coordinates": True,
        "highlight_pieces": ["pawn"]  # Highlight pawns since that was the issue
    }
    
    result = await visualize_board_position(arguments, None)  # analyzer not needed for this
    print(result[0].text)

asyncio.run(test_visualization())