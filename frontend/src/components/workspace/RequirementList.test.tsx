import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RequirementList } from "./RequirementList";
import type { RequirementChunk } from "../../api/documents";

const mockReqs: RequirementChunk[] = [
  {
    id: "chunk-1",
    document_id: "doc-1",
    project_id: "proj-1",
    req_id: "REQ-001",
    chunk_type: "requirement",
    heading: "User Authentication",
    content: "The system shall authenticate users with passwords.",
    token_count: 25,
    chunk_index: 1,
    created_at: "2026-11-20T10:00:00Z",
  },
  {
    id: "chunk-2",
    document_id: "doc-1",
    project_id: "proj-1",
    req_id: "REQ-002",
    chunk_type: "requirement",
    heading: "Data Export",
    content: "The system shall export data to CSV and JSON formats.",
    token_count: 30,
    chunk_index: 2,
    created_at: "2026-11-20T10:05:00Z",
  },
];

describe("RequirementList", () => {
  it("renders requirements list with REQ-IDs and headings", () => {
    render(<RequirementList requirements={mockReqs} />);

    expect(screen.getByText("REQ-001")).toBeInTheDocument();
    expect(screen.getByText("User Authentication")).toBeInTheDocument();
    expect(screen.getByText("REQ-002")).toBeInTheDocument();
    expect(screen.getByText("Data Export")).toBeInTheDocument();
  });

  it("filters requirements by search input", () => {
    render(<RequirementList requirements={mockReqs} />);

    const searchInput = screen.getByPlaceholderText(/search requirements/i);
    fireEvent.change(searchInput, { target: { value: "CSV" } });

    expect(screen.queryByText("REQ-001")).not.toBeInTheDocument();
    expect(screen.getByText("REQ-002")).toBeInTheDocument();
  });

  it("expands and collapses requirement content on click", () => {
    render(<RequirementList requirements={mockReqs} />);

    // Content is initially not visible
    expect(
      screen.queryByText("The system shall authenticate users with passwords.")
    ).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByText("User Authentication"));

    expect(
      screen.getByText("The system shall authenticate users with passwords.")
    ).toBeInTheDocument();

    // Click again to collapse
    fireEvent.click(screen.getByText("User Authentication"));

    expect(
      screen.queryByText("The system shall authenticate users with passwords.")
    ).not.toBeInTheDocument();
  });

  it("expands all and collapses all with control buttons", () => {
    render(<RequirementList requirements={mockReqs} />);

    fireEvent.click(screen.getByRole("button", { name: /expand all/i }));

    expect(
      screen.getByText("The system shall authenticate users with passwords.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("The system shall export data to CSV and JSON formats.")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /collapse all/i }));

    expect(
      screen.queryByText("The system shall authenticate users with passwords.")
    ).not.toBeInTheDocument();
  });

  it("shows empty state when no requirements match", () => {
    render(<RequirementList requirements={[]} />);
    expect(screen.getByText(/no requirements found/i)).toBeInTheDocument();
  });
});
