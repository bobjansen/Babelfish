"""MCP server for Babelfish chess analysis."""

import json
from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import TextContent, Tool, CallToolRequest
from .chess_analyzer import ChessAnalyzer


class BabelfishMCPServer:
    """MCP Server that exposes chess analysis tools."""
    
    def __init__(self):
        self.server = Server("babelfish")
        self.analyzer = ChessAnalyzer()
        self.setup_tools()
        
    def setup_tools(self):
        """Setup the MCP tools for chess analysis."""
        
        @self.server.call_tool()
        async def analyze_position(arguments: Dict[str, Any]) -> List[TextContent]:
            """Analyze a chess position given in FEN notation."""
            try:
                fen = arguments.get("fen")
                depth = arguments.get("depth", 15)
                
                if not fen:
                    return [TextContent(type="text", text="Error: FEN position is required")]
                    
                analysis = self.analyzer.analyze_position(fen, depth)
                explanation = self.analyzer.get_position_explanation(fen)
                
                result = {
                    "analysis": analysis,
                    "explanation": explanation
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Error analyzing position: {str(e)}")]
        
        @self.server.call_tool()
        async def analyze_game(arguments: Dict[str, Any]) -> List[TextContent]:
            """Analyze a complete chess game."""
            try:
                moves = arguments.get("moves", [])
                
                if not moves:
                    return [TextContent(type="text", text="Error: Moves list is required")]
                    
                analyses = self.analyzer.analyze_game(moves)
                
                # Create summary
                summary = {
                    "total_moves": len(moves),
                    "game_analysis": analyses
                }
                
                return [TextContent(type="text", text=json.dumps(summary, indent=2))]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Error analyzing game: {str(e)}")]
        
        @self.server.call_tool()
        async def explain_position(arguments: Dict[str, Any]) -> List[TextContent]:
            """Get a human-readable explanation of a chess position."""
            try:
                fen = arguments.get("fen")
                
                if not fen:
                    return [TextContent(type="text", text="Error: FEN position is required")]
                    
                explanation = self.analyzer.get_position_explanation(fen)
                
                return [TextContent(type="text", text=explanation)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Error explaining position: {str(e)}")]
    
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools."""
        return [
            Tool(
                name="analyze_position",
                description="Analyze a chess position using Stockfish engine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation"
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Analysis depth (default: 15)",
                            "default": 15
                        }
                    },
                    "required": ["fen"]
                }
            ),
            Tool(
                name="analyze_game",
                description="Analyze a complete chess game move by move",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "moves": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of moves in standard algebraic notation"
                        }
                    },
                    "required": ["moves"]
                }
            ),
            Tool(
                name="explain_position",
                description="Get a human-readable explanation of a chess position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "The chess position in FEN notation"
                        }
                    },
                    "required": ["fen"]
                }
            )
        ]
    
    async def run(self):
        """Run the MCP server."""
        # Register tools with the server
        for tool in self.get_tools():
            self.server.list_tools.append(tool)
            
        # Run the server
        return self.server