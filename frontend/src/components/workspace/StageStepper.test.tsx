import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StageStepper, STAGES } from './StageStepper';

describe('StageStepper', () => {
  it('renders all pipeline stages', () => {
    render(<StageStepper currentStageIndex={0} isRunActive={false} />);

    expect(screen.getByText('Pipeline Stages')).toBeInTheDocument();
    STAGES.forEach((stage) => {
      expect(screen.getByText(stage)).toBeInTheDocument();
    });
  });

  it('shows In Progress badge when run is active', () => {
    const { rerender } = render(<StageStepper currentStageIndex={2} isRunActive={false} />);
    expect(screen.queryByText('In Progress')).toBeNull();

    rerender(<StageStepper currentStageIndex={2} isRunActive={true} />);
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('marks stages correctly based on currentStageIndex', () => {
    const { container } = render(<StageStepper currentStageIndex={3} isRunActive={true} />);

    // Stage 3 (Check) is current
    expect(screen.getByText('Check')).toBeInTheDocument();

    // Check completed indicators (Check lucide icons)
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThanOrEqual(3);
  });
});
