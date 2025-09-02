#!/usr/bin/env python3
"""Test Stockfish principal variation extraction."""

from stockfish import Stockfish

# Test getting principal variation from Stockfish
stockfish = Stockfish()
fen = "8/8/2pk4/3p2p1/1p1P2P1/3K4/P1P5/8 b - - 0 1"

print("Testing Stockfish principal variation methods...")

stockfish.set_fen_position(fen)
stockfish.set_depth(20)

# Check available methods
print("\nStockfish methods:")
methods = [method for method in dir(stockfish) if not method.startswith('_')]
pv_methods = [method for method in methods if 'pv' in method.lower() or 'line' in method.lower() or 'variation' in method.lower()]
print(f"PV-related methods: {pv_methods}")

# Try different approaches
print(f"\nTesting get_best_move_time: {stockfish.get_best_move_time()}")

# Try to get more info
try:
    evaluation = stockfish.get_evaluation()
    print(f"Evaluation: {evaluation}")
except Exception as e:
    print(f"Evaluation error: {e}")

try:
    wdl = stockfish.get_wdl_stats()
    print(f"WDL stats: {wdl}")
except Exception as e:
    print(f"WDL error: {e}")

# Check if we can get UCI info
print(f"\nTesting _stockfish_major_version: {getattr(stockfish, '_stockfish_major_version', 'not found')}")

# Try to set options that might give us PV
try:
    stockfish._set_option("MultiPV", "1")
    result = stockfish._send_command("go depth 15")
    print(f"UCI go command result: {result}")
except Exception as e:
    print(f"UCI command error: {e}")

# Test what happens with multiple PVs
try:
    # Get top moves which might have more info
    top_moves = stockfish.get_top_moves(5)
    print(f"\nTop moves structure: {top_moves}")
except Exception as e:
    print(f"Top moves error: {e}")