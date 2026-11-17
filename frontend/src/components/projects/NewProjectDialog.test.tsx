import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NewProjectDialog } from './NewProjectDialog';

describe('NewProjectDialog', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <NewProjectDialog
        isOpen={false}
        isLoading={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders modal form when open', () => {
    render(
      <NewProjectDialog
        isOpen={true}
        isLoading={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Create New Project')).toBeInTheDocument();
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it('submits form with entered name and description', () => {
    const onSubmit = vi.fn();
    render(
      <NewProjectDialog
        isOpen={true}
        isLoading={false}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    );

    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: 'Inventory System' },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Manages warehouse items' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Project' }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'Inventory System',
      description: 'Manages warehouse items',
    });
  });

  it('displays error message when provided', () => {
    render(
      <NewProjectDialog
        isOpen={true}
        isLoading={false}
        error="Project name already exists."
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByText('Project name already exists.')).toBeInTheDocument();
  });
});
