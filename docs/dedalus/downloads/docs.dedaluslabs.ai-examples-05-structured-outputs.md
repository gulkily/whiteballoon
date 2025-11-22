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
