import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Folder } from 'lucide-react';
import { EmptyState } from './EmptyState';

describe('EmptyState Component', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        icon={Folder}
        title="No items found"
        description="Try adjusting your filter or create a new item."
      />
    );
    expect(screen.getByText('No items found')).toBeInTheDocument();
    expect(
      screen.getByText('Try adjusting your filter or create a new item.')
    ).toBeInTheDocument();
  });

  it('triggers action callback when action button is clicked', () => {
    const handleClick = vi.fn();
    render(
      <EmptyState
        title="Empty Projects"
        action={{
          label: 'Create Project',
          onClick: handleClick,
        }}
      />
    );

    const button = screen.getByRole('button', { name: /create project/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

