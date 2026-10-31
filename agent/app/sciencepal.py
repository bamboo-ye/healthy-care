"""SciencePal Agent HTTP adapter, following https://sciencepal.ai/help/sdk.

This invokes an Agent, not an OpenAI-compatible model endpoint. Credentials
never enter prompts, persisted graph state, or returned client errors.
"""
import json
import os
from uuid import UUID
import httpx
from .contracts import ProviderError

class SciencePalClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str | None = None, api_key: str | None = None):
        self.client = client
        self.base_url = (base_url or os.getenv('SCIENCEPAL_BASE_URL', 'https://sciencepal.ai/api')).rstrip('/')
        self.api_key = api_key if api_key is not None else os.getenv('SCIENCEPAL_API_KEY', '')

    @property
    def headers(self):
        if not self.api_key: raise ProviderError('sciencepal_not_configured')
        return {'Authorization': f'Bearer {self.api_key}'}

    async def initiate(self, agent_id: str, prompt: str, files: list[tuple[str, bytes]] | None = None) -> dict:
        if not agent_id: raise ProviderError('sciencepal_not_configured')
        uploads = [('files', (name, content, 'application/octet-stream')) for name, content in files or []]
        response = await self.client.post(f'{self.base_url}/agent/initiate', headers=self.headers, data={'agent_id': agent_id, 'prompt': prompt, 'stream': 'true', 'agent_select_type': 'manual'}, files=uploads or None)
        response.raise_for_status()
        result = response.json()
        if not result.get('thread_id') or not result.get('agent_run_id'): raise ProviderError('sciencepal_invalid_response')
        return result

    async def status(self, run_id: str) -> dict:
        self._identifier(run_id)
        response = await self.client.get(f'{self.base_url}/agent-run/{run_id}', headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def stream(self, run_id: str):
        self._identifier(run_id)
        async with self.client.stream('GET', f'{self.base_url}/agent-run/{run_id}/stream', headers=self.headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith('data:'): continue
                payload = line[5:].strip()
                if payload == '[DONE]': break
                if payload: yield json.loads(payload)

    async def add_message(self, thread_id: str, message_id: str, content: str) -> dict:
        self._identifier(thread_id); UUID(message_id)
        response = await self.client.post(f'{self.base_url}/thread/{thread_id}/messages', headers=self.headers, json={'message_id': message_id, 'content': content})
        response.raise_for_status()
        return response.json()

    async def start(self, thread_id: str) -> dict:
        self._identifier(thread_id)
        response = await self.client.post(f'{self.base_url}/thread/{thread_id}/agent/start', headers=self.headers, json={})
        response.raise_for_status()
        return response.json()

    async def stop(self, run_id: str) -> dict:
        self._identifier(run_id)
        response = await self.client.post(f'{self.base_url}/agent-run/{run_id}/stop', headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def download_file(self, thread_id: str, file_path: str, max_bytes: int = 1_000_000) -> bytes:
        self._identifier(thread_id)
        response = await self.client.get(f'{self.base_url}/thread/{thread_id}/sandbox', headers=self.headers)
        response.raise_for_status()
        sandbox_id = response.json()['sandbox_id']
        self._identifier(sandbox_id)
        chunks = []; total = 0
        async with self.client.stream('GET', f'{self.base_url}/sandboxes/{sandbox_id}/files/content', headers=self.headers, params={'path': file_path}) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > max_bytes: raise ProviderError('sciencepal_artifact_too_large')
                chunks.append(chunk)
        return b''.join(chunks)

    @staticmethod
    def _identifier(value: str):
        if not value or len(value) > 200 or any(v not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for v in value):
            raise ValueError('Invalid remote resource identifier')
