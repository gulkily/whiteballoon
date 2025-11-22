# Model Handoffs

> Multi-model routing where the agent intelligently selects the best model based on task complexity

This example demonstrates multi-model routing where the agent intelligently selects the best model based on task complexity, with model attributes for optimization.

<Tip>
  Claude (`anthropic/claude-sonnet-4-20250514`) is great at writing and creative tasks. Experiment with different models for different use-cases!
</Tip>

<CodeGroup>
  ```python Python theme={null}
  import os
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async
  import asyncio

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="Find the year GPT-5 released, and handoff to Claude to write a haiku about Elon Musk. Output this haiku. Use your tools.",
          model=["openai/gpt-5", "claude-sonnet-4-20250514"],
          mcp_servers=["windsor/brave-search-mcp"],
          stream=False
      )

      print(result.final_output)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>
