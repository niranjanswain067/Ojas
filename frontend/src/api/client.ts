/**
 * Typed API client for Ojas backend.
 */

import type { ErrorResponse } from './types';

export class ApiError extends Error {
  public statusCode: number;
  public detail: string;
  public timestamp?: string;

  constructor(statusCode: number, detail: string, timestamp?: string) {
    super(`API Error ${statusCode}: ${detail}`);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.detail = detail;
    this.timestamp = timestamp;
  }
}

const BASE_URL = '/api';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, body, headers, ...restOptions } = options;

  let url = endpoint.startsWith('/') ? `${BASE_URL}${endpoint}` : `${BASE_URL}/${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const defaultHeaders: Record<string, string> = {
    Accept: 'application/json',
  };

  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  if (!isFormData && body !== undefined) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...restOptions,
    headers: {
      ...defaultHeaders,
      ...headers,
    },
    body: isFormData ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    let timestamp: string | undefined;

    try {
      const errorJson = (await response.json()) as ErrorResponse | { detail?: string };
      if ('detail' in errorJson && typeof errorJson.detail === 'string') {
        errorDetail = errorJson.detail;
      }
      if ('timestamp' in errorJson && typeof errorJson.timestamp === 'string') {
        timestamp = errorJson.timestamp;
      }
    } catch {
      // response body was not valid JSON or was empty
    }

    throw new ApiError(response.status, errorDetail, timestamp);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}

export function apiGet<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  return request<T>(endpoint, { method: 'GET', params });
}

export function apiPost<T>(endpoint: string, body?: unknown, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  return request<T>(endpoint, { method: 'POST', body, params });
}

export function apiPut<T>(endpoint: string, body?: unknown, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  return request<T>(endpoint, { method: 'PUT', body, params });
}

export function apiPatch<T>(endpoint: string, body?: unknown, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  return request<T>(endpoint, { method: 'PATCH', body, params });
}

export function apiDelete<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  return request<T>(endpoint, { method: 'DELETE', params });
}

