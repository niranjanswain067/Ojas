import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getFileTree, getFileContent, saveFile, deleteFile } from './files';

describe('Files API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getFileTree requests /api/projects/:id/files', async () => {
    const mockTree = {
      tree: [
        {
          name: 'main.py',
          path: 'main.py',
          type: 'file',
          size_bytes: 120,
          is_generated: true,
          pending_approval: false,
        },
      ],
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockTree,
    } as Response);

    const result = await getFileTree('proj-123');
    expect(result).toEqual(mockTree);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/proj-123/files',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getFileContent requests /api/projects/:id/files/:path', async () => {
    const mockContent = {
      path: 'src/app.py',
      content: 'print("hello")',
      size_bytes: 14,
      language: 'python',
      is_generated: false,
      pending_approval: false,
      linked_req_ids: [],
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockContent,
    } as Response);

    const result = await getFileContent('proj-123', 'src/app.py');
    expect(result).toEqual(mockContent);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/proj-123/files/src/app.py',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('saveFile sends PUT request with content payload', async () => {
    const mockSave = {
      path: 'src/app.py',
      size_bytes: 25,
      updated_at: '2026-11-17T15:00:00',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockSave,
    } as Response);

    const result = await saveFile('proj-123', 'src/app.py', 'print("updated")');
    expect(result).toEqual(mockSave);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/proj-123/files/src/app.py',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ content: 'print("updated")' }),
      })
    );
  });

  it('deleteFile sends DELETE request', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 204,
      headers: new Headers(),
    } as Response);

    await deleteFile('proj-123', 'src/app.py');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/proj-123/files/src/app.py',
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});
