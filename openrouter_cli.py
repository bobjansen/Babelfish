#!/usr/bin/env python3
"""
OpenRouter CLI - Interactive command-line interface with MCP tool integration

This CLI app integrates with OpenRouter to provide LLM capabilities with access
to our MCP tools for chess coaching.
"""

import os
import sys
import json
import argparse
import logging
import time
from typing import Dict, Any, List, Optional
import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.status import Status
from rich.table import Table

# Import our MCP components
from mcp_tools import MCP_TOOLS
from mcp_tool_router import MCPToolRouter

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

console = Console()


class OpenRouterClient:
    """OpenRouter API client with function calling support."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/bobjansen/babelfish",
                "X-Title": "Babelfish CLI",
            }
        )

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter."""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Send chat completion request with optional tool calling and retry logic."""

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions", json=payload
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_error = e
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries:
                        # Exponential backoff: 1s, 2s, 4s
                        wait_time = 2**attempt
                        logger.warning(
                            f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limit exceeded after all retries")
                        raise e
                elif e.response.status_code >= 500:  # Server error
                    if attempt < max_retries:
                        wait_time = 1
                        logger.warning(
                            f"Server error {e.response.status_code}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Server error after all retries")
                        raise e
                else:
                    # Client error (4xx), don't retry
                    logger.error(f"Chat completion failed: {e}")
                    raise e

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 1
                    logger.warning(
                        f"Request failed: {e}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Chat completion failed after all retries: {e}")
                    raise e

        # This should never be reached, but just in case
        raise last_error or Exception("Unknown error in chat completion")


class MCPToolConverter:
    """Converts MCP tool definitions to OpenAI function calling format."""

    @staticmethod
    def convert_mcp_tools_to_openai(mcp_tools: List) -> List[Dict[str, Any]]:
        """Convert MCP tool definitions to OpenAI function calling format."""
        openai_tools = []

        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            openai_tools.append(openai_tool)

        return openai_tools


class ConversationManager:
    """Manages conversation history and context."""

    def __init__(self):
        # Start with a system message that encourages tool use
        self.messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": """You are Babelfish, an expert chess coach with access to powerful chess analysis tools.

CRITICAL: You MUST use your chess analysis tools to provide accurate, detailed chess coaching. Never guess about positions, evaluations, or moves without first analyzing them with the appropriate tools.

Available tools and when to use them:
- analyze_position: ALWAYS use this first when given a FEN position to get evaluation, best moves, and context
- visualize_board: Use whenever discussing positions to show the actual board layout - essential for understanding
- suggest_move: When asked for move recommendations
- evaluate_move_quality: To assess if a specific move was good/bad/blunder
- get_principal_variation: To show the best continuation from a position
- find_tactical_motifs: To identify pins, forks, skewers, and other tactics
- analyze_game: When given a series of moves to analyze
- analyze_endgame: For positions with few pieces remaining
- explain_position: For human-readable position explanations

TOOL USAGE PRINCIPLES:
1. ALWAYS analyze positions with tools before discussing them
2. Use visualize_board frequently so users can see what you're talking about
3. When users mention moves or positions, immediately use tools to understand them
4. Use multiple tools in sequence for comprehensive analysis
5. Don't just describe - SHOW with board visualizations and concrete analysis

CRITICAL ACCURACY RULES:
• NEVER make tactical claims without visualizing the board first
• ALWAYS use visualize_board before stating what pieces attack what squares
• Verify every tactical statement by looking at the actual board layout
• If you mention piece interactions (attacks, defenses, pins), you MUST show the board
• Remember: pawns attack diagonally only, pieces move in specific patterns
• Double-check geometric relationships - can piece X actually reach square Y?

COACHING AFTER ANALYSIS:
After using tools to gather concrete data, you MUST provide human coaching that includes:
• **Key Motifs**: Explain tactical/positional themes you discovered (pins, forks, weak squares, etc.)
• **Strategic Plans**: Outline concrete plans for both sides based on the position
• **Learning Points**: Highlight important chess principles or patterns users should remember
• **Next Steps**: Suggest specific moves or ideas to explore further
• **Context**: Connect the analysis to broader chess understanding

RESPONSE STRUCTURE:
1. Use tools to analyze (visualize board, analyze position, find tactics, etc.)
2. Present tool results clearly
3. Then provide YOUR COACHING SUMMARY with motifs, plans, and learning insights
4. Make it educational - help users understand WHY, not just WHAT

MANDATORY BOARD VISUALIZATION:
You MUST use visualize_board tool when:
• Making any claim about piece attacks or defenses
• Discussing tactical motifs (pins, forks, skewers)
• Explaining why a move works or doesn't work
• Describing geometric relationships between pieces
• Before making statements like "X attacks Y" or "this creates a fork"

COACHING LANGUAGE EXAMPLES:
• "Based on this analysis, the key motif here is..."
• "The strategic plan for White should focus on..."
• "This position teaches us the important principle that..."
• "Looking at the tactical scan, I notice..."
• "The critical imbalance in this position is..."

NEVER SAY THINGS LIKE:
• "The pawn on g4 attacks the pawn on c6" (geometrically impossible)
• "The knight forks the king and queen" (without showing the board)
• "This move pins the bishop" (without verifying the pin exists)
• "The rook controls the file" (without checking if path is clear)
USE TOOLS TO VERIFY ALL TACTICAL CLAIMS!

Your goal is to combine precise engine analysis with expert human chess coaching. Be both analytical AND educational!

FINAL ANALYSIS FORMAT:
End your response with a clear markdown-formatted summary under this exact header:

## 🔍 Final Analysis

Use proper markdown formatting:
- **Bold** for emphasis
- ### Subheaders for sections  
- > Blockquotes for key principles
- Bullet points for lists
- Clear, readable structure

This makes your analysis easy to read and understand!""",
            }
        ]
        self.tool_call_count = 0
        self.max_tool_calls = 10  # Prevent infinite loops

    def add_user_message(self, content: str):
        """Add user message to conversation."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(
        self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None
    ):
        """Add assistant message to conversation."""
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.messages.append(message)

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str):
        """Add tool execution result to conversation."""
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": result,
            }
        )

    def reset(self):
        """Reset conversation history but keep the system message."""
        # Keep only the system message (first message)
        if self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages.clear()
        self.tool_call_count = 0

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get current conversation messages."""
        return self.messages.copy()


class BabelfishMCPCLI:
    """Main CLI application class."""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.client = OpenRouterClient(api_key)
        self.model = model
        self.converter = MCPToolConverter()
        self.conversation = ConversationManager()

        # Initialize MCP components
        self.tool_router = MCPToolRouter()
        self.user_manager = None

        # Convert MCP tools to OpenAI format
        self.openai_tools = self.converter.convert_mcp_tools_to_openai(MCP_TOOLS)

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], user_id: Optional[int] = None
    ) -> str:
        """Execute an MCP tool and return the result."""
        try:
            # Execute tool through the router
            result = self.tool_router.call_tool(tool_name, arguments)

            # Truncate large results to avoid API limits
            result = self._truncate_large_results(result, tool_name)

            # Format result as JSON string
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            error_result = {"error": str(e), "tool": tool_name, "arguments": arguments}
            logger.error(f"Tool execution failed: {e}")
            return json.dumps(error_result, indent=2)

    def _truncate_large_results(
        self, result: Dict[str, Any], tool_name: str
    ) -> Dict[str, Any]:
        """Truncate large results to avoid API message size limits."""
        MAX_CHARS = 12000  # Increased limit for chess analysis responses

        result_str = json.dumps(result, default=str)
        if len(result_str) > MAX_CHARS:
            # For chess tools, try to preserve the message content
            if tool_name in [
                "analyze_position",
                "suggest_move",
                "get_principal_variation",
                "evaluate_move_quality",
                "find_tactical_motifs",
                "analyze_endgame",
                "explain_position",
            ]:
                # Truncate the message but preserve structure
                if "message" in result and len(result["message"]) > MAX_CHARS - 500:
                    result["message"] = (
                        result["message"][: MAX_CHARS - 500]
                        + "\n\n*[Response truncated for length]*"
                    )
                    result["truncated"] = True
                return result
            else:
                # Create a summary for other tools
                summary_result = {
                    "status": result.get("status", "success"),
                    "message": f"Result too large ({len(result_str)} chars). ",
                    "tool_name": tool_name,
                    "truncated": True,
                }
                return summary_result

        return result

    def process_tool_calls(
        self, tool_calls: List[Dict[str, Any]], user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Process and execute tool calls from the assistant."""
        results = []

        for tool_call in tool_calls:
            try:
                # Extract tool information with error handling
                function_info = tool_call.get("function", {})
                tool_name = function_info.get("name", "")
                arguments_str = function_info.get("arguments", "{}")
                tool_call_id = tool_call.get("id", "unknown")

                # Parse arguments safely first
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError as e:
                    console.print(f"[red]⚠️  Error parsing arguments: {e}[/red]")
                    arguments = {}

                if not tool_name:
                    # Try to infer the tool name from the arguments
                    inferred_name = self._infer_tool_name(arguments)
                    if inferred_name:
                        tool_name = inferred_name
                        console.print(
                            f"[yellow]⚠️  Tool call missing name, inferred: {tool_name}[/yellow]"
                        )
                    else:
                        console.print(
                            "[red]⚠️  Warning: Tool call missing name and cannot infer[/red]"
                        )
                        console.print(f"[dim]Tool call structure: {tool_call}[/dim]")
                        console.print(f"[dim]Parsed arguments: {arguments}[/dim]")
                        continue

                # Final validation before execution
                if tool_name not in self.tool_router.tools:
                    console.print(f"[red]⚠️  Warning: Unknown tool '{tool_name}'[/red]")
                    available = list(self.tool_router.tools.keys())
                    console.print(f"[dim]Available tools: {', '.join(available)}[/dim]")
                    continue

                console.print(f"[blue]🔧 Executing tool:[/blue] {tool_name}")
                console.print(f"[dim]Arguments: {arguments}[/dim]")

                # Execute the tool
                result = self.execute_tool(tool_name, arguments, user_id)

                # Display the tool result to the user
                self._display_tool_result(tool_name, result)

            except Exception as e:
                console.print(f"[red]⚠️  Error processing tool call: {e}[/red]")
                tool_name = "unknown"
                tool_call_id = tool_call.get("id", "unknown")
                result = json.dumps({"error": str(e), "status": "error"})

            # Add result to conversation
            self.conversation.add_tool_result(tool_call_id, tool_name, result)

            results.append(
                {"tool_call_id": tool_call_id, "tool_name": tool_name, "result": result}
            )

        return results

    def chat_loop(self, user_id: Optional[int] = None):
        """Main chat loop."""
        console.print(
            Panel(
                "[bold green]Babelfish CLI - Expert Chess Coach[/bold green]\n\n"
                f"Model: {self.model}\n"
                f"Available chess analysis tools: {len(self.openai_tools)}\n\n"
                "[bold cyan]🐟 Your AI chess coach uses powerful analysis tools![/bold cyan]\n"
                "• Provide chess positions (FEN notation) for deep analysis\n"
                "• Ask about specific moves or game situations\n"
                "• Get tactical analysis, evaluations, and move suggestions\n\n"
                "[yellow]Commands:[/yellow] '/tools' to see available tools, '/help' for all commands\n"
                "[dim]Type 'quit', 'exit', or 'q' to end the conversation.[/dim]",
                title="🐟 Welcome to Babelfish",
            )
        )

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")

                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # Add user message to conversation
                self.conversation.add_user_message(user_input)

                # Start tool call loop
                max_iterations = 16  # Increased from 5 to handle complex chess analysis
                iteration = 0

                while iteration < max_iterations:
                    iteration += 1

                    with Status("[dim]Thinking...[/dim]"):
                        response = self.client.chat_completion(
                            messages=self.conversation.get_messages(),
                            model=self.model,
                            tools=self.openai_tools,
                            tool_choice="auto",
                        )

                    choice = response["choices"][0]
                    message = choice["message"]
                    finish_reason = choice["finish_reason"]

                    # Add assistant message
                    tool_calls = message.get("tool_calls", [])
                    content = message.get("content", "")

                    if content:
                        console.print(
                            f"\n[bold green]Assistant[/bold green]: {content}"
                        )

                    self.conversation.add_assistant_message(content, tool_calls)

                    # Handle tool calls
                    if tool_calls and finish_reason == "tool_calls":
                        self.process_tool_calls(tool_calls, user_id)
                        # Add a longer delay to prevent rapid API calls and respect rate limits
                        time.sleep(1.0)  # Increased from 0.5s to 1s
                        continue  # Continue the loop for follow-up
                    else:
                        break  # No more tool calls, exit loop

                if iteration >= max_iterations:
                    console.print(
                        f"[yellow]Maximum iterations ({max_iterations}) reached.[/yellow]"
                    )

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    console.print(
                        f"[yellow]⚠️  Rate limit exceeded. Please wait a moment before trying again.[/yellow]"
                    )
                    console.print(
                        f"[dim]You may have hit OpenRouter's rate limits. Consider using a different model or waiting a few minutes.[/dim]"
                    )
                elif e.response.status_code == 401:
                    console.print(
                        f"[red]❌ Authentication failed. Please check your OpenRouter API key.[/red]"
                    )
                elif e.response.status_code >= 500:
                    console.print(
                        f"[red]❌ Server error ({e.response.status_code}). OpenRouter may be experiencing issues.[/red]"
                    )
                else:
                    console.print(
                        f"[red]❌ API Error ({e.response.status_code}): {e}[/red]"
                    )
                logger.error(f"API error: {e}")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                logger.error(f"Chat loop error: {e}")

    def _handle_command(self, command: str):
        """Handle CLI commands."""
        command = command.lower().strip()

        if command == "/help":
            self._show_help()
        elif command == "/models":
            self._show_models()
        elif command == "/tools":
            self._show_tools()
        elif command == "/reset":
            self.conversation.reset()
            console.print("[green]Conversation reset[/green]")
        elif command == "/history":
            self._show_history()
        elif command.startswith("/model "):
            model_name = command.split(" ", 1)[1]
            self.model = model_name
            console.print(f"[green]Model set to: {model_name}[/green]")
        elif command == "/limits":
            self._show_rate_limits()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")

    def _show_help(self):
        """Show available commands."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="white")

        help_table.add_row("/tools", "[bold]🐟 View chess analysis tools[/bold]")
        help_table.add_row("/help", "Show this help message")
        help_table.add_row("/models", "List available models")
        help_table.add_row("/reset", "Reset conversation history")
        help_table.add_row("/history", "Show conversation history")
        help_table.add_row("/model <name>", "Change the current model")
        help_table.add_row("/limits", "Show rate limit information")
        help_table.add_row("quit/exit/q", "Exit the CLI")

        console.print(help_table)

    def _show_models(self):
        """Show available OpenRouter models."""
        with Status("[dim]Fetching models...[/dim]"):
            models = self.client.get_models()

        if not models:
            console.print("[red]Failed to fetch models[/red]")
            return

        # Show popular models
        popular_models = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-8b-instruct",
            "google/gemini-pro",
        ]

        model_table = Table(title="Popular Models for Chess Playing")
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Provider", style="green")
        model_table.add_column("Context", style="yellow")

        for model_data in models:
            if model_data["id"] in popular_models:
                model_table.add_row(
                    model_data["id"],
                    model_data.get("name", ""),
                    f"{model_data.get('context_length', 'Unknown'):,}",
                )

        console.print(model_table)
        console.print(f"[dim]Current model: {self.model}[/dim]")
        console.print(f"[dim]Total available models: {len(models)}[/dim]")

    def _show_tools(self):
        """Show available MCP tools with chess-specific guidance."""
        console.print(
            Panel(
                "[bold cyan]🐟 Chess Analysis Tools[/bold cyan]\n\n"
                "Your AI coach uses these tools to provide expert analysis:\n\n"
                "[bold yellow]Essential Tools:[/bold yellow]\n"
                "• [cyan]analyze_position[/cyan] - Deep analysis of any position (provide FEN)\n"
                "• [cyan]visualize_board[/cyan] - Show the board layout clearly\n"
                "• [cyan]suggest_move[/cyan] - Get the best move recommendations\n\n"
                "[bold yellow]Advanced Analysis:[/bold yellow]\n"
                "• [cyan]evaluate_move_quality[/cyan] - Was that move good/bad/blunder?\n"
                "• [cyan]find_tactical_motifs[/cyan] - Spot pins, forks, skewers\n"
                "• [cyan]get_principal_variation[/cyan] - See the best continuation\n"
                "• [cyan]analyze_endgame[/cyan] - Specialized endgame analysis\n"
                "• [cyan]analyze_game[/cyan] - Full game move-by-move analysis\n\n"
                "[bold green]💡 Pro Tips:[/bold green]\n"
                "- Just provide a FEN position and ask questions!\n"
                "- The AI uses tools first, then provides expert coaching\n"
                "- You'll get both engine analysis AND human explanations\n"
                "- Try: 'Analyze this position: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'\n"
                "- Or: 'What are the key motifs in this position?'",
                title="🔧 Available Chess Tools",
            )
        )

    def _show_history(self):
        """Show conversation history."""
        if not self.conversation.messages:
            console.print("[yellow]No conversation history[/yellow]")
            return

        console.print(Panel("Conversation History", style="blue"))
        for i, msg in enumerate(
            self.conversation.messages[-10:], 1
        ):  # Show last 10 messages
            role = msg["role"].title()
            content = msg.get("content", "")[:200]  # Truncate long messages
            if msg.get("tool_calls"):
                content += f" [Tool calls: {len(msg['tool_calls'])}]"

            console.print(f"[dim]{i}.[/dim] [bold]{role}[/bold]: {content}")

    def _show_rate_limits(self):
        """Show rate limit information and tips."""
        limits_panel = Panel(
            """[bold yellow]Rate Limit Information[/bold yellow]

[cyan]Current Settings:[/cyan]
• Retry attempts: 3 with exponential backoff
• Delay between tool calls: 1 second
• Max iterations per conversation: 8

[cyan]If you encounter rate limits:[/cyan]
• Wait 1-2 minutes between complex requests
• Try using a different model (e.g., Claude Haiku is faster/cheaper)
• Consider reducing analysis depth for chess tools
• Break complex queries into smaller parts

[cyan]Rate Limit Friendly Models:[/cyan]
• anthropic/claude-3-haiku (fastest, cheapest)
• openai/gpt-4o-mini (good balance)
• meta-llama/llama-3.1-8b-instruct (economical)

[dim]Note: Rate limits vary by model and your OpenRouter plan.[/dim]""",
            title="Rate Limits",
            border_style="yellow",
        )
        console.print(limits_panel)

    def _infer_tool_name(self, arguments: Dict[str, Any]) -> Optional[str]:
        """Infer the tool name from arguments when name is missing."""
        if not isinstance(arguments, dict):
            return None

        # Get available tools from the router
        available_tools = list(self.tool_router.tools.keys())

        # Inference logic based on argument patterns
        if "fen" in arguments:
            if "move" in arguments:
                # Has both fen and move -> likely evaluate_move_quality
                return (
                    "evaluate_move_quality"
                    if "evaluate_move_quality" in available_tools
                    else None
                )
            elif "moves" in arguments:
                # Has fen and moves -> likely analyze_game
                return "analyze_game" if "analyze_game" in available_tools else None
            elif "max_moves" in arguments:
                # Has fen with max_moves -> likely get_principal_variation
                return (
                    "get_principal_variation"
                    if "get_principal_variation" in available_tools
                    else None
                )
            elif arguments.get("depth", 0) >= 25:
                # Has fen with very high depth (25+) -> likely analyze_endgame
                return (
                    "analyze_endgame" if "analyze_endgame" in available_tools else None
                )
            else:
                # Just has fen -> could be several tools, default to most common
                # Priority: analyze_position > explain_position > suggest_move
                for tool in ["analyze_position", "explain_position", "suggest_move"]:
                    if tool in available_tools:
                        return tool
        elif "moves" in arguments:
            # Only has moves -> analyze_game
            return "analyze_game" if "analyze_game" in available_tools else None

        return None

    def _display_tool_result(self, tool_name: str, result_json: str):
        """Display the tool result to the user in a nicely formatted way."""
        try:
            # Parse the result
            result = json.loads(result_json)

            if result.get("status") == "success":
                message = result.get("message", "")

                # Check if it's a chess tool result (contains the 🐟 symbol)
                if "🐟" in message:
                    # Display chess analysis results with special formatting
                    console.print(f"\n[green]📋 Tool Result ({tool_name}):[/green]")

                    # Split the message into sections for better readability
                    lines = message.split("\n")
                    formatted_lines = []

                    for line in lines:
                        if line.startswith("🐟"):
                            # Main header - make it stand out
                            formatted_lines.append(
                                f"[bold magenta on black]{line}[/bold magenta on black]"
                            )
                        elif (
                            line.startswith("**")
                            and line.endswith("**")
                            and len(line) > 4
                        ):
                            # Bold section headers - remove ** and color
                            clean_line = line.replace("**", "")
                            formatted_lines.append(
                                f"[bold yellow]{clean_line}[/bold yellow]"
                            )
                        elif (
                            line.startswith("*")
                            and line.endswith("*")
                            and not line.startswith("**")
                        ):
                            # Italic text (analysis notes) - remove * and make dim
                            clean_line = line.replace("*", "")
                            formatted_lines.append(
                                f"[dim italic]{clean_line}[/dim italic]"
                            )
                        elif (
                            line.strip()
                            and len(line) > 0
                            and (line.strip()[0].isdigit() or line.startswith("•"))
                        ):
                            # Numbered lists or bullet points - highlight moves
                            formatted_lines.append(f"[bright_cyan]{line}[/bright_cyan]")
                        elif line.strip():
                            formatted_lines.append(f"[white]{line}[/white]")
                        else:
                            formatted_lines.append(line)  # Keep empty lines as-is

                    formatted_message = "\n".join(formatted_lines)
                    console.print(formatted_message)
                    console.print("")  # Add spacing

                else:
                    # Non-chess tool result
                    console.print(f"\n[green]📋 Tool Result ({tool_name}):[/green]")
                    console.print(message)
                    console.print("")

            elif result.get("status") == "error":
                error_msg = result.get("message", "Unknown error")
                console.print(f"\n[red]❌ Tool Error ({tool_name}):[/red]")
                console.print(f"[red]{error_msg}[/red]")
                console.print("")

            else:
                # Fallback for unexpected result format
                console.print(f"\n[yellow]🔧 Tool Output ({tool_name}):[/yellow]")
                console.print(result_json[:500])  # Limit length
                if len(result_json) > 500:
                    console.print("[dim]...[truncated][/dim]")
                console.print("")

        except json.JSONDecodeError:
            # If result isn't valid JSON, display as-is (truncated)
            console.print(f"\n[yellow]🔧 Tool Output ({tool_name}):[/yellow]")
            console.print(result_json[:500])
            if len(result_json) > 500:
                console.print("[dim]...[truncated][/dim]")
            console.print("")
        except Exception as e:
            console.print(f"\n[red]❌ Error displaying tool result: {e}[/red]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Babelfish OpenRouter CLI")
    parser.add_argument(
        "--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--model", default="anthropic/claude-3.5-sonnet", help="Model to use"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OpenRouter API key required.[/red]")
        console.print("Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)

    try:
        # Initialize and start CLI
        cli = BabelfishMCPCLI(api_key, args.model)
        cli.chat_loop()

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
