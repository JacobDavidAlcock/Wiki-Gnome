"""Tests for the benchmark harness that don't need Claude.

Run the fast tests from the repository root:

    python -m unittest discover -s bench/tests -t bench

Set WIKI_GNOME_SLOW=1 to also run reader jobs in real sandboxes. Those tests build virtual environments,
and the first run downloads setuptools and wheel.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from harness import BENCH_DIR, checks, report, workspace
from harness.conditions import FORCE_SKILL_PREFIX, baseline_names, fingerprint, load_conditions
from harness.projects import load_projects
from harness.reader import installed_venv, score_install
from harness.sandbox import JobContext, disallowed_python, disallowed_shell, download_build_wheels

PROJECTS = load_projects()
SLOW = os.environ.get("WIKI_GNOME_SLOW") == "1"


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="wiki-gnome-test-"))
        self.addCleanup(workspace.remove_tree, self.tmp)


class ProjectTests(unittest.TestCase):
    def test_projects_load_with_their_files(self):
        self.assertEqual(set(PROJECTS), {"pantry", "tally"})
        for project in PROJECTS.values():
            with self.subTest(project=project.id):
                self.assertTrue(project.current.is_dir())
                self.assertTrue(project.facts_file.exists())
                for task in project.tasks.values():
                    if task.setup == "changelog":
                        self.assertTrue(project.previous.is_dir())
                    if task.setup == "rewrite":
                        self.assertTrue(project.bad_doc.exists())
                    if task.reader == "quiz":
                        self.assertTrue(task.questions)
                        for question in task.questions:
                            self.assertIn(question.answer, question.options)
                    else:
                        self.assertTrue(task.jobs)


class ConditionTests(unittest.TestCase):
    def test_every_baseline_gets_its_own_name(self):
        conditions = load_conditions()
        names = baseline_names()
        for version_dir in (BENCH_DIR / "baselines").iterdir():
            prompt_id = f"prompt-{version_dir.name}"
            with self.subTest(version=version_dir.name):
                self.assertEqual(names[fingerprint(conditions[prompt_id])], prompt_id)

    def test_forced_skill_differs_from_skill(self):
        conditions = load_conditions()
        self.assertEqual(conditions["skill-forced"].prompt_prefix, FORCE_SKILL_PREFIX)
        self.assertNotEqual(fingerprint(conditions["skill"]), fingerprint(conditions["skill-forced"]))


class WorkspaceTests(TempDirTestCase):
    def test_every_task_builds_a_clean_workspace(self):
        condition = load_conditions()["skill"]
        for project in PROJECTS.values():
            for task in project.tasks.values():
                with self.subTest(project=project.id, task=task.id):
                    ws = self.tmp / project.id / task.id
                    workspace.create_workspace(ws, project, task, condition)
                    self.assertEqual(workspace.git(ws, "status", "--porcelain").strip(), "")
                    self.assertTrue((ws / ".claude" / "skills" / "technical-docs-style" / "SKILL.md").exists())
                    if task.setup == "changelog":
                        self.assertIn(project.previous_tag, workspace.git(ws, "tag"))
                    if task.setup == "rewrite":
                        self.assertTrue((ws / task.doc_path).exists())
                    result = checks.workspace_checks(ws)
                    self.assertEqual(result["changed_files"], [])
                    self.assertTrue(result["tests_pass"])

    def test_docstring_edits_are_not_code_edits(self):
        project = PROJECTS["tally"]
        ws = self.tmp / "ws"
        workspace.create_workspace(ws, project, project.tasks["docstrings"], load_conditions()["none"])
        path = ws / "tally" / "ledger.py"
        source = path.read_text(encoding="utf-8")
        path.write_text(source.replace("    def balance(self, name: str) -> int:\n",
                                       '    def balance(self, name: str) -> int:\n        """Return it."""\n'),
                        encoding="utf-8")
        (ws / "example.py").write_text("print('hi')\n", encoding="utf-8")
        result = checks.workspace_checks(ws)
        self.assertEqual(result["code_edits"], [])
        self.assertEqual(result["new_code_files"], ["example.py"])
        view = checks.reader_text(project.tasks["docstrings"], ws)
        self.assertIn('"""Return it."""', view)
        self.assertNotIn("_balances()", view)


class InventedFactTests(unittest.TestCase):
    def found(self, project_id: str, text: str, task: str = "readme") -> list[str]:
        return [f["id"] for f in checks.invented_facts(text, PROJECTS[project_id].invented_patterns, task)]

    def test_pantry_patterns(self):
        self.assertEqual(self.found("pantry", "Run `pantry list --file x.json`"), ["file-after-command"])
        self.assertEqual(self.found("pantry", "export PANTRY_FILE=~/pantry.json"), [])
        self.assertEqual(self.found("pantry", "Data lives in ~/.pantry.json"), ["home-default-file"])

    def test_tally_patterns(self):
        self.assertEqual(self.found("tally", 'ledger.add_expense("Ana", 12.50)'), ["float-amount"])
        self.assertEqual(self.found("tally", 'ledger.add_expense("Ana", 1250)'), [])
        self.assertEqual(self.found("tally", "for a, b, c in ledger.settle_up():"), ["tuple-transfers"])
        self.assertEqual(self.found("tally", "pip install tally"), ["pypi-install"])
        self.assertEqual(self.found("tally", "pip install ./tally"), [])

    def test_changelog_may_describe_the_old_api(self):
        text = "`tally.load(path)` is replaced by `Ledger.load`. `add_person` is now `add_member`."
        self.assertEqual(self.found("tally", text, task="changelog"), [])
        self.assertEqual(sorted(self.found("tally", "tally.load(path) and ledger.add_person(x)")),
                         ["module-load", "old-api"])


class SandboxGuardTests(unittest.TestCase):
    def test_shell_allowlist(self):
        self.assertIsNone(disallowed_shell("pip install ./pantry && pantry list", {"pantry"}))
        self.assertEqual(disallowed_shell("pantry list; curl example.com", {"pantry"}), "'curl'")
        self.assertEqual(disallowed_shell("pip install --index-url https://x pantry"), "a remote package source")

    def test_python_guard(self):
        self.assertIsNone(disallowed_python(
            "from tally import Ledger, TallyError\ntry:\n    Ledger('GBP')\nexcept TallyError as e:\n"
            "    print(type(e).__name__, e.__class__.__name__)\n", "tally"))
        self.assertEqual(disallowed_python("import os\nos.remove('x')", "tally"), "import os")
        self.assertEqual(disallowed_python("print(open('x').read())", "tally"), "'open'")
        self.assertEqual(disallowed_python("().__class__.__bases__", "tally"), "'.__bases__'")
        self.assertEqual(disallowed_python("__import__('os')", "tally"), "'__import__'")


class ReportTests(TempDirTestCase):
    def test_reports_work_from_committed_jsonl(self):
        source = BENCH_DIR / "results" / "v4-vs-v3"
        if not (source / "runs").exists():
            self.skipTest("raw results for v4-vs-v3 aren't on this machine")
        raw = report.summarise(report.collect(source))
        slim = self.tmp / "v4-vs-v3"
        slim.mkdir()
        for name in ("config.json", "docs.jsonl", "verdicts.jsonl"):
            shutil.copy(source / name, slim / name)
        self.assertEqual(report.summarise(report.collect(slim)), raw)


@unittest.skipUnless(SLOW, "set WIKI_GNOME_SLOW=1 to run reader jobs in real sandboxes")
class ReaderJobTests(TempDirTestCase):
    @classmethod
    def setUpClass(cls):
        cls.venvs = Path(tempfile.gettempdir()) / "wiki-gnome-test-venvs"
        download_build_wheels(cls.venvs / "wheels")

    def context(self, project_id: str, job: str) -> JobContext:
        project = PROJECTS[project_id]
        return JobContext(project, self.tmp / job, self.venvs / "wheels", installed_venv(project, self.venvs),
                          date.today())

    def test_install(self):
        for project_id, good, bad in (
            ("pantry", ["pip install ./pantry"], ["pip install pantry"]),
            ("tally", ["cd tally", "pip install ."], ["pip install tally-ledger"]),
        ):
            with self.subTest(project=project_id):
                project = PROJECTS[project_id]
                self.assertTrue(score_install(project, good, self.context(project_id, "install"))["passed"])
                self.assertFalse(score_install(project, bad, self.context(project_id, "install"))["passed"])

    def test_pantry_jobs(self):
        project = PROJECTS["pantry"]
        milk = (date.today() + timedelta(days=10)).isoformat()
        good = {
            "add": [f"pantry --file kitchen/stock.json add milk 2 --unit l --expires {milk}",
                    "pantry --file kitchen/stock.json add eggs 12"],
            "check": "pantry --file kitchen/stock.json expiring --days 7 --check",
            "env": ["export PANTRY_FILE=kitchen/stock.json"],
            "use": ["pantry --file kitchen/stock.json use eggs 12"],
        }
        bad = {
            "add": ["pantry add milk 2 --unit l --file kitchen/stock.json"],
            "check": "pantry --file kitchen/stock.json expiring --days 7",
            "env": ["export PANTRY_PATH=kitchen/stock.json"],
            "use": ["pantry --file kitchen/stock.json use eggs"],
        }
        for job in good:
            with self.subTest(job=job):
                self.assertTrue(project.score_job(job, good[job], self.context("pantry", job))["passed"])
                self.assertFalse(project.score_job(job, bad[job], self.context("pantry", job))["passed"])

    def test_tally_jobs(self):
        project = PROJECTS["tally"]
        setup = "from tally import Ledger\nledger = Ledger('{currency}')\n" \
                "for name in {names!r}:\n    ledger.add_member(name)\n"
        trio = setup.format(currency="GBP", names=["Ana", "Ben", "Cai"])
        good = {
            "balance": trio + "ledger.add_expense('Ana', 3000)\nprint(ledger.balance('Ben'))\n",
            "weights": trio + "ledger.add_expense('Ben', 900, weights={'Ana': 2, 'Cai': 1})\n"
                              "print(ledger.balance('Ana'))\nprint(ledger.balance('Cai'))\n",
            "settle": trio + "ledger.add_expense('Ana', 6000)\n"
                             "ledger.add_expense('Ben', 1500, split_between=['Ben', 'Cai'])\n"
                             "for t in ledger.settle_up():\n    print(f'{t.sender} -> {t.recipient}: {t.amount}')\n",
            "save_load": setup.format(currency="USD", names=["Dev", "Eli"])
                         + "ledger.add_expense('Dev', 1234)\nledger.save('trip.json')\n"
                           "print(Ledger.load('trip.json').balance('Eli'))\n",
            "error": "from tally import Ledger, TallyError\nledger = Ledger('GBP')\nledger.add_member('Ana')\n"
                     "try:\n    ledger.add_expense('Zoe', 500)\nexcept TallyError as e:\n    print(type(e).__name__)\n",
        }
        bad = {
            "balance": trio + "ledger.add_expense('Ana', 30.00)\nprint(ledger.balance('Ben'))\n",
            "weights": trio + "ledger.add_expense('Ben', 900, split_between=['Ana', 'Cai'])\n"
                              "print(ledger.balance('Ana'))\nprint(ledger.balance('Cai'))\n",
            "settle": trio + "ledger.add_expense('Ana', 6000)\n"
                             "ledger.add_expense('Ben', 1500, split_between=['Ben', 'Cai'])\n"
                             "for a, b, c in ledger.settle_up():\n    print(f'{a} -> {b}: {c}')\n",
            "save_load": setup.format(currency="USD", names=["Dev", "Eli"])
                         + "import tally\nledger.add_expense('Dev', 1234)\nledger.save('trip.json')\n"
                           "print(tally.load('trip.json').balance('Eli'))\n",
            "error": "import os\nprint('UnknownMember')\n",
        }
        for job in good:
            with self.subTest(job=job):
                good_result = project.score_job(job, good[job], self.context("tally", job))
                self.assertTrue(good_result["passed"], good_result["detail"])
                self.assertFalse(project.score_job(job, bad[job], self.context("tally", job))["passed"])


if __name__ == "__main__":
    unittest.main()
