Some reflections on vibe coding this app:

- Vibe coding does require some practice, I'm getting better results faster
  than when I started
- Claude is extremely strong when it comes to HTML/CSS/JS, I made only minor
  tweaks to the CSS
- The hype is all about MCP but OpenRouter only supported OpenAI function
  calling and that works just as well
- Helpers such as `black` and `ruff` do improve the code over the raw output
- LLMs suck at chess, they are great at post hoc rationalizations. This was
  very apparent when improving the tooling and prompting for analyzing chess.
  It might not be for other use cases
- Prompting matters a lot, for example, the response to the Dvoretsky example
  improves when 'Zugzwang' is mentioned in the request
