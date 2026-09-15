"""Runs headless Claude Code sessions (`claude -p`) on the signed-in subscription."""

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

CLAUDE = shutil.which("claude")

# Text that means the plan's usage limit was hit, so the whole benchmark should pause.
LIMIT_PATTERN = re.compile(r"usage limit|limit reached|rate.?limit|out of (extra )?usage|\b429\b", re.IGNORECASE)


class UsageLimitReached(RuntimeError):
    pass


@dataclass
class Session:
    ok: bool
    result: str
    error: str | None
    num_turns: int
    duration_ms: int
    cost_usd: float
    skills_available: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)

    def skill_loaded(self, name: str) -> bool:
        return any(
            call["name"] == "Skill" and name in json.dumps(call["input"])
            for call in self.tool_calls
        )

    def to_json(self) -> dict:
        return {
            "ok": self.ok,
            "error": self.error,
            "num_turns": self.num_turns,
            "duration_ms": self.duration_ms,
            "cost_usd_estimate": self.cost_usd,
            "skills_available": self.skills_available,
            "tool_calls": [call["name"] for call in self.tool_calls],
            "denied_tools": self.denied_tools,
        }


def run_claude(
    prompt: str,
    *,
    cwd: Path,
    model: str,
    transcript: Path,
    tools: list[str],
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    append_system_prompt: str | None = None,
    timeout: int = 1200,
) -> Session:
    if CLAUDE is None:
        raise RuntimeError("The claude command isn't on PATH. Install Claude Code and sign in first.")

    cmd = [
        CLAUDE, "-p",
        "--model", model,
        "--setting-sources", "project",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "dontAsk",
        "--tools", ",".join(tools),
    ]
    if allowed_tools:
        cmd += ["--allowedTools", ",".join(allowed_tools)]
    if disallowed_tools:
        cmd += ["--disallowedTools", ",".join(disallowed_tools)]
    if append_system_prompt:
        cmd += ["--append-system-prompt", append_system_prompt]

    env = os.environ.copy()
    # Without an API key, Claude Code falls back to the signed-in subscription.
    env.pop("ANTHROPIC_API_KEY", None)

    transcript.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            cmd, input=prompt, cwd=cwd, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = f"timed out after {timeout}s"
    finally:
        _remove_empty_project_dir(cwd)

    transcript.write_text(stdout, encoding="utf-8")
    session = _parse_stream(stdout)
    if session is None:
        session = Session(False, "", stderr.strip()[-2000:] or "no result event", 0, 0, 0.0)
    if not session.ok and LIMIT_PATTERN.search(f"{session.error} {session.result} {stderr}"):
        raise UsageLimitReached(session.error or session.result or stderr)
    return session


def _parse_stream(stdout: str) -> Session | None:
    skills, calls, denied, result_event = [], [], [], None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            skills = event.get("skills", [])
        elif kind == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    calls.append({"name": block.get("name"), "input": block.get("input", {})})
        elif kind == "user":
            content = event.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                text = json.dumps(block.get("content", ""))
                if block.get("is_error") and "permission" in text.lower():
                    denied.append(text[:200])
        elif kind == "result":
            result_event = event

    if result_event is None:
        return None
    ok = not result_event.get("is_error") and result_event.get("subtype") == "success"
    return Session(
        ok=ok,
        result=result_event.get("result") or "",
        error=None if ok else (result_event.get("result") or result_event.get("subtype")),
        num_turns=result_event.get("num_turns", 0),
        duration_ms=result_event.get("duration_ms", 0),
        cost_usd=result_event.get("total_cost_usd", 0.0),
        skills_available=skills,
        tool_calls=calls,
        denied_tools=denied,
    )


def _remove_empty_project_dir(cwd: Path) -> None:
    """Claude Code creates ~/.claude/projects/<mangled cwd>; remove it when the session left nothing in it."""
    project_dir = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    if not project_dir.is_dir():
        return
    if any(path.is_file() for path in project_dir.rglob("*")):
        return
    shutil.rmtree(project_dir, ignore_errors=True)


def parse_json_answer(text: str) -> dict | None:
    """Pull the first JSON object out of a model reply, with or without a code fence."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    start = text.find("{")
    if start != -1:
        candidates.append(text[start:text.rfind("}") + 1])
    for candidate in candidates:
        # Models sometimes write shell-style \' inside JSON strings, which isn't valid JSON.
        for text_variant in (candidate, candidate.replace("'\\''", "'").replace("\\'", "'")):
            try:
                return json.loads(text_variant)
            except json.JSONDecodeError:
                continue
    return None
