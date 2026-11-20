/**
 * Hybrid Search API Client.
 */

import { apiGet } from "./client";
import type { SearchResponse } from "./types";

/**
 * Execute hybrid semantic + keyword search with Reciprocal Rank Fusion.
 */
export async function searchRequirements(
  projectId: string,
  query: string,
  topK: number = 6
): Promise<SearchResponse> {
  return apiGet<SearchResponse>(
    `/projects/${encodeURIComponent(projectId)}/search`,
    {
      q: query,
      top_k: topK,
    }
  );
}
