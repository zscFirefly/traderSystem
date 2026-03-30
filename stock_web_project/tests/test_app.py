import unittest

from stock_web_app import create_app


try:
    import flask  # noqa: F401
    FLASK_AVAILABLE = True
except ModuleNotFoundError:
    FLASK_AVAILABLE = False


@unittest.skipUnless(FLASK_AVAILABLE, "Flask is not installed in the current environment")
class CreateAppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "DEBUG": False,
                "DATA_FILE": "/tmp/nonexistent.xlsx",
            }
        )
        self.client = self.app.test_client()

    def test_index_route_returns_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)

    def test_search_stocks_without_analyzer_returns_empty_list(self):
        response = self.client.get("/api/search_stocks?query=测试")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main()
