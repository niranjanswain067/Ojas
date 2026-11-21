import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EscalationBanner } from './EscalationBanner';

describe('EscalationBanner', () => {
  it('renders nothing when stopReason is null or unrecognized', () => {
    const { container: c1 } = render(
      <EscalationBanner stopReason={null} />
    );
    expect(c1.firstChild).toBeNull();

    const { container: c2 } = render(
      <EscalationBanner stopReason="all_passed" />
    );
    expect(c2.firstChild).toBeNull();
  });

  it('renders repeated failure warning when stopReason is repeated_failure', () => {
    const handleViewBugs = vi.fn();
    const handleDismiss = vi.fn();

    render(
      <EscalationBanner
        stopReason="repeated_failure"
        onViewBugs={handleViewBugs}
        onDismiss={handleDismiss}
      />
    );

    expect(screen.getByText('Fix Loop Stopped: Repeated Failure')).toBeInTheDocument();
    expect(screen.getByText(/same test failure repeated across consecutive fix iterations/i)).toBeInTheDocument();

    const viewButton = screen.getByText('View diagnosed bug reports');
    fireEvent.click(viewButton);
    expect(handleViewBugs).toHaveBeenCalledTimes(1);

    const dismissButton = screen.getByRole('button', { name: '' });
    fireEvent.click(dismissButton);
    expect(handleDismiss).toHaveBeenCalledTimes(1);
  });

  it('renders iteration limit warning when stopReason is iteration_limit', () => {
    render(
      <EscalationBanner stopReason="iteration_limit" />
    );

    expect(screen.getByText('Fix Loop Stopped: Iteration Limit')).toBeInTheDocument();
    expect(screen.getByText(/reached its maximum iteration limit without resolving all failing test cases/i)).toBeInTheDocument();
  });
});
