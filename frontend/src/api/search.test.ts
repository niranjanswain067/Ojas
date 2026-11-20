import { describe, it, expect, vi, beforeEach } from "vitest";
import { searchRequirements } from "./search";

describe("searchRequirements API client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls search endpoint with correct query parameters", async () => {
    const mockResponse = {
      query: "authentication",
      total_results: 1,
      results: [
        {
          chunk_id: "c-1",
          req_id: "REQ-AUTH-01",
          heading: "Authentication",
          content: "Users must log in with email and password.",
          score: 0.032,
          source: "both",
        },
      ],
    };

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockResponse,
    } as Response);

    const result = await searchRequirements("proj-123", "authentication", 5);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/projects/proj-123/search?q=authentication&top_k=5",
      expect.objectContaining({ method: "GET" })
    );
    expect(result.total_results).toBe(1);
    expect(result.results[0].req_id).toBe("REQ-AUTH-01");
  });
});
