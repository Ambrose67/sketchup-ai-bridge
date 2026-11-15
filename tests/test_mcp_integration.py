"""Exercise the real MCP stdio protocol against a simulated SketchUp peer."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


class RealMCPTest(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_and_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp, USERPROFILE=tmp)
            params = StdioServerParameters(command=os.sys.executable,
                                           args=[str(ROOT / 'server.py')], env=env)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual({t.name for t in tools.tools}, {'model_info', 'list_groups', 'create_box'})

                    async def mock_sketchup():
                        folder = Path(tmp) / '.sketchup-ai-bridge'
                        for _ in range(100):
                            requests = list((folder / 'requests').glob('*.json'))
                            if requests:
                                path = requests[0]
                                request = json.loads(path.read_text())
                                self.assertEqual(request['command'], 'create_box')
                                self.assertEqual(request['arguments']['width_mm'], 1000)
                                path.unlink()
                                (folder / 'responses' / path.name).write_text(json.dumps(
                                    {'ok': True, 'result': {'id': 42, 'units': 'mm'}}))
                                return
                            await asyncio.sleep(.05)
                        raise AssertionError('No request received')

                    mock = asyncio.create_task(mock_sketchup())
                    result = await session.call_tool('create_box', {'width_mm': 1000, 'depth_mm': 500, 'height_mm': 750})
                    await mock
                    self.assertFalse(result.isError, result.content)
                    self.assertEqual(json.loads(result.content[0].text)['id'], 42)


if __name__ == '__main__':
    unittest.main()
