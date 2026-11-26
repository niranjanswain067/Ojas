import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProjectCard } from './ProjectCard';
import * as projectApi from '../../api/projects';
import type { Project } from '../../api/types';

const mockProject: Project = {
  id: 'proj-123',
  name: 'Library System',
  description: 'Book catalog and members',
  status: 'done',
  document_count: 2,
  requirement_count: 8,
  test_case_count: 5,
  test_count: 5,
  bug_count: 1,
  run_count: 3,
  created_at: '2026-11-01T10:00:00',
  updated_at: '2026-11-02T12:00:00',
};

describe('ProjectCard', () => {
  it('renders project metadata, status, and stats', () => {
    render(
      <MemoryRouter>
        <ProjectCard project={mockProject} onDelete={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText('Library System')).toBeInTheDocument();
    expect(screen.getByText('Book catalog and members')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Docs
    expect(screen.getByText('8')).toBeInTheDocument(); // Reqs
    expect(screen.getByText('5')).toBeInTheDocument(); // Tests
    expect(screen.getByText('1')).toBeInTheDocument(); // Bugs
  });

  it('triggers onDelete callback when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(
      <MemoryRouter>
        <ProjectCard project={mockProject} onDelete={onDelete} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /delete library system/i }));
    expect(onDelete).toHaveBeenCalledWith(mockProject);
  });

  it('triggers download when download button is clicked', async () => {
    const downloadSpy = vi
      .spyOn(projectApi, 'downloadProjectZip')
      .mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter>
        <ProjectCard project={mockProject} onDelete={vi.fn()} />
      </MemoryRouter>
    );

    const downloadBtn = screen.getByRole('button', {
      name: /download library system/i,
    });
    expect(downloadBtn).toBeInTheDocument();

    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(downloadSpy).toHaveBeenCalledWith('proj-123', 'Library System');
    });

    downloadSpy.mockRestore();
  });
});
