# Travel Agent

> Creating a travel planning agent that can search for flights, hotels, and provide travel recommendations.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="""I'm planning a trip to Paris, France from New York City 
          for 5 days in October. Can you help me find:
          1. Flight options and prices
          2. Hotel recommendations in central Paris
          3. Weather forecast for my travel dates
          4. Popular attractions and restaurants
          5. Currency exchange rates and travel tips
          
          My budget is around $3000 total and I prefer mid-range accommodations.""",
          model="openai/gpt-4.1",
          mcp_servers=[
              "joerup/exa-mcp",        # For semantic travel research
              "windsor/brave-search-mcp", # For travel information search
              "joerup/open-meteo-mcp"   # For weather at destination
          ]
      )

      print(f"Travel Planning Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This travel agent example uses multiple MCP servers:

  * **Exa MCP** (`joerup/exa-mcp`): For semantic search of travel content and recommendations
  * **Brave Search MCP** (`windsor/brave-search-mcp`): For finding current travel information, reviews, and booking options
  * **Open Meteo MCP** (`joerup/open-meteo-mcp`): For weather forecasts at your destination

  Try these servers out in your projects!
</Tip>

# Web Search Agent

> Create a web search agent using multiple search MCPs to find and analyze information from the web.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="""I need to research the latest developments in AI agents for 2024. 
          Please help me:
          1. Find recent news articles about AI agent breakthroughs
          2. Search for academic papers on multi-agent systems
          3. Look up startup companies working on AI agents
          4. Find GitHub repositories with popular agent frameworks
          5. Summarize the key trends and provide relevant links
          
          Focus on developments from the past 6 months.""",
          model="openai/gpt-4.1",
          mcp_servers=[
              "joerup/exa-mcp",        # Semantic search engine
              "windsor/brave-search-mcp"  # Privacy-focused web search
          ]
      )

      print(f"Web Search Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This example uses multiple search MCP servers:

  * **Exa MCP** (`joerup/exa-mcp`)
  * **Brave Search MCP** (`windsor/brave-search-mcp`)

  Try these servers out in your projects!
</Tip>

# Weather Forecaster

> Create a weather forecasting agent using the Open Meteo MCP to provide detailed weather information and forecasts.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="""I'm planning a outdoor wedding in San Francisco next weekend. 
          Can you provide:
          1. Current weather conditions
          2. 7-day forecast with hourly details
          3. Probability of precipitation
          4. Temperature highs and lows
          5. Wind conditions and UV index
          6. Recommendations for outdoor event planning based on the forecast""",
          model="openai/gpt-4.1",
          mcp_servers=["joerup/open-meteo-mcp"]
      )

      print(f"Weather Forecast Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This example uses the Open Meteo MCP (`joerup/open-meteo-mcp`) which provides:

  * Current weather conditions
  * Multi-day weather forecasts
  * Hourly weather data
  * Historical weather information
  * Weather alerts and warnings

  Try it out in your projects!
</Tip>

# Concert Planner

> Create a concert planner agent using the Ticketmaster MCP to search for concerts and venue information.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="""I want to see Taylor Swift perform in New York City. 
          Can you help me find upcoming concerts, get details about the venue, 
          and provide information about ticket prices? I'm particularly interested 
          in accessibility information and seating options.""",
          model="openai/gpt-4.1",
          mcp_servers=["windsor/ticketmaster-mcp"]
      )

      print(f"Concert Planning Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This example uses the Ticketmaster MCP (`windsor/ticketmaster-mcp`).

  Try it out in your projects!
</Tip>

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

