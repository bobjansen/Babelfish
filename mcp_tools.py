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
        ]
