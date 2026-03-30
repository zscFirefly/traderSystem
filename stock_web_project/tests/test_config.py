import unittest

from stock_web_app.config import Config


class ConfigTests(unittest.TestCase):
    def test_default_sheet_name_is_present(self):
        self.assertEqual(Config.DATA_SHEET, "股票维度")

    def test_default_port_is_int(self):
        self.assertIsInstance(Config.PORT, int)


if __name__ == "__main__":
    unittest.main()
