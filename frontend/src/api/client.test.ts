import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiGet, apiPost, apiPut, apiPatch, apiDelete, ApiError } from './client';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('performs apiGet with JSON response', async () => {
    const mockData = { status: 'healthy', version: '0.1.0' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockData,
    } as Response);

    const result = await apiGet('/health');
    expect(result).toEqual(mockData);
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/health', expect.objectContaining({
      method: 'GET',
    }));
  });

  it('performs apiGet with query params', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ success: true }),
    } as Response);

    await apiGet('/projects', { limit: 10, offset: 0 });
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/projects?limit=10&offset=0', expect.any(Object));
  });

  it('performs apiPost with JSON payload', async () => {
    const requestBody = { name: 'Test Project' };
    const responseBody = { id: 'proj-123', name: 'Test Project' };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 201,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => responseBody,
    } as Response);

    const result = await apiPost('/projects', requestBody);
    expect(result).toEqual(responseBody);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(requestBody),
      })
    );
  });

  it('performs apiPut and apiPatch', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ updated: true }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ patched: true }),
      } as Response);

    const putRes = await apiPut('/settings', { temperature: 0.5 });
    expect(putRes).toEqual({ updated: true });

    const patchRes = await apiPatch('/projects/1', { name: 'New' });
    expect(patchRes).toEqual({ patched: true });
  });

  it('performs apiDelete and handles 204 No Content', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 204,
      headers: new Headers(),
    } as Response);

    const result = await apiDelete('/projects/123');
    expect(result).toEqual({});
  });

  it('throws ApiError on non-2xx status code', async () => {
    const errorBody = {
      status_code: 404,
      detail: 'Project not found',
      timestamp: '2026-11-07T12:00:00Z',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => errorBody,
    } as Response);

    await expect(apiGet('/projects/999')).rejects.toThrow(ApiError);
  });
});

