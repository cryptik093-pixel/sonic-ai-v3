import asyncio
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / 'server.py'
spec = importlib.util.spec_from_file_location('sonic_server', SERVER)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class Records(unittest.TestCase):
    def test_success_and_repeat(self):
        first = server.sonic_get_state()
        second = server.sonic_get_state()
        self.assertEqual(first['status'], 'succeeded')
        self.assertEqual(first['result'], second['result'])
        self.assertNotEqual(first['execution_id'], second['execution_id'])
        self.assertEqual(first['evidence'], second['evidence'])

    def test_missing_corrupt_and_unsupported(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(server, 'ROOT', Path(directory)):
            self.assertEqual(server.sonic_get_state()['error']['code'], 'DEPENDENCY_UNAVAILABLE')
            p = Path(directory) / server.FILES['state']
            p.parent.mkdir(parents=True)
            for content in ['{bad', '[]', '{"schema_version":"999"}']:
                p.write_text(content)
                self.assertEqual(server.sonic_get_state()['error']['code'], 'INVALID_RECORD')

    def test_symlink_denied(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(server, 'ROOT', Path(directory)):
            p = Path(directory) / server.FILES['state']
            p.parent.mkdir(parents=True)
            target = Path(directory) / 'private.json'
            target.write_text('{"secret":"never return"}')
            p.symlink_to(target)
            result = server.sonic_get_state()
            self.assertEqual(result['error']['code'], 'AUTHORIZATION_DENIED')
            self.assertNotIn('never return', json.dumps(result))

class Protocol(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_session(self):
        async with asyncio.timeout(20):
            params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=10)) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    self.assertEqual({t.name for t in result.tools}, {'sonic_get_state', 'sonic_list_agents'})
                    for tool in result.tools:
                        self.assertTrue(tool.annotations.readOnlyHint)
                        response = await session.call_tool(tool.name, {})
                        self.assertFalse(response.isError)
                        data = json.loads(response.content[0].text)
                        self.assertEqual(data['status'], 'succeeded')
                    denied = await session.call_tool('sonic_execute_shell', {'command':'whoami'})
                    self.assertTrue(denied.isError)

if __name__ == '__main__':
    unittest.main()
