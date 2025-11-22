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
