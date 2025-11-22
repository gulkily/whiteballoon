# Basic Tools

> Clean tool execution with the new Runner

This example demonstrates basic tool execution using the Dedalus Runner with simple mathematical tools.

<Tip>
  GPT 5 or 4.1 (`openai/gpt-5` or `openai/gpt-4.1`) are strong tool-calling models. In general, older models may struggle with tool calling.
</Tip>

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  def add(a: int, b: int) -> int:
      """Add two numbers."""
      return a + b

  def multiply(a: int, b: int) -> int:
      """Multiply two numbers."""
      return a * b

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="Calculate (15 + 27) * 2", 
          model="openai/gpt-5", 
          tools=[add, multiply]
      )

      print(f"Result: {result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>
