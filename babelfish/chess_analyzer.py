"""Chess analysis module using Stockfish via MCP."""

from stockfish import Stockfish
from typing import Dict, List, Optional
import chess
import chess.pgn
import os
import math


class ChessAnalyzer:
    """Chess analyzer that provides context-rich analysis using Stockfish."""

    def __init__(self, stockfish_path: Optional[str] = None, verbose: bool = False):
        """Initialize the chess analyzer.

        Args:
            stockfish_path: Path to stockfish binary. If None, uses system stockfish.
            verbose: Whether to print configuration details.
        """
        # Calculate optimal thread count: floor(2/3 * num_cores)
        num_cores = os.cpu_count() or 1
        optimal_threads = max(1, math.floor((2 / 3) * num_cores))

        # Configure Stockfish with optimal settings for performance
        stockfish_params = {
            "Threads": optimal_threads,
            "Hash": min(1024, 64 * optimal_threads),  # 64MB per thread, max 1GB
            "Move Overhead": 10,  # Reduce time overhead for faster analysis
            "Minimum Thinking Time": 10,  # Minimum time per move in ms
        }

        if stockfish_path:
            self.stockfish = Stockfish(path=stockfish_path, parameters=stockfish_params)
        else:
            self.stockfish = Stockfish(parameters=stockfish_params)

        if verbose:
            hash_mb = stockfish_params["Hash"]
            print(
                f"🐟 Stockfish configured: {optimal_threads} threads, {hash_mb}MB hash (system: {num_cores} cores)"
            )

        # Store configuration for reference
        self.config = {
            "threads": optimal_threads,
            "hash_mb": stockfish_params["Hash"],
            "total_cores": num_cores,
        }

    def uci_to_san(self, fen: str, uci_move: str) -> str:
        """Convert UCI move to Standard Algebraic Notation.

        Args:
            fen: The position in FEN notation
            uci_move: Move in UCI format (e.g., "b4d2")

        Returns:
            Move in Standard Algebraic Notation (e.g., "Bd2")
        """
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(uci_move)
            if move in board.legal_moves:
                return board.san(move)
            else:
                return uci_move  # Return UCI if conversion fails
        except:
            return uci_move  # Return UCI if conversion fails

    def san_to_uci(self, fen: str, san_move: str) -> str:
        """Convert Standard Algebraic Notation to UCI move format.

        Args:
            fen: The position in FEN notation
            san_move: Move in SAN format (e.g., "Nf3")

        Returns:
            Move in UCI format (e.g., "g1f3")
        """
        try:
            board = chess.Board(fen)
            move = board.parse_san(san_move)
            return move.uci()
        except:
            return san_move  # Return original if conversion fails

    def convert_san_moves_to_uci(self, moves: List[str]) -> List[str]:
        """Convert a list of SAN moves to UCI format.

        Args:
            moves: List of moves in Standard Algebraic Notation

        Returns:
            List of moves in UCI format
        """
        uci_moves = []
        board = chess.Board()

        for san_move in moves:
            try:
                move = board.parse_san(san_move)
                uci_moves.append(move.uci())
                board.push(move)
            except:
                # If conversion fails, try to use the move as-is
                uci_moves.append(san_move)
                break

        return uci_moves

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
        best_move_uci = self.stockfish.get_best_move()
        top_moves = self.stockfish.get_top_moves(3)

        # Convert UCI moves to Standard Algebraic Notation
        best_move = self.uci_to_san(fen, best_move_uci) if best_move_uci else None

        # Convert top moves to SAN
        top_moves_san = []
        for move_info in top_moves:
            uci_move = move_info.get("Move")
            if uci_move:
                san_move = self.uci_to_san(fen, uci_move)
                move_info_san = move_info.copy()
                move_info_san["Move"] = san_move
                move_info_san["UCI"] = uci_move  # Keep UCI for reference
                top_moves_san.append(move_info_san)
            else:
                top_moves_san.append(move_info)

        return {
            "fen": fen,
            "evaluation": evaluation,
            "best_move": best_move,
            "best_move_uci": best_move_uci,
            "top_moves": top_moves_san,
            "is_check": (
                self.stockfish.will_move_be_a_capture(best_move_uci)
                if best_move_uci
                else False
            ),
        }

    def analyze_game(self, moves: List[str]) -> List[Dict]:
        """Analyze a complete game given as a list of moves.

        Args:
            moves: List of moves in standard algebraic notation

        Returns:
            List of analysis for each position
        """
        analyses = []

        # Convert SAN moves to UCI format for Stockfish
        uci_moves = self.convert_san_moves_to_uci(moves)

        # Analyze each position in the game
        for i in range(len(moves)):
            try:
                # Set position up to move i
                self.stockfish = Stockfish()  # Reset to starting position
                if i > 0:
                    self.stockfish.set_position(uci_moves[:i])

                # Make the current move
                if i < len(uci_moves):
                    self.stockfish.make_moves_from_current_position([uci_moves[i]])

                fen = self.stockfish.get_fen_position()
                analysis = self.analyze_position(fen)
                analysis["move_number"] = i + 1
                analysis["move"] = moves[i]  # Keep original SAN move
                analyses.append(analysis)

            except Exception as e:
                print(f"Error analyzing position after move {i+1}: {e}")
                # Continue with partial results
                break

        return analyses

    def get_position_explanation(
        self, fen: str, analysis: Dict = None, depth: int = 15
    ) -> str:
        """Get a human-readable explanation of the position.

        Args:
            fen: The position in FEN notation
            analysis: Pre-computed analysis to use (optional)
            depth: Analysis depth if analysis is not provided

        Returns:
            Human-readable position description
        """
        if analysis is None:
            analysis = self.analyze_position(fen, depth)

        explanation_parts = []

        # Evaluation explanation
        eval_info = analysis["evaluation"]
        if eval_info["type"] == "cp":
            centipawns = eval_info["value"]
            if abs(centipawns) < 50:
                explanation_parts.append("The position is roughly equal.")
            elif centipawns > 0:
                advantage = (
                    "slight"
                    if centipawns < 100
                    else "significant" if centipawns < 300 else "decisive"
                )
                explanation_parts.append(
                    f"White has a {advantage} advantage ({centipawns/100:.1f} pawns)."
                )
            else:
                advantage = (
                    "slight"
                    if centipawns > -100
                    else "significant" if centipawns > -300 else "decisive"
                )
                explanation_parts.append(
                    f"Black has a {advantage} advantage ({abs(centipawns)/100:.1f} pawns)."
                )
        elif eval_info["type"] == "mate":
            moves_to_mate = eval_info["value"]
            side = "White" if moves_to_mate > 0 else "Black"
            explanation_parts.append(f"{side} has mate in {abs(moves_to_mate)} moves.")

        # Best move suggestion
        if analysis["best_move"]:
            explanation_parts.append(f"The best move is {analysis['best_move']}.")

        return " ".join(explanation_parts)

    def get_principal_variation(
        self, fen: str, depth: int = 20, max_moves: int = 20
    ) -> Dict:
        """Get the engine's principal variation (main line) from a position.

        Args:
            fen: The starting position in FEN notation
            depth: Analysis depth for each position
            max_moves: Maximum number of moves to analyze in the line

        Returns:
            Dictionary containing the principal variation analysis
        """
        if not self.stockfish.is_fen_valid(fen):
            raise ValueError(f"Invalid FEN: {fen}")

        pv_moves = []
        pv_analysis = []
        current_fen = fen

        try:
            board = chess.Board(fen)

            for move_num in range(max_moves):
                # Analyze current position
                self.stockfish.set_fen_position(current_fen)
                self.stockfish.set_depth(depth)

                evaluation = self.stockfish.get_evaluation()
                best_move_uci = self.stockfish.get_best_move()

                if not best_move_uci:
                    # No more moves (checkmate, stalemate, or error)
                    break

                # Convert UCI to SAN
                best_move_san = self.uci_to_san(current_fen, best_move_uci)

                # Make the move on our board
                try:
                    chess_move = board.parse_san(best_move_san)
                    board.push(chess_move)
                    new_fen = board.fen()
                except:
                    # Move parsing failed
                    break

                # Store this move in the variation
                move_info = {
                    "move_number": move_num + 1,
                    "move_san": best_move_san,
                    "move_uci": best_move_uci,
                    "fen_before": current_fen,
                    "fen_after": new_fen,
                    "evaluation": evaluation,
                    "to_move": "White" if chess.Board(current_fen).turn else "Black",
                }

                pv_moves.append(best_move_san)
                pv_analysis.append(move_info)

                # Check for game ending conditions
                if board.is_checkmate():
                    move_info["result"] = "checkmate"
                    break
                elif board.is_stalemate():
                    move_info["result"] = "stalemate"
                    break
                elif board.is_insufficient_material():
                    move_info["result"] = "insufficient_material"
                    break

                # Move to next position
                current_fen = new_fen

                # Stop if evaluation becomes too extreme (likely found a winning/losing line)
                if evaluation["type"] == "mate":
                    break
                elif evaluation["type"] == "cp" and abs(evaluation["value"]) > 2000:
                    # Very large advantage, probably found the key line
                    break

        except Exception:
            # Return partial results if something goes wrong
            pass

        return {
            "starting_fen": fen,
            "pv_moves": pv_moves,
            "pv_analysis": pv_analysis,
            "total_moves": len(pv_moves),
            "analysis_depth": depth,
        }
