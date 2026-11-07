import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusChip } from './StatusChip';

describe('StatusChip Component', () => {
  it('renders healthy status with default Ready label', () => {
    render(<StatusChip status="healthy" />);
    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  it('renders degraded status with default Degraded label', () => {
    render(<StatusChip status="degraded" />);
    expect(screen.getByText('Degraded')).toBeInTheDocument();
  });

  it('renders offline status with Offline label', () => {
    render(<StatusChip status="offline" />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('renders custom label and tooltip', () => {
    render(
      <StatusChip
        status="running"
        label="Generating code..."
        tooltip="Generating ast-checked code"
      />
    );
    const chip = screen.getByText('Generating code...');
    expect(chip).toBeInTheDocument();
    expect(chip.closest('span')?.parentElement).toHaveAttribute(
      'title',
      'Generating ast-checked code'
    );
  });
});

