# Quickstart

> Get started with the Dedalus SDK.

# Setup and Integration

<AccordionGroup defaultOpen>
  <Accordion icon="key" title="Get Your API Key" defaultOpen>
    To use Dedalus Labs, you'll need an API key. To get one:

    1. Create an account at [dedaluslabs.ai](https://dedaluslabs.ai).
    2. Navigate to your dashboard.
    3. Generate a new API key in the settings section.
    4. Add your API key to your environment as `DEDALUS_API_KEY`. For local development, create a `.env` file with:

    ```bash  theme={null}
    DEDALUS_API_KEY=your_api_key_here
    ```

    Keep your API key secure and never share it publicly.

    **HTTP API Authentication**: When making direct HTTP requests, pass your API key using either:

    * `Authorization: Bearer <your_api_key>` header, or
    * `x-api-key: <your_api_key>` header
  </Accordion>

  <Accordion icon="code" title="Install Our SDK" defaultOpen>
    We provide SDKs for multiple programming languages to make integration seamless:

    <CodeGroup>
      ```bash Python theme={null}
      pip install dedalus-labs
      ```

      ```bash TypeScript theme={null}
      npm install dedalus-labs
      ```
    </CodeGroup>
  </Accordion>

  <Accordion icon="hand-wave" title="Hello World" defaultOpen>
    This example demonstrates the most basic usage of the Dedalus SDK - making a simple chat completion call.

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

          response = await runner.run(
              input="What was the score of the 2025 Wimbledon final?",
              model="openai/gpt-5-mini",
              mcp_servers=["windsor/exa-search-mcp"]
          )

          print(response.final_output)

      if __name__ == "__main__":
          asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      Coming soon.
      ```
    </CodeGroup>
  </Accordion>

  <Accordion icon="hammer" title="Basic Tools" defaultOpen>
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
  </Accordion>
</AccordionGroup>

<CardGroup cols={4}>
  <Card title="Streaming" icon="water" href="examples/03-streaming" />

  <Card title="MCP Integration" icon="plug" href="examples/04-mcp-integration" />

  <Card title="Model Handoffs" icon="arrows-rotate" href="examples/06-handoffs" />

  <Card title="Tool Chaining" icon="link" href="examples/07-tool-chaining" />
</CardGroup>

# Next Steps

<Card title="View the Examples" icon="book-open" href="examples/use-case/travel-agent">
  See detailed examples for your use-case
</Card>

<Card title="Join Our Community" icon="discord" href="https://discord.com/invite/RuDhZKnq5R">
  Get help, suggest improvements, and connect with other developers.
</Card>
