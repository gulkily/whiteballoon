# Data Analyst

> Create a data analyst agent that can search for real-time data, write and execute Python code to analyze it, and generate insights.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dedalus_labs.utils.stream import stream_async
  from dotenv import load_dotenv

  load_dotenv()

  def execute_python_code(code: str) -> str:
      """
      Execute Python code and return the result.
      Safely executes code in a controlled namespace.
      """
      try:
          namespace = {}
          exec(code, {"__builtins__": __builtins__}, namespace)

          if 'result' in namespace:
              return str(namespace['result'])

          results = {k: v for k, v in namespace.items() if not k.startswith('_')}
          return str(results) if results else "Code executed successfully"
      except Exception as e:
          return f"Error executing code: {str(e)}"

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = runner.run(
          input="""Research the current stock price of Tesla (TSLA) and Apple (AAPL).
          Then write and execute Python code to:
          1. Compare their current prices
          2. Calculate the percentage difference
          3. Determine which stock has grown more in the past year based on the data you find
          4. Provide investment insights based on your analysis

          Use web search to get the latest stock information.""",
          model="openai/gpt-5",
          tools=[execute_python_code],
          mcp_servers=["windsor/brave-search-mcp"],
          stream=True
      )

      await stream_async(result)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This data analyst example combines real-time web search with code execution capabilities:

  * **Brave Search MCP** (`windsor/brave-search-mcp`): Fetches real-time data from the web
  * **execute\_python\_code** tool: Allows the agent to write and run Python code for analysis

  The agent can search for current information, extract relevant data, then dynamically write code to analyze it and generate insights.

  **Note**: In production environments, consider using sandboxed code execution for security.
</Tip>
