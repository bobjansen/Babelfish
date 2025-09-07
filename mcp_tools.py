from mcp.types import Tool

MCP_TOOLS = [
    Tool(
        name="analyze_position",
        description="Analyze a chess position using Stockfish engine. Provides evaluation, best moves, and human-readable explanation.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN (Forsyth-Edwards Notation)",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth (default: 20, higher is more accurate but slower)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 30,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="analyze_game",
        description="Analyze a complete chess game move by move. Provides evaluation for each position.",
        inputSchema={
            "type": "object",
            "properties": {
                "moves": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of moves in standard algebraic notation (e.g., ['e4', 'e5', 'Nf3'])",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth for each position (default: 16)",
                    "default": 16,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["moves"],
        },
    ),
    Tool(
        name="explain_position",
        description="Get a human-readable explanation of a chess position's evaluation and key features.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                }
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="get_principal_variation",
        description="Get the engine's principal variation (main line) from a chess position. Shows the best continuation for both sides.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth for each position (default: 22)",
                    "default": 22,
                    "minimum": 1,
                    "maximum": 25,
                },
                "max_moves": {
                    "type": "integer",
                    "description": "Maximum number of moves to calculate in the line (default: 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="suggest_move",
        description="Get the best move suggestion for a position with detailed explanation of why it's the best choice.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth (default: 22, higher gives better suggestions)",
                    "default": 22,
                    "minimum": 5,
                    "maximum": 25,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="find_tactical_motifs",
        description="Analyze a position to find tactical motifs like pins, forks, skewers, and other tactical patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth to search for tactics (default: 20)",
                    "default": 20,
                    "minimum": 8,
                    "maximum": 20,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="evaluate_move_quality",
        description="Evaluate whether a specific move in a position is good, bad, or a blunder compared to the best moves.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position BEFORE the move",
                },
                "move": {
                    "type": "string",
                    "description": "The move to evaluate in standard algebraic notation (e.g., 'Nf3', 'exd5', 'O-O')",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth (default: 20)",
                    "default": 20,
                    "minimum": 8,
                    "maximum": 22,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen", "move"],
        },
    ),
    Tool(
        name="analyze_endgame",
        description="Specialized analysis for endgame positions, providing tablebase information when available and endgame principles.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The endgame position in FEN notation",
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth (default: 28, endgames benefit from deeper analysis)",
                    "default": 28,
                    "minimum": 15,
                    "maximum": 30,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="get_top_lines",
        description="Get the top principal variations (best lines of play) from a position. Shows alternative continuations and their evaluations. Use this to compare different strategic approaches.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "num_lines": {
                    "type": "integer",
                    "description": "Number of top lines to show (2-5, default: 3). Use fewer lines for simple positions, more for complex tactical positions.",
                    "default": 3,
                    "minimum": 2,
                    "maximum": 5,
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth for each line (default: 25)",
                    "default": 25,
                    "minimum": 15,
                    "maximum": 30,
                },
                "moves_per_line": {
                    "type": "integer",
                    "description": "Number of moves to show per line (default: 6)",
                    "default": 6,
                    "minimum": 3,
                    "maximum": 10,
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="visualize_board",
        description="Generate ASCII visualization of a chess board position from FEN notation. ESSENTIAL for verifying tactical claims - use this before making any statements about piece attacks, defenses, or interactions.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "flip": {
                    "type": "boolean",
                    "description": "Flip the board to show from Black's perspective (default: false)",
                    "default": False,
                },
                "highlight_pieces": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of square names to highlight (e.g., ['e4', 'e5', 'd4']) - useful for showing tactical relationships",
                    "default": [],
                },
            },
            "required": ["fen"],
        },
    ),
    Tool(
        name="validate_move_choice",
        description="CRITICAL VALIDATION: Determines if a move is among Stockfish's top recommendations. Use this to validate any move suggestions - if a move is NOT in the top recommendations, it should be considered INCORRECT.",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation",
                },
                "move": {
                    "type": "string",
                    "description": "The move to validate in standard algebraic notation",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Check if move is in top N engine recommendations (default: 3)",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                },
                "depth": {
                    "type": "integer",
                    "description": "Engine analysis depth (default: 22)",
                    "default": 22,
                    "minimum": 15,
                    "maximum": 25,
                },
                "time_limit": {
                    "type": "number",
                    "description": "Maximum time in seconds for analysis (default: auto-selected based on depth, max: 60s)",
                    "minimum": 1.0,
                    "maximum": 60.0,
                },
            },
            "required": ["fen", "move"],
        },
    ),
    Tool(
        name="apply_moves",
        description="CRITICAL TOOL: Apply moves to a FEN position to get the correct resulting FEN. Takes a starting FEN and list of moves in algebraic notation, validates each move's legality, and returns the accurate final position. ALWAYS use this tool instead of trying to calculate FEN positions manually - chess position calculation is extremely error-prone and leads to incorrect analysis. This tool is essential for accurate move sequences and position analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "starting_fen": {
                    "type": "string",
                    "description": "The starting chess position in FEN notation",
                },
                "moves": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of moves to apply in standard algebraic notation (e.g., ['e4', 'e5', 'Nf3', 'Nc6']). Each move will be validated and applied sequentially.",
                    "minItems": 1,
                    "maxItems": 30,
                },
                "show_progression": {
                    "type": "boolean",
                    "description": "Whether to show the position after each move (default: false, only shows final position)",
                    "default": False,
                },
            },
            "required": ["starting_fen", "moves"],
        },
    ),
    Tool(
        name="evaluate_candidate_moves",
        description="RAPID EVALUATION TOOL: Quickly evaluate multiple candidate moves from a chess position. Perfect for comparing move options without hesitation - use this tool frequently and liberally when analyzing positions. The persistent Stockfish instance makes this very fast. Ideal for: 1) Comparing multiple candidate moves 2) Validating move suggestions 3) Quick tactical checks 4) Exploring alternative lines. ALWAYS use this when you have multiple moves to consider - there's no performance penalty thanks to caching!",
        inputSchema={
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The chess position in FEN notation to analyze from",
                },
                "candidate_moves": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of candidate moves in standard algebraic notation (e.g., ['Nf3', 'e4', 'c4', 'd4']). Include as many candidates as you want to evaluate - the tool is very fast.",
                    "minItems": 2,
                    "maxItems": 20,
                },
                "depth": {
                    "type": "integer",
                    "description": "Analysis depth for evaluation (default: 15)",
                    "default": 15,
                    "minimum": 10,
                    "maximum": 25,
                },
            },
            "required": ["fen", "candidate_moves"],
        },
    ),
]
