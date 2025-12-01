## Development Scripts

- `no-pytest.sh` – simple guardrail invoked via local alias to block running `pytest` during this planning-focused phase. Have your shell source it like:

  ```bash
  alias pytest="$(pwd)/scripts/no-pytest.sh"
  ```

  That way any accidental `pytest` call prints a reminder instead of executing automated tests.
