"""Chess analysis module using Stockfish via MCP."""

from stockfish import Stockfish
from typing import Dict, List, Optional
import json


class ChessAnalyzer:
    """Chess analyzer that provides context-rich analysis using Stockfish."""
    
    def __init__(self, stockfish_path: Optional[str] = None):
        """Initialize the chess analyzer.
        
        Args:
            stockfish_path: Path to stockfish binary. If None, uses system stockfish.
        """
        self.stockfish = Stockfish(path=stockfish_path) if stockfish_path else Stockfish()
        
    def analyze_position(self, fen: str, depth: int = 15) -> Dict:
        """Analyze a chess position given in FEN notation.
        
        Args:
            fen: The position in FEN notation
            depth: Analysis depth (default 15)
            
        Returns:
            Dictionary containing position analysis
        """
        if not self.stockfish.is_fen_valid(fen):
            raise ValueError(f"Invalid FEN: {fen}")
            
        self.stockfish.set_fen_position(fen)
        self.stockfish.set_depth(depth)
        
        evaluation = self.stockfish.get_evaluation()
        best_move = self.stockfish.get_best_move()
        top_moves = self.stockfish.get_top_moves(3)
        
        return {
            "fen": fen,
            "evaluation": evaluation,
            "best_move": best_move,
            "top_moves": top_moves,
            "is_check": self.stockfish.will_move_be_a_capture(best_move) if best_move else False
        }
        
    def analyze_game(self, moves: List[str]) -> List[Dict]:
        """Analyze a complete game given as a list of moves.
        
        Args:
            moves: List of moves in standard algebraic notation
            
        Returns:
            List of analysis for each position
        """
        analyses = []
        self.stockfish.set_position(moves)
        
        # Analyze each position in the game
        for i in range(len(moves)):
            self.stockfish.set_position(moves[:i+1])
            fen = self.stockfish.get_fen_position()
            
            try:
                analysis = self.analyze_position(fen)
                analysis["move_number"] = i + 1
                analysis["move"] = moves[i]
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing position after move {i+1}: {e}")
                
        return analyses
        
    def get_position_explanation(self, fen: str) -> str:
        """Get a human-readable explanation of the position.
        
        Args:
            fen: The position in FEN notation
            
        Returns:
            Human-readable position description
        """
        analysis = self.analyze_position(fen)
        
        explanation_parts = []
        
        # Evaluation explanation
        eval_info = analysis["evaluation"]
        if eval_info["type"] == "cp":
            centipawns = eval_info["value"]
            if abs(centipawns) < 50:
                explanation_parts.append("The position is roughly equal.")
            elif centipawns > 0:
                advantage = "slight" if centipawns < 100 else "significant" if centipawns < 300 else "decisive"
                explanation_parts.append(f"White has a {advantage} advantage ({centipawns/100:.1f} pawns).")
            else:
                advantage = "slight" if centipawns > -100 else "significant" if centipawns > -300 else "decisive"
                explanation_parts.append(f"Black has a {advantage} advantage ({abs(centipawns)/100:.1f} pawns).")
        elif eval_info["type"] == "mate":
            moves_to_mate = eval_info["value"]
            side = "White" if moves_to_mate > 0 else "Black"
            explanation_parts.append(f"{side} has mate in {abs(moves_to_mate)} moves.")
        
        # Best move suggestion
        if analysis["best_move"]:
            explanation_parts.append(f"The best move is {analysis['best_move']}.")
            
        return " ".join(explanation_parts)