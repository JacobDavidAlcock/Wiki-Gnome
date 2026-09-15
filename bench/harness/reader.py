"""Reader tests: a fresh session gets only the doc, and its answers are checked for real."""

import json
from datetime import date
from pathlib import Path

from .claude import parse_json_answer, run_claude
from .model import Project, Task
from .sandbox import JobContext, Sandbox, commands_text, disallowed_shell, make_venv
from .workspace import remove_tree

QUIZ_PROMPT = """Answer each question using only the documentation below. If the documentation doesn't answer a question, choose E. Don't use general knowledge or guess.

{questions}

Reply with only a JSON object mapping each question number to a letter, for example {{"1": "A", "2": "E"}}.

<documentation>
{doc}
</documentation>
"""


def run_reader(project: Project, task: Task, doc: str, *, model: str, out_dir: Path, sandbox_root: Path,
               venvs_dir: Path) -> dict:
    sandbox_root.mkdir(parents=True, exist_ok=True)
    try:
        if task.reader == "quiz":
            return _run_quiz(task, doc, model=model, out_dir=out_dir, cwd=sandbox_root)
        return _run_exec(project, task, doc, model=model, out_dir=out_dir, sandbox_root=sandbox_root,
                         venvs_dir=venvs_dir)
    finally:
        # Sandboxes can hold a whole virtual environment each, and every result is already saved.
        remove_tree(sandbox_root)


def _run_exec(project: Project, task: Task, doc: str, *, model: str, out_dir: Path, sandbox_root: Path,
              venvs_dir: Path) -> dict:
    today = date.today()
    prompt = project.exec_prompt.format(doc=doc, **project.exec_prompt_values(today))
    session = run_claude(prompt, cwd=sandbox_root, model=model, transcript=out_dir / "reader-transcript.jsonl", tools=[])
    answer = parse_json_answer(session.result) or {}
    (out_dir / "reader-answer.json").write_text(json.dumps(answer, indent=2), encoding="utf-8")

    wheels = venvs_dir / "wheels"
    context = JobContext(project, sandbox_root / "job", wheels, installed_venv(project, venvs_dir), today)
    steps = {}
    for job in task.jobs:
        context.root = sandbox_root / job
        if job == "install":
            steps[job] = score_install(project, answer.get(job), context)
        else:
            steps[job] = project.score_job(job, answer.get(job), context)
    passed = sum(1 for result in steps.values() if result["passed"])
    return {
        "type": "exec",
        "session": session.to_json(),
        "answer_parsed": bool(answer),
        "steps": steps,
        "passed": passed,
        "total": len(task.jobs),
        "score": passed / len(task.jobs),
    }


def installed_venv(project: Project, venvs_dir: Path) -> Path:
    return make_venv(venvs_dir / f"installed-{project.id}", venvs_dir / "wheels", install=project.current)


def score_install(project: Project, value, context: JobContext) -> dict:
    """Run the reader's install commands in a fresh virtual environment, then check the project works."""
    script = commands_text(value).strip()
    result = {"commands": script, "passed": False, "detail": ""}
    if not script:
        result["detail"] = "no commands given"
        return result
    bad = disallowed_shell(script, project.extra_commands)
    if bad:
        result["detail"] = f"not run: uses {bad}, which the sandbox doesn't allow"
        return result
    sandbox = Sandbox(context.root, project, context.wheels)
    sandbox.venv = make_venv(context.root / ".venv", context.wheels)
    run = sandbox.run_shell(script, timeout=300)
    check = sandbox.run_shell(project.install_check)
    result["passed"] = check.returncode == 0 and project.install_check_output in check.stdout
    result["detail"] = check.stdout.strip() if result["passed"] else (run.stderr or run.stdout)[-500:]
    return result


def _run_quiz(task: Task, doc: str, *, model: str, out_dir: Path, cwd: Path) -> dict:
    lines = []
    for number, question in enumerate(task.questions, start=1):
        lines.append(f"{number}. {question.text}")
        lines += [f"   {letter}. {option}" for letter, option in question.options.items()]
        lines.append("   E. The documentation doesn't say")
    prompt = QUIZ_PROMPT.format(questions="\n".join(lines), doc=doc)
    session = run_claude(prompt, cwd=cwd, model=model, transcript=out_dir / "reader-transcript.jsonl", tools=[])
    answer = parse_json_answer(session.result) or {}
    (out_dir / "reader-answer.json").write_text(json.dumps(answer, indent=2), encoding="utf-8")
    results = {}
    for number, question in enumerate(task.questions, start=1):
        given = str(answer.get(str(number), "")).strip().upper()[:1]
        results[str(number)] = {"given": given, "expected": question.answer, "passed": given == question.answer}
    passed = sum(1 for r in results.values() if r["passed"])
    return {
        "type": "quiz",
        "session": session.to_json(),
        "answer_parsed": bool(answer),
        "questions": results,
        "passed": passed,
        "total": len(task.questions),
        "score": passed / len(task.questions),
        "said_not_documented": sum(1 for r in results.values() if r["given"] == "E"),
    }
