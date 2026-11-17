import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EditorTabs } from './EditorTabs';
import type { OpenFile } from '../../store/uiStore';

describe('EditorTabs', () => {
  const mockFiles: OpenFile[] = [
    {
      path: 'src/main.py',
      name: 'main.py',
      language: 'python',
      content: 'print(1)',
      originalContent: 'print(1)',
      isDirty: false,
      isGenerated: true,
    },
    {
      path: 'package.json',
      name: 'package.json',
      language: 'json',
      content: '{"modified": true}',
      originalContent: '{}',
      isDirty: true,
      isGenerated: false,
    },
  ];

  it('renders nothing when file list is empty', () => {
    const { container } = render(
      <EditorTabs
        files={[]}
        activeFilePath={null}
        onSelectTab={vi.fn()}
        onCloseTab={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders tabs with file names and active styling', () => {
    render(
      <EditorTabs
        files={mockFiles}
        activeFilePath="src/main.py"
        onSelectTab={vi.fn()}
        onCloseTab={vi.fn()}
      />
    );

    expect(screen.getByText('main.py')).toBeInTheDocument();
    expect(screen.getByText('package.json')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('triggers onSelectTab when clicking a tab', () => {
    const onSelectTab = vi.fn();
    render(
      <EditorTabs
        files={mockFiles}
        activeFilePath="src/main.py"
        onSelectTab={onSelectTab}
        onCloseTab={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('package.json'));
    expect(onSelectTab).toHaveBeenCalledWith('package.json');
  });

  it('triggers onCloseTab when clicking tab close button', () => {
    const onCloseTab = vi.fn();
    render(
      <EditorTabs
        files={mockFiles}
        activeFilePath="src/main.py"
        onSelectTab={vi.fn()}
        onCloseTab={onCloseTab}
      />
    );

    const closeBtn = screen.getByTitle('Close main.py');
    fireEvent.click(closeBtn);
    expect(onCloseTab).toHaveBeenCalledWith('src/main.py');
  });
});
