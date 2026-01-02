from __future__ import annotations

import argparse
from pathlib import Path
import re

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    tomllib = None


HEADER = [
    "# Requirements for WhiteBalloon",
    "# Generated from pyproject.toml dependencies",
    "# Do not edit manually; run ./wb generate-requirements",
    "# Install with: pip install -r requirements.txt",
    "",
]


def load_dependencies(pyproject_path: Path) -> list[str]:
    if tomllib is not None:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", [])
        if not isinstance(deps, list) or not all(isinstance(item, str) for item in deps):
            raise ValueError("Invalid project.dependencies in pyproject.toml")
        return deps
    return _parse_dependencies_block(pyproject_path.read_text(encoding="utf-8"))


def _parse_dependencies_block(content: str) -> list[str]:
    in_project = False
    in_dependencies = False
    buffer: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            in_dependencies = False
            continue
        if not in_project:
            continue
        if not in_dependencies:
            if stripped.startswith("dependencies"):
                bracket_index = stripped.find("[")
                if bracket_index == -1:
                    continue
                after = stripped[bracket_index + 1 :]
                if "]" in after:
                    buffer.append(after.split("]", 1)[0])
                    break
                buffer.append(after)
                in_dependencies = True
            continue
        if "]" in stripped:
            buffer.append(stripped.split("]", 1)[0])
            break
        buffer.append(stripped)

    if not buffer:
        raise ValueError("Unable to locate project.dependencies in pyproject.toml")

    combined = "\n".join(_strip_toml_comment(line) for line in buffer)
    deps = [match.group(2) for match in re.finditer(r'(["\'])(.*?)\1', combined)]
    if not deps:
        raise ValueError("No dependencies found in project.dependencies")
    return deps


def _strip_toml_comment(line: str) -> str:
    in_string = False
    quote = ""
    for idx, char in enumerate(line):
        if char in {"'", '"'}:
            if not in_string:
                in_string = True
                quote = char
            elif quote == char:
                in_string = False
        if char == "#" and not in_string:
            return line[:idx]
    return line


def render_requirements(deps: list[str]) -> str:
    lines = HEADER + deps
    return "\n".join(lines).rstrip() + "\n"


def write_requirements(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate requirements.txt from pyproject.toml")
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "pyproject.toml",
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "requirements.txt",
        help="Path to write requirements.txt",
    )
    args = parser.parse_args()

    deps = load_dependencies(args.pyproject)
    content = render_requirements(deps)
    write_requirements(args.output, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
