import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IterationStatus } from './IterationStatus';

describe('IterationStatus', () => {
  it('renders nothing when iteration <= 0', () => {
    const { container } = render(
      <IterationStatus iteration={0} iterationLimit={5} failingCount={0} isActive={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders progress and iteration counter when iteration > 0', () => {
    render(
      <IterationStatus iteration={2} iterationLimit={5} failingCount={3} isActive={true} />
    );

    expect(screen.getByText('Fix Loop Progress')).toBeInTheDocument();
    expect(screen.getByText('Iteration 2 of 5')).toBeInTheDocument();
    expect(screen.getByText('3 test(s) failing')).toBeInTheDocument();
    expect(screen.getByText('Max limit: 5')).toBeInTheDocument();
  });

  it('renders all tests passing when failingCount is 0', () => {
    render(
      <IterationStatus iteration={1} iterationLimit={5} failingCount={0} isActive={false} />
    );

    expect(screen.getByText('All tests passing')).toBeInTheDocument();
  });
});
