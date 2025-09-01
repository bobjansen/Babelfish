from mcp.types import TextContent, Tool
MCP_TOOLS = [Tool(
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
                            "description": "Analysis depth (default: 15, higher is more accurate but slower)",
                            "default": 15,
                            "minimum": 1,
                            "maximum": 30,
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
                            "description": "Analysis depth for each position (default: 12)",
                            "default": 12,
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
                            "description": "Analysis depth for each position (default: 20)",
                            "default": 20,
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
                            "description": "Analysis depth (default: 18, higher gives better suggestions)",
                            "default": 18,
                            "minimum": 5,
                            "maximum": 25,
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
                            "description": "Analysis depth to search for tactics (default: 15)",
                            "default": 15,
                            "minimum": 8,
                            "maximum": 20,
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
                            "description": "Analysis depth (default: 16)",
                            "default": 16,
                            "minimum": 8,
                            "maximum": 22,
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
                            "description": "Analysis depth (default: 25, endgames benefit from deeper analysis)",
                            "default": 25,
                            "minimum": 15,
                            "maximum": 30,
                        },
                    },
                    "required": ["fen"],
                },
            ),
        ]
