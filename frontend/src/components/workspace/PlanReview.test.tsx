import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlanReview } from './PlanReview';

describe('PlanReview', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <PlanReview
        isOpen={false}
        planText='{"files": []}'
        onApprove={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders modal with plan text when isOpen is true', () => {
    render(
      <PlanReview
        isOpen={true}
        planText='{"project_name": "TestProject"}'
        onApprove={vi.fn()}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Review Development Plan')).toBeInTheDocument();
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toBe('{"project_name": "TestProject"}');
  });

  it('allows editing plan text and approves with proceed=true', () => {
    const handleApprove = vi.fn().mockResolvedValue(undefined);
    render(
      <PlanReview
        isOpen={true}
        planText='{"project_name": "TestProject"}'
        onApprove={handleApprove}
        onClose={vi.fn()}
      />
    );

    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: '{"project_name": "Updated"}' } });

    const approveButton = screen.getByText('Approve & Generate Code');
    fireEvent.click(approveButton);

    expect(handleApprove).toHaveBeenCalledWith('{"project_name": "Updated"}', true);
  });

  it('triggers onApprove with proceed=false when Save Plan Only is clicked', () => {
    const handleApprove = vi.fn().mockResolvedValue(undefined);
    render(
      <PlanReview
        isOpen={true}
        planText='{"project_name": "TestProject"}'
        onApprove={handleApprove}
        onClose={vi.fn()}
      />
    );

    const saveOnlyButton = screen.getByText('Save Plan Only');
    fireEvent.click(saveOnlyButton);

    expect(handleApprove).toHaveBeenCalledWith('{"project_name": "TestProject"}', false);
  });

  it('calls onClose when Cancel or Close is clicked', () => {
    const handleClose = vi.fn();
    render(
      <PlanReview
        isOpen={true}
        planText='{"project_name": "TestProject"}'
        onApprove={vi.fn()}
        onClose={handleClose}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
