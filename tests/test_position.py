#!/usr/bin/env python3
"""Test the specific position to see legal moves."""

import chess
from babelfish.chess_analyzer import ChessAnalyzer

# Test position
fen = "8/8/2pk4/3p2p1/1p1P2P1/3K4/P1P5/8 b - - 0 1"

# Create board and analyzer
board = chess.Board(fen)
analyzer = ChessAnalyzer()

print(f"Position: {fen}")
print(f"Black to move: {not board.turn}")
print(f"Black king on: {chess.square_name(board.king(chess.BLACK))}")

# Get all legal moves
legal_moves = list(board.legal_moves)
san_moves = [board.san(move) for move in legal_moves]

print(f"\nTotal legal moves: {len(san_moves)}")
print(f"Legal moves: {', '.join(sorted(san_moves))}")

# Check specifically for king moves
king_moves = []
for move in legal_moves:
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.KING and piece.color == chess.BLACK:
        king_moves.append(board.san(move))

print(f"\nBlack king legal moves: {', '.join(king_moves)}")

# Check if Kb6 is legal
print(f"\nIs Kb6 legal? {any('Kb6' == san for san in san_moves)}")
print(f"Is Kc7 legal? {any('Kc7' == san for san in san_moves)}")

# Show analysis of Kc7
try:
    analysis = analyzer.analyze_position(fen, depth=20)
    print(f"\nPosition evaluation: {analysis['evaluation']}")
    print(f"Best move: {analysis['best_move']}")
    
    # Check if Kc7 is in top moves
    for i, move_info in enumerate(analysis['top_moves'][:5], 1):
        move = move_info['Move']
        cp = move_info.get('Centipawn', 0)
        print(f"{i}. {move} ({cp/100:+.1f})")
        if move == 'Kc7':
            print(f"   ^^ Kc7 is ranked #{i} by engine")
    
except Exception as e:
    print(f"Analysis error: {e}")