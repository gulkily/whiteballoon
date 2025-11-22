# Streaming

> Streaming responses with Agent system

This example demonstrates streaming agent output using the built-in streaming support with the Agent system.

<CodeGroup>
  ```python Async Streaming theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = runner.run(
          input="What do you think of Mulligan?",
          model="openai/gpt-5-mini",
          stream=True
      )

      # use stream parameter and stream_async function to stream output
      await stream_async(result)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```python Sync Streaming theme={null}
  from dedalus_labs import Dedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_sync

  load_dotenv()

  def main():
      client = Dedalus()
      runner = DedalusRunner(client)

      result = runner.run(
          input="What do you think of Mulligan?",
          model="openai/gpt-5-mini",
          stream=True
      )

      # use stream parameter and stream_sync function to stream output
      stream_sync(result)

  if __name__ == "__main__":
      main()
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>
