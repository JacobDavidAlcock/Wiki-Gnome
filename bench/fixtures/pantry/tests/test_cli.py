import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from pantry.cli import main


class PantryTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name) / "pantry.json"

    def run_cli(self, *args, file=True):
        argv = (["--file", str(self.file)] if file else []) + list(args)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def days_from_today(self, days):
        return (date.today() + timedelta(days=days)).isoformat()


class AddTests(PantryTestCase):
    def test_add_creates_file(self):
        code, out, _ = self.run_cli("add", "Milk", "2", "--unit", "l")
        self.assertEqual(code, 0)
        self.assertEqual(out, "milk: 2 l\n")
        data = json.loads(self.file.read_text())
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["items"], [{"name": "milk", "quantity": 2, "unit": "l", "expires": None}])

    def test_add_merges_names_case_insensitively(self):
        self.run_cli("add", "Brown  Rice", "1", "--unit", "kg")
        code, out, _ = self.run_cli("add", "brown rice", "2", "--unit", "kg")
        self.assertEqual(code, 0)
        self.assertEqual(out, "brown rice: 3 kg\n")

    def test_add_keeps_earlier_expiry(self):
        self.run_cli("add", "eggs", "6", "--expires", "2030-01-10")
        self.run_cli("add", "eggs", "6", "--expires", "2030-01-20")
        data = json.loads(self.file.read_text())
        self.assertEqual(data["items"][0]["expires"], "2030-01-10")

    def test_add_rejects_unit_mismatch(self):
        self.run_cli("add", "flour", "1", "--unit", "kg")
        code, _, err = self.run_cli("add", "flour", "500", "--unit", "g")
        self.assertEqual(code, 1)
        self.assertIn("flour is stored in 'kg', not 'g'", err)

    def test_add_rejects_bad_date(self):
        code, _, err = self.run_cli("add", "eggs", "6", "--expires", "10/01/2030")
        self.assertEqual(code, 1)
        self.assertIn("use YYYY-MM-DD", err)
        self.assertFalse(self.file.exists())

    def test_add_rejects_zero_quantity(self):
        code, _, _ = self.run_cli("add", "eggs", "0")
        self.assertEqual(code, 2)


class ListTests(PantryTestCase):
    def test_empty(self):
        self.assertEqual(self.run_cli("list")[1], "Pantry is empty.\n")

    def test_list_does_not_create_file(self):
        self.run_cli("list")
        self.assertFalse(self.file.exists())

    def test_sort_by_expiry_puts_undated_last(self):
        self.run_cli("add", "salt", "1")
        self.run_cli("add", "milk", "1", "--expires", "2030-01-02")
        self.run_cli("add", "yoghurt", "1", "--expires", "2030-01-01")
        _, out, _ = self.run_cli("list", "--format", "json", "--sort", "expires")
        self.assertEqual([item["name"] for item in json.loads(out)], ["yoghurt", "milk", "salt"])

    def test_table(self):
        self.run_cli("add", "milk", "2", "--unit", "l", "--expires", "2030-01-02")
        _, out, _ = self.run_cli("list")
        self.assertEqual(out.splitlines()[1].split(), ["milk", "2", "l", "2030-01-02"])

    def test_file_option_must_come_before_command(self):
        code, _, _ = self.run_cli("list", "--file", str(self.file), file=False)
        self.assertEqual(code, 2)


class UseTests(PantryTestCase):
    def test_use_defaults_to_one(self):
        self.run_cli("add", "eggs", "6")
        self.assertEqual(self.run_cli("use", "eggs")[1], "eggs: 5 item left\n")

    def test_use_last_removes_item(self):
        self.run_cli("add", "eggs", "2")
        code, out, _ = self.run_cli("use", "Eggs", "2")
        self.assertEqual(code, 0)
        self.assertEqual(out, "Used the last of eggs; removed it from the pantry.\n")
        self.assertEqual(json.loads(self.file.read_text())["items"], [])

    def test_use_more_than_available(self):
        self.run_cli("add", "eggs", "2")
        code, _, err = self.run_cli("use", "eggs", "3")
        self.assertEqual(code, 1)
        self.assertIn("only 2 item of eggs left", err)

    def test_use_missing_item(self):
        code, _, err = self.run_cli("use", "caviar")
        self.assertEqual(code, 1)
        self.assertIn("no item named 'caviar'", err)


class ExpiringTests(PantryTestCase):
    def test_nothing_expiring(self):
        self.run_cli("add", "rice", "1", "--expires", self.days_from_today(30))
        code, out, _ = self.run_cli("expiring", "--check")
        self.assertEqual(code, 0)
        self.assertEqual(out, "Nothing expires in the next 3 days.\n")

    def test_includes_expired_and_boundary(self):
        self.run_cli("add", "milk", "1", "--expires", self.days_from_today(-2))
        self.run_cli("add", "bread", "1", "--expires", self.days_from_today(0))
        self.run_cli("add", "cheese", "1", "--expires", self.days_from_today(3))
        self.run_cli("add", "rice", "1", "--expires", self.days_from_today(4))
        code, out, _ = self.run_cli("expiring")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "milk (1 item): expired 2 days ago",
            "bread (1 item): expires today",
            "cheese (1 item): expires in 3 days",
        ])

    def test_check_exit_code(self):
        self.run_cli("add", "milk", "1", "--expires", self.days_from_today(1))
        self.assertEqual(self.run_cli("expiring", "--check")[0], 3)

    def test_days_zero(self):
        self.run_cli("add", "milk", "1", "--expires", self.days_from_today(1))
        self.assertEqual(self.run_cli("expiring", "--days", "0")[1], "Nothing expires in the next 0 days.\n")


class FileLocationTests(PantryTestCase):
    def test_env_var_used_without_flag(self):
        env_file = Path(self.tmp.name) / "from-env.json"
        with mock.patch.dict(os.environ, {"PANTRY_FILE": str(env_file)}):
            self.run_cli("add", "tea", "1", file=False)
        self.assertTrue(env_file.exists())

    def test_flag_beats_env_var(self):
        env_file = Path(self.tmp.name) / "from-env.json"
        with mock.patch.dict(os.environ, {"PANTRY_FILE": str(env_file)}):
            self.run_cli("add", "tea", "1")
        self.assertTrue(self.file.exists())
        self.assertFalse(env_file.exists())

    def test_default_is_current_directory(self):
        with mock.patch.dict(os.environ, {}, clear=False) as env:
            env.pop("PANTRY_FILE", None)
            cwd = os.getcwd()
            os.chdir(self.tmp.name)
            try:
                self.run_cli("add", "tea", "1", file=False)
            finally:
                os.chdir(cwd)
        self.assertTrue(self.file.exists())

    def test_unsupported_version(self):
        self.file.write_text('{"version": 2, "items": []}')
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("unsupported format version 2", err)

    def test_invalid_json(self):
        self.file.write_text("not json")
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("is not valid JSON", err)


if __name__ == "__main__":
    unittest.main()
