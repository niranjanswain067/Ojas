import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelOutput } from './ModelOutput';

describe('ModelOutput Component', () => {
  it('renders placeholder when no output exists', () => {
    render(<ModelOutput output="" />);
    expect(screen.getByText(/no model output yet/i)).toBeInTheDocument();
    expect(screen.getByText(/raw tokens will stream here/i)).toBeInTheDocument();
  });

  it('renders streamed output text and character count', () => {
    render(<ModelOutput output="def calculate(a, b): return a + b" />);
    expect(screen.getByText(/def calculate\(a, b\): return a \+ b/)).toBeInTheDocument();
    expect(screen.getByText(/33 characters/i)).toBeInTheDocument();
  });

  it('triggers onClear callback when Clear button is clicked', () => {
    const handleClear = vi.fn();
    render(<ModelOutput output="Sample code" onClear={handleClear} />);

    const clearBtn = screen.getByRole('button', { name: /clear/i });
    expect(clearBtn).not.toBeDisabled();
    fireEvent.click(clearBtn);
    expect(handleClear).toHaveBeenCalledTimes(1);
  });

  it('toggles auto-scroll button state', () => {
    render(<ModelOutput output="Some output" />);
    const scrollBtn = screen.getByRole('button', { name: /auto-scroll on/i });
    expect(scrollBtn).toBeInTheDocument();

    fireEvent.click(scrollBtn);
    expect(screen.getByRole('button', { name: /auto-scroll off/i })).toBeInTheDocument();
  });
});
