import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CoverageTable } from './CoverageTable';
import type { TraceabilityCoverageItem } from '../../api/reports';

const mockItems: TraceabilityCoverageItem[] = [
  {
    req_id: 'REQ-001',
    heading: 'User Authentication',
    description: 'Allow users to login and logout safely.',
    code_symbols: [
      {
        file_path: 'auth.py',
        symbol_name: 'login_user',
        start_line: 10,
        end_line: 25,
      },
    ],
    test_cases: [
      { id: '1', tc_id: 'TC-001', name: 'test_login_success', status: 'passed' },
      { id: '2', tc_id: 'TC-002', name: 'test_invalid_password', status: 'passed' },
    ],
    results: [
      { tc_id: 'TC-001', result: 'passed' },
      { tc_id: 'TC-002', result: 'passed' },
    ],
    bugs: [],
    status: 'passing',
  },
  {
    req_id: 'REQ-002',
    heading: 'Password Reset',
    description: 'Send recovery emails to users.',
    code_symbols: [],
    test_cases: [
      { id: '3', tc_id: 'TC-003', name: 'test_reset_token', status: 'failed' },
    ],
    results: [{ tc_id: 'TC-003', result: 'failed' }],
    bugs: [
      {
        bug_id: 'B-001',
        title: 'Token expiry mismatch',
        severity: 'high',
        status: 'open',
      },
    ],
    status: 'failing',
  },
];

describe('CoverageTable Component', () => {
  it('renders all requirement items and status badges', () => {
    render(<CoverageTable items={mockItems} />);

    expect(screen.getByText('REQ-001')).toBeInTheDocument();
    expect(screen.getByText('User Authentication')).toBeInTheDocument();
    expect(screen.getByText('login_user')).toBeInTheDocument();
    expect(screen.getByText('Passing')).toBeInTheDocument();

    expect(screen.getByText('REQ-002')).toBeInTheDocument();
    expect(screen.getByText('Password Reset')).toBeInTheDocument();
    expect(screen.getByText('Failing')).toBeInTheDocument();
    expect(screen.getByText('B-001')).toBeInTheDocument();
  });

  it('filters by status button', () => {
    render(<CoverageTable items={mockItems} />);

    const failingBtn = screen.getByRole('button', { name: /failing \(1\)/i });
    fireEvent.click(failingBtn);

    expect(screen.queryByText('REQ-001')).not.toBeInTheDocument();
    expect(screen.getByText('REQ-002')).toBeInTheDocument();
  });

  it('filters by search input', () => {
    render(<CoverageTable items={mockItems} />);

    const searchInput = screen.getByPlaceholderText(/filter requirements/i);
    fireEvent.change(searchInput, { target: { value: 'Authentication' } });

    expect(screen.getByText('REQ-001')).toBeInTheDocument();
    expect(screen.queryByText('REQ-002')).not.toBeInTheDocument();
  });
});
