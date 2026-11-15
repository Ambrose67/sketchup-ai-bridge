import importlib.util
import json
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path


class FakeMCP:
    def __init__(self, *args, **kwargs):
        pass

    def tool(self):
        return lambda function: function


try:
    import mcp.server.fastmcp
except ImportError:
    sys.modules.setdefault('mcp', types.ModuleType('mcp'))
    sys.modules.setdefault('mcp.server', types.ModuleType('mcp.server'))
    fast = types.ModuleType('mcp.server.fastmcp')
    fast.FastMCP = FakeMCP
    sys.modules['mcp.server.fastmcp'] = fast
spec = importlib.util.spec_from_file_location('bridge_server', Path(__file__).resolve().parents[1] / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class BridgeTest(unittest.TestCase):
    def test_request_response_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            server.bridge = Path(folder)
            def simulate_sketchup():
                requests = server.bridge / 'requests'
                while not list(requests.glob('*.json')):
                    time.sleep(.01)
                request_file = next(requests.glob('*.json'))
                data = json.loads(request_file.read_text())
                self.assertEqual(data['command'], 'model_info')
                request_file.unlink()
                (server.bridge / 'responses' / request_file.name).write_text(json.dumps({'ok': True, 'result': {'title': 'Test'}}))
            worker = threading.Thread(target=simulate_sketchup)
            worker.start()
            self.assertEqual(server.model_info(), {'title': 'Test'})
            worker.join()

    def test_invalid_dimensions_rejected_before_request(self):
        for value in (0, -1, float('nan'), float('inf'), 1000001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                server.create_box(value, 100, 100)

    def test_timeout_removes_pending_request(self):
        with tempfile.TemporaryDirectory() as folder:
            server.bridge = Path(folder)
            with self.assertRaises(TimeoutError):
                server.request('model_info', timeout=0.1)
            self.assertEqual(list((server.bridge / 'requests').glob('*.json')), [])


if __name__ == '__main__':
    unittest.main()
