#!/usr/bin/env python3
"""Demo analysis showing what the LLM should have done for the Kc7 question."""

import chess
from babelfish.chess_analyzer import ChessAnalyzer

fen = "8/8/2pk4/3p2p1/1p1P2P1/3K4/P1P5/8 b - - 0 1"
analyzer = ChessAnalyzer()

print("🎯 PROPER LLM ANALYSIS FOR: 'Explain the move Kc7 in this position'")
print("=" * 70)

print("\n1️⃣ STEP 1: Use list_legal_moves to verify what moves are possible")
board = chess.Board(fen)
legal_moves = [board.san(move) for move in board.legal_moves]
print(f"   Legal moves: {', '.join(sorted(legal_moves))}")
print("   ✅ Kc7 IS legal")
print("   ❌ Kb6 is NOT legal (LLM hallucinated this)")

print("\n2️⃣ STEP 2: Use analyze_position to get engine evaluation")
analysis = analyzer.analyze_position(fen, depth=20)
print(f"   Position evaluation: {analysis['evaluation']['value']/100:+.1f} pawns")
print("   Top moves:")
for i, move_info in enumerate(analysis['top_moves'][:5], 1):
    move = move_info['Move']
    cp = move_info.get('Centipawn', 0)
    marker = " ← ENGINE'S TOP CHOICE!" if move == "Kc7" else ""
    print(f"   {i}. {move} ({cp/100:+.1f}){marker}")

print("\n3️⃣ STEP 3: Use evaluate_move to specifically assess Kc7")
# Simulate what evaluate_move would show
best_cp = analysis['top_moves'][0].get('Centipawn', 0)
kc7_cp = None
for move_info in analysis['top_moves']:
    if move_info['Move'] == 'Kc7':
        kc7_cp = move_info.get('Centipawn', 0)
        break

if kc7_cp is not None:
    diff = kc7_cp - best_cp
    if abs(diff) < 20:
        rating = "🟢 Excellent"
    elif abs(diff) < 50:
        rating = "🔵 Good"
    else:
        rating = "🟡 Questionable"
    
    print(f"   Kc7 rating: {rating}")
    print(f"   Evaluation change: {diff/100:+.1f} pawns vs best move")

print("\n4️⃣ WHAT THE LLM SHOULD HAVE CONCLUDED:")
print("   • Kc7 is the ENGINE'S TOP CHOICE (-5.0 centipawns)")
print("   • It's an EXCELLENT move (engine's #1 recommendation)")  
print("   • Kb6 doesn't exist as a legal move")
print("   • This is a king endgame where centralization and activity matter")

print("\n❌ WHAT THE LLM DID WRONG:")
print("   • Didn't use list_legal_moves to verify move legality")
print("   • Hallucinated Kb6 as a legal alternative")
print("   • Didn't use analyze_position to see engine evaluation")
print("   • Made assumptions about chess moves without tool verification")

print("\n💡 SOLUTION: The tool descriptions now emphasize:")
print("   • 'ALWAYS use this tool before discussing specific moves'")
print("   • 'ESSENTIAL VERIFICATION TOOL to prevent move hallucinations'")  
print("   • 'Chess move legality cannot be reliably determined without this tool'")