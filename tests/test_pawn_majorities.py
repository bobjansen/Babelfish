#!/usr/bin/env python3
"""Test pawn majority analysis on the position where LLM claimed 2-vs-1 kingside majority."""

import chess
import asyncio

# Position: 8/4k1p1/2p5/4K3/8/3P4/6P1/8 w - - 0 1
# LLM claimed: "White's 2-vs-1 pawn majority on the kingside"
fen = "8/4k1p1/2p5/4K3/8/3P4/6P1/8 w - - 0 1"

print("🔍 TESTING PAWN MAJORITY ANALYSIS")
print("=" * 50)
print(f"Position: {fen}")
print("LLM claimed: 'White's 2-vs-1 pawn majority on the kingside'")
print("Expected: NO majorities - equal pawns on both sides")

board = chess.Board(fen)

print("\nBoard visualization:")
print("  a b c d e f g h")
for rank in range(7, -1, -1):
    row = f"{rank+1} "
    for file in range(8):
        square = chess.square(file, rank)
        piece = board.piece_at(square)
        if piece:
            row += piece.symbol() + " "
        else:
            row += ". "
    print(row)

# Manual count
print("\nManual pawn counting:")
queenside_files = ['a', 'b', 'c', 'd']  # files 0,1,2,3
kingside_files = ['e', 'f', 'g', 'h']   # files 4,5,6,7

white_queenside = 0
black_queenside = 0
white_kingside = 0
black_kingside = 0

pawn_locations = []
for square in chess.SQUARES:
    piece = board.piece_at(square)
    if piece and piece.piece_type == chess.PAWN:
        square_name = chess.square_name(square)
        file_letter = square_name[0]
        color_name = "White" if piece.color == chess.WHITE else "Black"
        pawn_locations.append((color_name, square_name, file_letter))
        
        if file_letter in queenside_files:
            if piece.color == chess.WHITE:
                white_queenside += 1
            else:
                black_queenside += 1
        else:
            if piece.color == chess.WHITE:
                white_kingside += 1
            else:
                black_kingside += 1

print("Pawn locations:")
for color, square, file in pawn_locations:
    side = "Queenside" if file in queenside_files else "Kingside"
    print(f"  {color} pawn on {square} ({side})")

print(f"\nActual counts:")
print(f"  Queenside: White {white_queenside}, Black {black_queenside}")
print(f"  Kingside: White {white_kingside}, Black {black_kingside}")

print(f"\nLLM's claim vs Reality:")
print(f"  LLM said: 'White 2-vs-1 kingside majority'")
print(f"  Reality: White {white_kingside} vs Black {black_kingside} on kingside")
print(f"  Verdict: {'INCORRECT' if white_kingside != 2 or black_kingside != 1 else 'CORRECT'}")

# Test our function
print(f"\n🔧 Testing our analyze_chess_concepts function:")

async def test_concepts():
    from chess_coach_mcp import analyze_passed_pawns
    result = await analyze_passed_pawns(board)
    print(result)

asyncio.run(test_concepts())