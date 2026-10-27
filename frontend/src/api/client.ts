import type { components } from './schema'

type Schemas = components['schemas']

// The API types come from schema.d.ts, which is generated from the backend (npm run gen:api).
export type Category = Schemas['Category']
export type Priority = Schemas['Priority']
export type DraftStatus = Schemas['DraftStatus']
export type Email = Schemas['Email']
export type EmailAnalysis = Schemas['EmailAnalysis']
export type Draft = Schemas['Draft']
export type DigestItem = Schemas['DigestItem']
export type DailyCount = Schemas['DailyCount']
export type Metrics = Schemas['Metrics']
export type PipelineResult = Schemas['PipelineResult']
// OpenAPI describes the counts as a plain string map. They are keyed by category.
export type Digest = Omit<Schemas['Digest'], 'counts'> & { counts: Record<Category, number> }

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI answers our own errors (404, 409, 403) with {"detail": "text"}.
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // The body was not JSON: use the generic message below.
  }
  return `Request failed (${response.status})`
}

const UNREACHABLE = 'Could not reach the API.'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init).catch(() => {
    throw new ApiError(0, UNREACHABLE)
  })
  if (!response.ok) {
    // The dev proxy and any reverse proxy answer 502 to 504 when the API is down.
    const down = response.status >= 502 && response.status <= 504
    throw new ApiError(response.status, down ? UNREACHABLE : await errorMessage(response))
  }
  return response.json() as Promise<T>
}

const post = <T>(path: string) => request<T>(path, { method: 'POST' })

export const api = {
  digest: () => request<Digest>('/digest'),
  drafts: () => request<DigestItem[]>('/drafts'),
  metrics: () => request<Metrics>('/metrics'),
  editDraft: (id: number, body: string) =>
    request<Draft>(`/drafts/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body }),
    }),
  approveDraft: (id: number) => post<Draft>(`/drafts/${id}/approve`),
  discardDraft: (id: number) => post<Draft>(`/drafts/${id}/discard`),
  runDemo: () => post<PipelineResult>('/demo/run'),
  resetDemo: () => post<PipelineResult>('/demo/reset'),
}
