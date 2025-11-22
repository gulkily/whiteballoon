# Hello World

> Basic chat completion with Dedalus

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

# MCP Integration

> Basic remote MCP server usage with the Dedalus SDK

This example demonstrates basic remote MCP (Model Context Protocol) server usage with the Dedalus SDK for connecting to external tools and services.

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
          input="Who won Wimbledon 2025?",
          model="openai/gpt-5-mini",
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

# Structured Outputs

> Type-safe JSON responses with Pydantic models

Ensure model responses adhere to a schema you define. Dedalus provides OpenAI-compatible structured outputs with automatic Pydantic validation.

<Note>
  **API Compatibility**

  Dedalus supports structured outputs via the **Chat Completions API** (`/chat/completions`), which is the industry standard interface supported across providers.

  OpenAI's **Responses API** (`/responses`) uses different parameter names (`input`, `text_format`, `output_parsed`) and requires additional infrastructure. We do not support it yet. The Chat Completions API provides equivalent functionality with broader compatibility.

  All examples below use the Chat Completions API.
</Note>

<Tip>
  **Dedalus API**

  We are committed to full Chat Completions API support and will build Dedalus-native features on Chat Completions semantics. While we will maintain feature parity with the Responses API where applicable, its integration is a lower priority. Chat Completions has broader backward compatibility with existing codebases and tooling across the ecosystem.
</Tip>

## Client API

The client provides three methods for structured outputs:

* **`.parse()`** - Non-streaming with Pydantic models
* **`.stream()`** - Streaming with Pydantic models (context manager)
* **`.create()`** - Dict-based schemas only (rejects Pydantic)

### Basic Usage with .parse()

<CodeGroup>
  ```python Non-Streaming theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int
      occupation: str
      skills: list[str]

  async def main():
      client = AsyncDedalus()

      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[
              {"role": "user", "content": "Profile for Alice, 28, software engineer"}
          ],
          response_format=PersonInfo,
      )

      # Access parsed Pydantic model
      person = completion.choices[0].message.parsed
      print(f"{person.name}, {person.age}")
      print(f"Skills: {', '.join(person.skills)}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

### Streaming with .stream()

<CodeGroup>
  ```python Streaming Events theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int
      occupation: str
      skills: list[str]

  async def main():
      client = AsyncDedalus()

      # Use context manager for streaming
      async with client.chat.completions.stream(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Profile for Bob, 32, data scientist"}],
          response_format=PersonInfo,
      ) as stream:
          # Process events as they arrive
          async for event in stream:
              if event.type == "content.delta":
                  print(event.delta, end="", flush=True)
              elif event.type == "content.done":
                  # Snapshot available at content.done
                  print(f"\nSnapshot: {event.parsed.name}")

          # Get final parsed result
          final = await stream.get_final_completion()
          person = final.choices[0].message.parsed
          print(f"\nFinal: {person.name}, {person.age}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

### Input + Instructions Pattern

Dedalus extends OpenAI's API to support both `messages` (Chat Completions) and `input`+`instructions` (Responses) patterns:

<CodeGroup>
  ```python Input Pattern theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int

  async def main():
      client = AsyncDedalus()

      # Dedalus extension: input + instructions
      completion = await client.chat.completions.parse(
          input="Profile for Carol, 35, designer",
  				model="openai/gpt-4o-mini",
          instructions="Output only structured data.",
          response_format=PersonInfo,
      )

      person = completion.choices[0].message.parsed
      print(f"{person.name}, {person.age}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

### Optional Fields

Use `Optional[T]` for nullable fields:

<CodeGroup>
  ```python Optional Fields theme={null}
  import asyncio

  from typing import Optional

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PartialInfo(BaseModel):
      name: str
      # You can also use `<type> | None = None` notation (Python 3.10+)
      age: Optional[int] = None
      occupation: Optional[str] = None

  async def main():
      client = AsyncDedalus()

      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Just name: Dave"}],
          response_format=PartialInfo,
      )

      person = completion.choices[0].message.parsed
      print(f"Name: {person.name}")
      print(f"Age: {person.age or 'unknown'}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

## Streaming Helpers

Dedalus provides unified `stream_async()` and `stream_sync()` helpers that work with **both** streaming APIs:

<CodeGroup>
  ```python Unified Helper theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dedalus_labs.utils.stream import stream_async
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int


  async def main():
      client = AsyncDedalus()

      # Works with .stream() (Pydantic models)
      stream = client.chat.completions.stream(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Profile for Alice, 28"}],
          response_format=PersonInfo,
      )
      await stream_async(stream)  # Auto-detects context manager

      # Also works with .create(stream=True) (dict-based)
      stream = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Count to 10"}],
          stream=True,
      )
      await stream_async(stream)  # Auto-detects raw chunks

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

**Helper Auto-Detection:**

* Detects `ChatCompletionStreamManager` (from `.stream()`) → uses event API
* Detects raw `StreamChunk` iterator (from `.create(stream=True)`) → uses chunk API
* Single unified interface - no need to choose which helper to use

## DedalusRunner API

The Runner supports `response_format` with automatic Pydantic conversion:

<CodeGroup>
  ```python Runner with Structured Outputs theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class WeatherResponse(BaseModel):
      location: str
      temperature: int
      summary: str


  async def get_weather(location: str) -> str:
      """Get weather for a location."""
      return f"Sunny, 72°F in {location}"


  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="What's the weather in Paris?",
          model="openai/gpt-4o-mini",
          tools=[get_weather],
          response_format=WeatherResponse,  # Pydantic model
          max_steps=5,
      )

      print(result.final_output)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Note>
  The Runner auto-converts Pydantic models to dict schemas. For tool-only workflows without structured final output, omit `response_format`.
</Note>

### Tools + Structured Outputs with Client API

For more control, use the client's `.parse()` method with `tools` parameter.

<Note>
  Tools must have `"strict": true` and `"additionalProperties": false` when used with `.parse()`. This ensures both the response and tool calls are validated.
</Note>

<CodeGroup>
  ```python Tools + Structured Outputs theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class WeatherInfo(BaseModel):
      location: str
      temperature: int
      conditions: str


  async def main():
      client = AsyncDedalus()

      # Define strict tool schemas (required for .parse())
      tools = [
          {
              "type": "function",
              "function": {
                  "name": "get_weather",
                  "description": "Get weather for a location",
                  "parameters": {
                      "type": "object",
                      "properties": {
                          "location": {"type": "string"}
                      },
                      "required": ["location"],
                      "additionalProperties": False,
                  },
                  "strict": True,
              }
          }
      ]

      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "What's the weather in Paris?"}],
          tools=tools,
          response_format=WeatherInfo,
      )

      # Check if tool was called or structured response returned
      message = completion.choices[0].message
      if message.tool_calls:
          print(f"Tool called: {message.tool_calls[0].function.name}")
      elif message.parsed:
          print(f"Weather: {message.parsed.location}, {message.parsed.temperature}°C")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

## .create() vs .parse() vs .stream()

| Method      | Pydantic Support | Streaming | Use Case                |
| ----------- | ---------------- | --------- | ----------------------- |
| `.create()` | ❌ Dict only      | ✓         | Manual JSON schemas     |
| `.parse()`  | ✓ Direct         | ❌         | Type-safe non-streaming |
| `.stream()` | ✓ Direct         | ✓         | Type-safe streaming     |

<Note>
  `.create()` will throw a `TypeError` if you pass a Pydantic model:

  ```
  TypeError: You tried to pass a `BaseModel` class to `chat.completions.create()`;
  You must use `chat.completions.parse()` instead
  ```
</Note>

## Advanced: Nested Models

<CodeGroup>
  ```python Nested Structures theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class Skill(BaseModel):
      name: str
      years_experience: int


  class DetailedProfile(BaseModel):
      name: str
      age: int
      skills: list[Skill]


  async def main():
      client = AsyncDedalus()

      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{
              "role": "user",
              "content": "Profile for expert developer Alice, 28, with 5 years Python and 3 years Rust"
          }],
          response_format=DetailedProfile,
      )

      profile = completion.choices[0].message.parsed
      print(f"{profile.name}: {len(profile.skills)} skills")
      for skill in profile.skills:
          print(f"  - {skill.name}: {skill.years_experience}y")
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

## Error Handling

<CodeGroup>
  ```python Refusals theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int


  async def main():
      client = AsyncDedalus()

      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Generate harmful content"}],
          response_format=PersonInfo,
      )

      message = completion.choices[0].message
      if message.refusal:
          print(f"Model refused: {message.refusal}")
      elif message.parsed:
          print(f"Parsed: {message.parsed.name}")
      else:
          print("No response or parsing failed")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

## Advanced Patterns

### Messages + Instructions Override

<CodeGroup>
  ```python Override System Message theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class PersonInfo(BaseModel):
      name: str
      age: int


  async def main():
      client = AsyncDedalus()

      # Instructions override system message in messages list
      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[
              {"role": "system", "content": "This gets replaced"},
              {"role": "user", "content": "Profile for Eve, 29"}
          ],
          instructions="Be concise.",  # Overrides system message
          response_format=PersonInfo,
      )

      person = completion.choices[0].message.parsed
      print(f"{person.name}, {person.age}")
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

### Using Dict Response Format

For cases where you can't use Pydantic models, use dict-based schemas:

<CodeGroup>
  ```python Dict Schema theme={null}
  import asyncio
  import json

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()


  async def main():
      client = AsyncDedalus()

      # Manual JSON schema
      response_format = {
          "type": "json_schema",
          "json_schema": {
              "name": "person",
              "strict": True,
              "schema": {
                  "type": "object",
                  "properties": {
                      "name": {"type": "string"},
                      "age": {"type": "integer"}
                  },
                  "required": ["name", "age"],
                  "additionalProperties": False
              }
          }
      }

      # Works with .create() and streaming
      completion = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Profile for Frank, 31"}],
          response_format=response_format,
      )

      data = json.loads(completion.choices[0].message.content)
      print(f"{data['name']}, {data['age']}")
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

### MCP Servers Flexibility

The `mcp_servers` parameter accepts both single strings and lists:

<CodeGroup>
  ```python Flexible MCP Servers theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class Info(BaseModel):
      result: str


  async def main():
      client = AsyncDedalus()

      # Single string
      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "What time is it?"}],
          mcp_servers="time",  # Single server
          response_format=Info,
      )

      # List of servers
      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[{"role": "user", "content": "Check my notes"}],
          mcp_servers=["time", "memory"],  # Multiple servers
          response_format=Info,
      )
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

## Supported Models

The SDK's `.parse()` and `.stream()` methods work across all providers. Schema enforcement varies by provider:

**Strict Enforcement** (CFG-based, schema guarantees):

* ✓ `openai/*` - Context-free grammar compilation
* ✓ `xai/*` - Native schema validation
* ✓ `fireworks_ai/*` - Native schema validation (select models)
* ✓ `deepseek/*` - Native schema validation (select models)

**Best-Effort** (schema sent for guidance, no guarantees):

* 🟡 `google/*` - Schema forwarded to `generationConfig.responseSchema`. Typically conforms but not guaranteed.
* 🟡 `anthropic/*` - Prompt-based JSON generation. \~85-90% success rate.

<Warning>
  For `google/*` and `anthropic/*` models, always validate parsed output and implement retry logic. The SDK uses schemas for validation but cannot enforce adherence.
</Warning>

<Note>
  **HTTP API Limitation:** The `response_format` parameter in raw HTTP requests only works with OpenAI/xAI/Fireworks/DeepSeek. Use the SDK's `.parse()` method for cross-provider support.
</Note>

## Quick Reference

### All Streaming Methods Compared

| Method                 | Syntax                                                      | Pydantic    | Events          | Use When           |
| ---------------------- | ----------------------------------------------------------- | ----------- | --------------- | ------------------ |
| `.create(stream=True)` | `await client.chat.completions.create(stream=True, ...)`    | ❌ Dict only | Raw chunks      | Legacy/simple      |
| `.stream()`            | `async with client.chat.completions.stream(...) as stream:` | ✓           | Granular events | Pydantic models    |
| `stream_async()`       | `await stream_async(stream)`                                | ✓ Both      | Auto-detect     | Convenience helper |

### Helper Functions

```python  theme={null}
from dedalus_labs.lib.utils.stream import stream_async, stream_sync

# Async
await stream_async(stream)  # Works with .stream() or .create(stream=True)

# Sync
stream_sync(stream)  # Works with .stream() or .create(stream=True)
```

The helpers auto-detect the stream type and use the appropriate API.

## OpenAI Responses API Translation

Dedalus uses the Chat Completions API standard. The following table maps OpenAI Responses API parameters to their Chat Completions equivalents:

| OpenAI Responses API       | Dedalus Chat Completions API            | Notes                   |
| -------------------------- | --------------------------------------- | ----------------------- |
| `client.responses.parse()` | `client.chat.completions.parse()`       | Different resource path |
| `input=[...]`              | `messages=[...]`                        | Parameter name differs  |
| `text_format=Model`        | `response_format=Model`                 | Parameter name differs  |
| `response.output_parsed`   | `completion.choices[0].message.parsed`  | Different access path   |
| `response.output_text`     | `completion.choices[0].message.content` | Different access path   |
| `response.status`          | `completion.choices[0].finish_reason`   | Different field         |

### Example Translation

<CodeGroup>
  ```python OpenAI Responses API (not supported) theme={null}
  from openai import OpenAI
  from pydantic import BaseModel

  client = OpenAI()

  class CalendarEvent(BaseModel):
      name: str
      date: str
      participants: list[str]

  # This will NOT work with Dedalus
  response = client.responses.parse(
      model="gpt-4o-2024-08-06",
      input=[
          {"role": "system", "content": "Extract the event information."},
          {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
      ],
      text_format=CalendarEvent,
  )

  event = response.output_parsed
  ```

  ```python Dedalus Chat Completions API (supported) theme={null}
  import asyncio

  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv
  from pydantic import BaseModel

  load_dotenv()


  class CalendarEvent(BaseModel):
      name: str
      date: str
      participants: list[str]


  async def main():
      client = AsyncDedalus()

      # Use this instead
      completion = await client.chat.completions.parse(
          model="openai/gpt-4o-mini",
          messages=[
              {"role": "system", "content": "Extract the event information."},
              {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
          ],
          response_format=CalendarEvent,
      )

      event = completion.choices[0].message.parsed
      print(f"Event: {event.name} on {event.date}")
      print(f"Participants: {', '.join(event.participants)}")


  if __name__ == "__main__":
      asyncio.run(main())
  ```
</CodeGroup>

<Info>
  The Responses API requires additional infrastructure beyond what Chat Completions provides. Chat Completions has broader ecosystem support and backward compatibility with existing codebases.
</Info>

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

# Tool Chaining

> Advanced tool chaining workflow with async execution

This example demonstrates advanced tool chaining where multiple tools are executed in sequence, with the Runner handling complex multi-step workflows automatically.

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

  def celsius_to_fahrenheit(celsius: float) -> float:
      """Convert temperature from Celsius to Fahrenheit."""
      return (celsius * 9/5) + 32

  def get_clothing_recommendation(temp_f: float) -> str:
      """Recommend clothing based on temperature in Fahrenheit."""
      if temp_f < 32:
          return "Heavy winter coat, gloves, hat, and warm boots"
      elif temp_f < 50:
          return "Warm jacket or coat, long pants, closed shoes"
      elif temp_f < 65:
          return "Light jacket or sweater, long pants"
      elif temp_f < 80:
          return "T-shirt or light shirt, comfortable pants or shorts"
      else:
          return "Lightweight clothing, shorts, sandals, and sun protection"

  def plan_activity(temp_f: float, clothing: str) -> str:
      """Suggest outdoor activities based on temperature and clothing."""
      if temp_f < 32:
          return f"Great weather for skiing, ice skating, or cozy indoor activities. Dress in: {clothing}"
      elif temp_f < 50:
          return f"Perfect for hiking, jogging, or outdoor photography. Dress in: {clothing}"
      elif temp_f < 80:
          return f"Ideal for picnics, outdoor sports, or walking in the park. Dress in: {clothing}"
      else:
          return f"Excellent for swimming, beach activities, or water sports. Dress in: {clothing}"

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="It's 22 degrees Celsius today in Paris. Convert this to Fahrenheit, recommend what I should wear, suggest outdoor activities, and search for current weather conditions in Paris to confirm.",
          model=["openai/gpt-5"],
          tools=[celsius_to_fahrenheit, get_clothing_recommendation, plan_activity],
          mcp_servers=["joerup/open-meteo-mcp", "windsor/brave-search-mcp"],
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

# Image Generation & Vision

> Generate, edit, and analyze images with AI models

This example demonstrates comprehensive image workflows including generation, editing, variations, vision analysis, and orchestration using DedalusRunner.

<Tip>
  For image generation, use `openai/dall-e-3` for best quality. For vision tasks, `openai/gpt-4o-mini` provides excellent performance at lower cost.
</Tip>

## Image Generation

Generate images from text prompts using DALL-E models.

<CodeGroup>
  ```python Generate Image theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()

  async def generate_image():
      """Generate image from text."""
      client = AsyncDedalus()
      response = await client.images.generate(
          prompt="Dedalus flying through clouds",
          model="openai/dall-e-3",
      )
      print(response.data[0].url)

  if __name__ == "__main__":
      asyncio.run(generate_image())
  ```
</CodeGroup>

## Image Editing

Edit existing images by providing a source image, mask, and prompt describing desired changes.

<CodeGroup>
  ```python Edit Image theme={null}
  import asyncio
  import httpx
  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()

  async def edit_image():
      """Edit image (using generated image as both source and mask)."""

      client = AsyncDedalus()

      # Generate a test image (DALL·E output is valid RGBA PNG)
      gen_response = await client.images.generate(
          prompt="A white cat on a cushion",
          model="openai/dall-e-2",
          size="512x512",
      )

      # Download generated image
      async with httpx.AsyncClient() as http:
          img_data = await http.get(gen_response.data[0].url)
          img_bytes = img_data.content

      # Use same image as both source and mask (just testing endpoint works)
      response = await client.images.edit(
          image=img_bytes,
          mask=img_bytes,
          prompt="A white cat with sunglasses",
          model="openai/dall-e-2",
      )
      print(response.data[0].url)

  if __name__ == "__main__":
      asyncio.run(edit_image())
  ```
</CodeGroup>

## Image Variations

Create variations of an existing image.

<CodeGroup>
  ```python Create Variations theme={null}
  import asyncio
  from pathlib import Path
  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()

  async def create_variations():
      """Create image variations."""
      client = AsyncDedalus()

      image_path = Path("image.png")
      if not image_path.exists():
          print("Skipped: image.png not found")
          return

      response = await client.images.create_variation(
          image=image_path.read_bytes(),
          model="openai/dall-e-2",
          n=2,
      )
      for img in response.data:
          print(img.url)

  if __name__ == "__main__":
      asyncio.run(create_variations())
  ```
</CodeGroup>

## Vision: Analyze Images from URL

Use vision models to analyze and describe images from URLs.

<CodeGroup>
  ```python Vision with URL theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()

  async def vision_url():
      """Analyze image from URL."""
      client = AsyncDedalus()
      completion = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[
              {
                  "role": "user",
                  "content": [
                      {"type": "text", "text": "What's in this image?"},
                      {
                          "type": "image_url",
                          "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"},
                      },
                  ],
              }
          ],
      )
      print(completion.choices[0].message.content)

  if __name__ == "__main__":
      asyncio.run(vision_url())
  ```
</CodeGroup>

## Vision: Analyze Local Images with Base64

Analyze local images by encoding them as base64.

<CodeGroup>
  ```python Vision with Base64 theme={null}
  import asyncio
  import base64
  from pathlib import Path
  from dedalus_labs import AsyncDedalus
  from dotenv import load_dotenv

  load_dotenv()

  async def vision_base64():
      """Analyze local image via base64."""
      client = AsyncDedalus()

      image_path = Path("image.png")
      if not image_path.exists():
          print("Skipped: image.png not found")
          return

      b64 = base64.b64encode(image_path.read_bytes()).decode()
      completion = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[
              {
                  "role": "user",
                  "content": [
                      {"type": "text", "text": "Describe this image."},
                      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                  ],
              }
          ],
      )
      print(completion.choices[0].message.content)

  if __name__ == "__main__":
      asyncio.run(vision_base64())
  ```
</CodeGroup>

## Advanced: Image Orchestration with DedalusRunner

Create complex image workflows by combining generation, editing, and vision capabilities using DedalusRunner.

<CodeGroup>
  ```python DedalusRunner Image Workflow theme={null}
  import asyncio
  import httpx
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv

  load_dotenv()

  class ImageToolSuite:
      """Helper that exposes image endpoints as DedalusRunner tools."""

      def __init__(self, client: AsyncDedalus):
          self._client = client

      async def generate_concept_art(
          self,
          prompt: str,
          model: str = "openai/dall-e-3",
          size: str = "1024x1024",
      ) -> str:
          """Create concept art and return the hosted image URL."""
          response = await self._client.images.generate(
              prompt=prompt,
              model=model,
              size=size,
          )
          return response.data[0].url

      async def edit_concept_art(
          self,
          prompt: str,
          reference_url: str,
          mask_url: str | None = None,
          model: str = "openai/dall-e-2",
      ) -> str:
          """Apply edits to the referenced image URL and return a new URL."""

          if not reference_url:
              raise ValueError("reference_url must be provided when editing an image.")

          async with httpx.AsyncClient() as http:
              base_image = await http.get(reference_url)
              mask_bytes = await http.get(mask_url) if mask_url else None

          edit_kwargs = {
              "image": base_image.content,
              "prompt": prompt,
              "model": model,
          }
          if mask_bytes:
              edit_kwargs["mask"] = mask_bytes.content

          response = await self._client.images.edit(**edit_kwargs)
          return response.data[0].url

      async def describe_image(
          self,
          image_url: str,
          question: str = "Describe this image.",
          model: str = "openai/gpt-4o-mini",
      ) -> str:
          """Run a lightweight vision pass against an existing image URL."""
          completion = await self._client.chat.completions.create(
              model=model,
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": question},
                          {"type": "image_url", "image_url": {"url": image_url}},
                      ],
                  }
              ],
          )
          return completion.choices[0].message.content

  async def runner_storyboard():
      """Demonstrate DedalusRunner + agent-as-tool pattern for image workflows."""

      client = AsyncDedalus()
      runner = DedalusRunner(client, verbose=True)
      image_tools = ImageToolSuite(client)

      instructions = (
          "You are a creative director. Use the provided tools to generate concept art, "
          "optionally refine it, and then describe the final render. Always keep the "
          "main conversation on a text model and rely on the tools for image work."
      )

      result = await runner.run(
          instructions=instructions,
          input="Create a retro Dedalus mission patch, refine it with a neon palette, and describe it.",
          model="openai/gpt-4o-mini",
          tools=[
              image_tools.generate_concept_art,
              image_tools.edit_concept_art,
              image_tools.describe_image,
          ],
          max_steps=4,
          verbose=True,
          debug=False,
      )

      print("Runner final output:", result.final_output)
      print("Tools invoked:", result.tools_called)

  if __name__ == "__main__":
      asyncio.run(runner_storyboard())
  ```
</CodeGroup>

## Complete Example

Here's a complete script that demonstrates all image capabilities:

<CodeGroup>
  ```python Complete Example theme={null}
  """Image generation, edits, and DedalusRunner orchestration examples."""

  import asyncio
  import base64
  from pathlib import Path

  import httpx
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv

  load_dotenv()


  async def generate_image():
      """Generate image from text."""
      client = AsyncDedalus()
      response = await client.images.generate(
          prompt="Dedalus flying through clouds",
          model="openai/dall-e-3",
      )
      print(response.data[0].url)


  async def edit_image():
      """Edit image (using generated image as both source and mask)."""

      client = AsyncDedalus()

      # Generate a test image (DALL·E output is valid RGBA PNG)
      gen_response = await client.images.generate(
          prompt="A white cat on a cushion",
          model="openai/dall-e-2",
          size="512x512",
      )

      # Download generated image
      async with httpx.AsyncClient() as http:
          img_data = await http.get(gen_response.data[0].url)
          img_bytes = img_data.content

      # Use same image as both source and mask (just testing endpoint works)
      response = await client.images.edit(
          image=img_bytes,
          mask=img_bytes,
          prompt="A white cat with sunglasses",
          model="openai/dall-e-2",
      )
      print(response.data[0].url)


  async def create_variations():
      """Create image variations."""
      client = AsyncDedalus()

      image_path = Path("image.png")
      if not image_path.exists():
          print("Skipped: image.png not found")
          return

      response = await client.images.create_variation(
          image=image_path.read_bytes(),
          model="openai/dall-e-2",
          n=2,
      )
      for img in response.data:
          print(img.url)


  async def vision_url():
      """Analyze image from URL."""
      client = AsyncDedalus()
      completion = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[
              {
                  "role": "user",
                  "content": [
                      {"type": "text", "text": "What's in this image?"},
                      {
                          "type": "image_url",
                          "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"},
                      },
                  ],
              }
          ],
      )
      print(completion.choices[0].message.content)


  async def vision_base64():
      """Analyze local image via base64."""
      client = AsyncDedalus()

      image_path = Path("image.png")
      if not image_path.exists():
          print("Skipped: image.png not found")
          return

      b64 = base64.b64encode(image_path.read_bytes()).decode()
      completion = await client.chat.completions.create(
          model="openai/gpt-4o-mini",
          messages=[
              {
                  "role": "user",
                  "content": [
                      {"type": "text", "text": "Describe this image."},
                      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                  ],
              }
          ],
      )
      print(completion.choices[0].message.content)


  class ImageToolSuite:
      """Helper that exposes image endpoints as DedalusRunner tools."""

      def __init__(self, client: AsyncDedalus):
          self._client = client

      async def generate_concept_art(
          self,
          prompt: str,
          model: str = "openai/dall-e-3",
          size: str = "1024x1024",
      ) -> str:
          """Create concept art and return the hosted image URL."""
          response = await self._client.images.generate(
              prompt=prompt,
              model=model,
              size=size,
          )
          return response.data[0].url

      async def edit_concept_art(
          self,
          prompt: str,
          reference_url: str,
          mask_url: str | None = None,
          model: str = "openai/dall-e-2",
      ) -> str:
          """Apply edits to the referenced image URL and return a new URL."""

          if not reference_url:
              raise ValueError("reference_url must be provided when editing an image.")

          async with httpx.AsyncClient() as http:
              base_image = await http.get(reference_url)
              mask_bytes = await http.get(mask_url) if mask_url else None

          edit_kwargs = {
              "image": base_image.content,
              "prompt": prompt,
              "model": model,
          }
          if mask_bytes:
              edit_kwargs["mask"] = mask_bytes.content

          response = await self._client.images.edit(**edit_kwargs)
          return response.data[0].url

      async def describe_image(
          self,
          image_url: str,
          question: str = "Describe this image.",
          model: str = "openai/gpt-4o-mini",
      ) -> str:
          """Run a lightweight vision pass against an existing image URL."""
          completion = await self._client.chat.completions.create(
              model=model,
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": question},
                          {"type": "image_url", "image_url": {"url": image_url}},
                      ],
                  }
              ],
          )
          return completion.choices[0].message.content


  async def runner_storyboard():
      """Demonstrate DedalusRunner + agent-as-tool pattern for image workflows."""

      client = AsyncDedalus()
      runner = DedalusRunner(client, verbose=True)
      image_tools = ImageToolSuite(client)

      instructions = (
          "You are a creative director. Use the provided tools to generate concept art, "
          "optionally refine it, and then describe the final render. Always keep the "
          "main conversation on a text model and rely on the tools for image work."
      )

      result = await runner.run(
          instructions=instructions,
          input="Create a retro Dedalus mission patch, refine it with a neon palette, and describe it.",
          model="openai/gpt-4o-mini",
          tools=[
              image_tools.generate_concept_art,
              image_tools.edit_concept_art,
              image_tools.describe_image,
          ],
          max_steps=4,
          verbose=True,
          debug=False,
      )

      print("Runner final output:", result.final_output)
      print("Tools invoked:", result.tools_called)


  async def main() -> None:
      await generate_image()
      await edit_image()
      await create_variations()
      await vision_url()
      await vision_base64()
      await runner_storyboard()


  if __name__ == "__main__":
      asyncio.run(main())
  ```
</CodeGroup>


