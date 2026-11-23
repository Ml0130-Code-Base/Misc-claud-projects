import contextlib
import io
import unittest

from metro_maps.__main__ import main


class CliTest(unittest.TestCase):
    def test_help_lists_subcommands(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        for cmd in ("fetch", "diff", "analyze"):
            self.assertIn(cmd, buf.getvalue())


if __name__ == "__main__":
    unittest.main()
