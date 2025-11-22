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
