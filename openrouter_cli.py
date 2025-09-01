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
    ) -> Dict[str, Any]:
        """Send chat completion request with optional tool calling."""

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

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions", json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise


class MCPToolConverter:
    """Converts MCP tool definitions to OpenAI function calling format."""

    @staticmethod
    def convert_mcp_tools_to_openai(
        mcp_tools: List
    ) -> List[Dict[str, Any]]:
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
        self.messages: List[Dict[str, Any]] = []
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
        """Reset conversation history."""
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
        MAX_CHARS = 8000  # Conservative limit for OpenRouter

        result_str = json.dumps(result, default=str)
        if len(result_str) > MAX_CHARS:
            # Create a summary instead
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
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]

            console.print(f"[blue]🔧 Executing tool:[/blue] {tool_name}")
            console.print(f"[dim]Arguments: {arguments}[/dim]")

            # Execute the tool
            result = self.execute_tool(tool_name, arguments, user_id)

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
                "[bold green]Babelfish CLI[/bold green]\n"
                f"Model: {self.model}\n"
                f"Available tools: {len(self.openai_tools)}\n"
                "Type 'quit', 'exit', or 'q' to end the conversation.\n"
                "Type '/help' for available commands.",
                title="Welcome",
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
                max_iterations = 5
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
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
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
        else:
            console.print(f"[red]Unknown command: {command}[/red]")

    def _show_help(self):
        """Show available commands."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="white")

        help_table.add_row("/help", "Show this help message")
        help_table.add_row("/models", "List available models")
        help_table.add_row("/tools", "List available MCP tools")
        help_table.add_row("/reset", "Reset conversation history")
        help_table.add_row("/history", "Show conversation history")
        help_table.add_row("/model <name>", "Change the current model")
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
        """Show available MCP tools."""
        tool_table = Table(title="Available MCP Tools")
        tool_table.add_column("Tool Name", style="cyan")
        tool_table.add_column("Description", style="white")

        for tool in MCP_TOOLS[:10]:  # Show first 10 tools
            tool_table.add_row(tool.name, tool.description[:80] + "...")

        console.print(tool_table)
        console.print(f"[dim]Showing 10 of {len(MCP_TOOLS)} available tools[/dim]")

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


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Babelfish OpenRouter CLI")
    parser.add_argument(
        "--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--model", default="anthropic/claude-3.5-sonnet", help="Model to use"
    )
    parser.add_argument(
        "--backend", choices=["sqlite", "postgresql"], help="Database backend"
    )
    parser.add_argument("--db-url", help="Database connection URL for PostgreSQL")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OpenRouter API key required.[/red]")
        console.print("Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)

    # Set environment variables if provided
    if args.backend:
        os.environ["PANTRY_BACKEND"] = args.backend
    if args.db_url:
        os.environ["PANTRY_DATABASE_URL"] = args.db_url

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
