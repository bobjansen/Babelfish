#!/usr/bin/env python3
"""Web interface for Babelfish chess analysis using OpenRouter API."""

import os
import json
import time
from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Import our existing components
from openrouter_cli import OpenRouterClient, MCPToolConverter
from mcp_tools import MCP_TOOLS
from mcp_tool_router import MCPToolRouter

app = Flask(__name__)


@dataclass
class AnalysisResult:
    """Container for analysis results."""

    final_analysis: str
    debug_log: List[Dict[str, Any]]
    board_fen: str
    success: bool
    error_message: Optional[str] = None


class WebChessAnalyzer:
    """Web-based chess analyzer using OpenRouter."""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.client = OpenRouterClient(api_key)
        self.model = model
        self.converter = MCPToolConverter()
        self.tool_router = MCPToolRouter()

        # Convert MCP tools to OpenAI format
        self.openai_tools = self.converter.convert_mcp_tools_to_openai(MCP_TOOLS)

    def analyze_position(self, fen: str, user_question: str = None) -> AnalysisResult:
        """Analyze a chess position and return structured results."""

        debug_log = []

        try:
            # Prepare the analysis request
            if user_question:
                user_message = f"Analyze this chess position: {fen}\n\nSpecific question: {user_question}"
            else:
                user_message = (
                    f"Provide a comprehensive analysis of this chess position: {fen}"
                )

            # Create conversation with enhanced system prompt
            messages = [
                {"role": "system", "content": self._get_web_system_prompt()},
                {"role": "user", "content": user_message},
            ]

            debug_log.append(
                {
                    "type": "user_request",
                    "content": user_message,
                    "timestamp": time.time(),
                }
            )

            # Start analysis loop
            max_iterations = 16
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                debug_log.append(
                    {
                        "type": "iteration_start",
                        "iteration": iteration,
                        "timestamp": time.time(),
                    }
                )

                # Get AI response
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=self.openai_tools,
                    tool_choice="auto",
                )

                choice = response["choices"][0]
                message = choice["message"]
                finish_reason = choice["finish_reason"]

                debug_log.append(
                    {
                        "type": "ai_response",
                        "content": message.get("content", ""),
                        "finish_reason": finish_reason,
                        "tool_calls": message.get("tool_calls", []),
                        "timestamp": time.time(),
                    }
                )

                # Add assistant message to conversation
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "")

                assistant_msg = {"role": "assistant", "content": content}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)

                # If no tool calls, we're done
                if not tool_calls:
                    break

                # Execute tool calls
                for tool_call in tool_calls:
                    try:
                        function_info = tool_call.get("function", {})
                        tool_name = function_info.get("name", "")
                        arguments_str = function_info.get("arguments", "{}")
                        tool_call_id = tool_call.get("id", "unknown")

                        # Parse arguments
                        arguments = json.loads(arguments_str)

                        debug_log.append(
                            {
                                "type": "tool_call",
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "tool_call_id": tool_call_id,
                                "timestamp": time.time(),
                            }
                        )

                        # Execute tool
                        tool_result = self.tool_router.call_tool_mcp(
                            tool_name, arguments
                        )
                        result = tool_result[0].text if tool_result else "No result"

                        debug_log.append(
                            {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "result": (
                                    result[:500] + "..."
                                    if len(result) > 500
                                    else result
                                ),
                                "timestamp": time.time(),
                            }
                        )

                        # Add tool result to conversation
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": result,
                            }
                        )

                    except Exception as e:
                        error_msg = f"Tool execution error: {str(e)}"
                        debug_log.append(
                            {
                                "type": "error",
                                "error": error_msg,
                                "timestamp": time.time(),
                            }
                        )

                        # Add error as tool result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": error_msg,
                            }
                        )

            # Extract final analysis from the last assistant message
            final_analysis = ""
            for msg in reversed(messages):
                if msg["role"] == "assistant" and msg.get("content"):
                    final_analysis = msg["content"]
                    break

            return AnalysisResult(
                final_analysis=final_analysis,
                debug_log=debug_log,
                board_fen=fen,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                final_analysis="",
                debug_log=debug_log,
                board_fen=fen,
                success=False,
                error_message=str(e),
            )

    def _get_web_system_prompt(self) -> str:
        """Get enhanced system prompt for web interface."""
        return """You are Babelfish, an expert chess coach with powerful analysis tools.

CRITICAL INSTRUCTIONS FOR WEB INTERFACE:
1. You MUST use tools to analyze positions before making statements
2. Always visualize the board when discussing piece interactions
3. Provide analysis in clear, well-structured markdown format
4. Clearly separate your final analysis with a markdown header

WEB OUTPUT FORMAT:
Structure your response exactly like this:

## 🔍 Analysis Results

[Your comprehensive analysis here in markdown format]

### Key Findings
- Key tactical motifs discovered
- Strategic plans for both sides
- Critical weaknesses or strengths

### Recommended Moves
- Best moves with explanations
- Alternative options to consider

### Learning Points
- Important chess principles illustrated
- Patterns to remember

MARKDOWN REQUIREMENTS:
- Use ## for main headers, ### for subheaders
- Use **bold** for emphasis
- Use bullet points for lists
- Use > for important quotes or principles
- Keep it readable and well-organized

TOOL USAGE:
- ALWAYS use visualize_board before discussing piece positions
- Use analyze_position for deep evaluation
- Use find_tactical_motifs for tactical analysis
- Never make geometric claims without visual verification

Your goal: Provide expert analysis that combines precise engine evaluation with educational chess coaching, formatted beautifully in markdown."""


# Flask routes
@app.route("/")
def index():
    """Main page with chess analysis interface."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze a chess position."""
    data = request.get_json()
    fen = data.get("fen", "")
    question = data.get("question", "")

    if not fen:
        return jsonify({"success": False, "error": "FEN position is required"})

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify(
            {
                "success": False,
                "error": "OPENROUTER_API_KEY environment variable not set",
            }
        )

    # Get model from config (default to claude-3.5-sonnet if not set)
    model = app.config.get('MODEL', 'anthropic/claude-3.5-sonnet')
    
    # Perform analysis
    analyzer = WebChessAnalyzer(api_key, model)
    result = analyzer.analyze_position(fen, question)

    return jsonify(
        {
            "success": result.success,
            "analysis": result.final_analysis,
            "debug_log": result.debug_log,
            "board_fen": result.board_fen,
            "error": result.error_message,
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "babelfish-web"})


if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY=your_key_here")
        exit(1)

    print("🐟 Starting Babelfish Web Interface...")
    print("🌐 Access at: http://localhost:5000")
    print(
        "🔑 Using OpenRouter API key:",
        api_key[:12] + "..." if len(api_key) > 12 else "***",
    )

    app.run(debug=True, port=5000)
