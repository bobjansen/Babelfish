#!/usr/bin/env python3
"""Test the passed pawn analysis on the position with NO passed pawns."""

import chess
import asyncio

# The position mentioned - should have NO passed pawns
fen = "8/4k1p1/2p5/4K3/8/3P4/6P1/8 w - - 0 1"

print("🧪 TESTING PASSED PAWN ANALYSIS")
print("=" * 50)
print(f"Position: {fen}")
print("Expected: NO passed pawns (all pawns are blocked)")

board = chess.Board(fen)

# Print the position for visualization
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

print("\nPawn analysis:")
# Check each pawn manually
for square in chess.SQUARES:
    piece = board.piece_at(square)
    if piece and piece.piece_type == chess.PAWN:
        square_name = chess.square_name(square)
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        color_name = "White" if piece.color == chess.WHITE else "Black"
        
        print(f"  {color_name} pawn on {square_name}:")
        
        # Check what's blocking it
        if piece.color == chess.WHITE:
            # Check ranks ahead for blocking pawns
            blocked_by = []
            for check_rank in range(rank + 1, 8):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        check_piece = board.piece_at(check_square)
                        if check_piece and check_piece.piece_type == chess.PAWN and check_piece.color == chess.BLACK:
                            blocked_by.append(chess.square_name(check_square))
            if blocked_by:
                print(f"    BLOCKED by black pawns: {', '.join(blocked_by)}")
            else:
                print(f"    PASSED - no blocking pawns found")
        else:  # Black pawn
            blocked_by = []
            for check_rank in range(rank - 1, -1, -1):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        check_piece = board.piece_at(check_square)
                        if check_piece and check_piece.piece_type == chess.PAWN and check_piece.color == chess.WHITE:
                            blocked_by.append(chess.square_name(check_square))
            if blocked_by:
                print(f"    BLOCKED by white pawns: {', '.join(blocked_by)}")
            else:
                print(f"    PASSED - no blocking pawns found")

# Now test our analysis function
print(f"\n🔧 Testing analyze_passed_pawns function:")

async def test_passed_pawns():
    from chess_coach_mcp import analyze_passed_pawns
    result = await analyze_passed_pawns(board)
    print(result)

asyncio.run(test_passed_pawns())