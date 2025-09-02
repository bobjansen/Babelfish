#!/usr/bin/env python3
"""Test the principal variation for the Kc7 endgame position."""

from babelfish.chess_analyzer import ChessAnalyzer

# The position where Kc7 was questioned
fen = "8/8/2pk4/3p2p1/1p1P2P1/3K4/P1P5/8 b - - 0 1"

print("🎯 TESTING PRINCIPAL VARIATION FOR Kc7 POSITION")
print("=" * 60)

analyzer = ChessAnalyzer()

try:
    # Get the principal variation
    pv_data = analyzer.get_principal_variation(fen, depth=22, max_moves=15)
    
    print(f"Starting position: {fen}")
    print(f"Total moves found: {len(pv_data['pv_moves'])}")
    print(f"Principal variation: {' '.join(pv_data['pv_moves'])}")
    
    print("\nMove-by-move breakdown:")
    for i, move_analysis in enumerate(pv_data['pv_analysis'][:10]):  # Show first 10 moves
        move = move_analysis['move_san']
        eval_info = move_analysis['evaluation']
        to_move = move_analysis['to_move']
        
        if eval_info['type'] == 'cp':
            eval_text = f"{eval_info['value']/100:+.1f}"
        else:
            eval_text = f"Mate in {abs(eval_info['value'])}"
            
        print(f"{i+1:2d}. {move:6s} ({to_move:5s} to move) → {eval_text}")
    
    # Show the strategic pattern
    print("\nStrategic Analysis:")
    king_moves = sum(1 for move in pv_data['pv_moves'] if move.startswith('K'))
    pawn_moves = sum(1 for move in pv_data['pv_moves'] if len(move) <= 3 and not move.startswith('K'))
    
    print(f"King moves: {king_moves}/{len(pv_data['pv_moves'])} ({100*king_moves/len(pv_data['pv_moves']):.0f}%)")
    print(f"Pawn moves: {pawn_moves}/{len(pv_data['pv_moves'])} ({100*pawn_moves/len(pv_data['pv_moves']) if pv_data['pv_moves'] else 0:.0f}%)")
    
    # Check if this shows the zugzwang plan
    starting_eval = pv_data['pv_analysis'][0]['evaluation']['value']
    final_eval = pv_data['pv_analysis'][-1]['evaluation']['value'] if pv_data['pv_analysis'] else starting_eval
    improvement = final_eval - starting_eval
    
    print(f"Evaluation change: {starting_eval/100:+.1f} → {final_eval/100:+.1f} (improvement: {improvement/100:+.1f})")
    
    if king_moves >= len(pv_data['pv_moves']) * 0.4:
        print("✅ This appears to be a KING ACTIVITY plan (lots of king moves)")
        
    print(f"\nFinal position FEN: {pv_data['pv_analysis'][-1]['fen_after'] if pv_data['pv_analysis'] else 'N/A'}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()