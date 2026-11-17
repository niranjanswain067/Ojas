import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileTree } from './FileTree';
import type { FileNode } from '../../api/types';

describe('FileTree', () => {
  const mockTree: FileNode[] = [
    {
      name: 'src',
      path: 'src',
      type: 'directory',
      size_bytes: 0,
      is_generated: false,
      pending_approval: false,
      children: [
        {
          name: 'app.py',
          path: 'src/app.py',
          type: 'file',
          size_bytes: 120,
          is_generated: true,
          pending_approval: false,
        },
      ],
    },
    {
      name: 'README.md',
      path: 'README.md',
      type: 'file',
      size_bytes: 45,
      is_generated: false,
      pending_approval: false,
    },
  ];

  it('renders explorer header and file items', () => {
    render(
      <FileTree
        tree={mockTree}
        onSelectFile={vi.fn()}
      />
    );

    expect(screen.getByText(/explorer/i)).toBeInTheDocument();
    expect(screen.getByText('src')).toBeInTheDocument();
    expect(screen.getByText('app.py')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('triggers onSelectFile when clicking a file', () => {
    const onSelectFile = vi.fn();
    render(
      <FileTree
        tree={mockTree}
        onSelectFile={onSelectFile}
      />
    );

    fireEvent.click(screen.getByText('README.md'));
    expect(onSelectFile).toHaveBeenCalledWith(
      expect.objectContaining({ path: 'README.md', name: 'README.md' })
    );
  });

  it('toggles folder collapse and expansion', () => {
    render(
      <FileTree
        tree={mockTree}
        onSelectFile={vi.fn()}
      />
    );

    // Initial state: src is expanded, app.py is visible
    expect(screen.getByText('app.py')).toBeInTheDocument();

    // Click src folder to collapse
    fireEvent.click(screen.getByText('src'));
    expect(screen.queryByText('app.py')).not.toBeInTheDocument();

    // Click again to re-expand
    fireEvent.click(screen.getByText('src'));
    expect(screen.getByText('app.py')).toBeInTheDocument();
  });
});
