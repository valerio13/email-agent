import { vi } from 'vitest'
import type { Category, Digest, DigestItem, Draft, Metrics, PipelineResult } from '../api/client'

type Call = { method: string; path: string; body?: unknown }

const CATEGORIES: Category[] = ['urgent', 'needs_reply', 'informational']

function draft(id: number, emailId: string, body: string): Draft {
  return {
    id,
    email_id: emailId,
    body,
    status: 'proposed',
    gmail_draft_id: null,
    created_at: '2026-10-26T07:00:00Z',
    updated_at: '2026-10-26T07:00:00Z',
  }
}

// Three emails, one per category, already analysed. The informational one has no draft.
export function sampleItems(): DigestItem[] {
  return [
    {
      email: {
        id: 'demo-001',
        sender: 'Marcus Lee <marcus.lee@northwind.example.com>',
        subject: 'Production API is down',
        body: 'Our integration has been returning errors since 09:00.',
        received_at: '2026-10-26T09:14:00Z',
      },
      analysis: {
        category: 'urgent',
        priority: 'high',
        summary: 'Production API is down: errors since 09:00',
        needs_reply: true,
        draft_reply: 'Hi Marcus,',
      },
      draft: draft(1, 'demo-001', 'Hi Marcus,\n\nThanks for your message.'),
    },
    {
      email: {
        id: 'demo-004',
        sender: 'Priya Nair <priya.nair@lumen.example.com>',
        subject: 'Quote for the Q4 website redesign',
        body: 'Could you send us a quote for redesigning our website?',
        received_at: '2026-10-26T07:55:00Z',
      },
      analysis: {
        category: 'needs_reply',
        priority: 'medium',
        summary: 'Quote requested for the website redesign',
        needs_reply: true,
        draft_reply: 'Hi Priya,',
      },
      draft: draft(2, 'demo-004', 'Hi Priya,\n\nThanks for reaching out.'),
    },
    {
      email: {
        id: 'demo-008',
        sender: 'Product Weekly <news@productweekly.example.com>',
        subject: 'Your weekly product newsletter',
        body: 'This week we shipped three new features.',
        received_at: '2026-10-26T05:00:00Z',
      },
      analysis: {
        category: 'informational',
        priority: 'low',
        summary: 'Weekly newsletter',
        needs_reply: false,
        draft_reply: null,
      },
      draft: null,
    },
  ]
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

// A stand-in for the backend. It answers the API calls from memory and records them, so a test
// can check what the screen sent and in which order.
export class FakeApi {
  items: DigestItem[]
  demoMode: boolean
  offline = false
  // What a run of the pipeline finds, and an optional gate that holds it until a test opens it.
  pipelineResult: PipelineResult = { new_emails: 2, analysed: 2 }
  pipelineGate: Promise<void> | null = null
  pipelineBusy = false
  calls: Call[] = []

  constructor({ items = sampleItems(), demoMode = true } = {}) {
    this.items = items
    this.demoMode = demoMode
  }

  install() {
    vi.stubGlobal('fetch', this.fetch)
    return this
  }

  // Someone else decides a draft while the screen still shows it as pending.
  decideBehindTheScenes(draftId: number, status: 'approved' | 'discarded') {
    const item = this.items.find((entry) => entry.draft?.id === draftId)
    if (item?.draft) item.draft = { ...item.draft, status }
  }

  // The day of an email, as the backend groups them.
  private dayOf = (item: DigestItem) => item.email.received_at.slice(0, 10)

  private digest(requested: string | null): Digest {
    const days = [...new Set(this.items.map(this.dayOf))].sort()
    const day = requested ?? days.at(-1) ?? null
    const items = this.items.filter((item) => this.dayOf(item) === day)
    return {
      day,
      previous_day: days.findLast((other) => day && other < day) ?? null,
      next_day: days.find((other) => day && other > day) ?? null,
      total: items.length,
      counts: Object.fromEntries(
        CATEGORIES.map((category) => [
          category,
          items.filter((item) => item.analysis.category === category).length,
        ]),
      ) as Record<Category, number>,
      pending_drafts: this.pending().length,
      items,
    }
  }

  private pending() {
    return this.items.filter((item) => item.draft?.status === 'proposed')
  }

  private metrics(): Metrics {
    const days = ['2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25', '2026-10-26']
    return {
      days: this.items.length ? days.map((day, index) => ({ day, emails: index + 2 })) : [],
      emails_processed: 35,
      drafts_created: 21,
      waiting_for_review: this.pending().length,
      minutes_saved: 196,
      minutes_per_email: 2,
      minutes_per_draft: 6,
    }
  }

  private decide(id: number, status: 'approved' | 'discarded') {
    const item = this.items.find((entry) => entry.draft?.id === id)
    if (!item?.draft) return json({ detail: `Draft ${id} does not exist.` }, 404)
    if (item.draft.status !== 'proposed') {
      return json({ detail: `Draft ${id} is already ${item.draft.status}.` }, 409)
    }
    item.draft = {
      ...item.draft,
      status,
      gmail_draft_id: status === 'approved' ? `demo-draft-${id}` : null,
    }
    return json(item.draft)
  }

  private restore(id: number) {
    const item = this.items.find((entry) => entry.draft?.id === id)
    if (!item?.draft) return json({ detail: `Draft ${id} does not exist.` }, 404)
    if (item.draft.status !== 'discarded') {
      return json({ detail: `Draft ${id} is not discarded (it is ${item.draft.status}).` }, 409)
    }
    item.draft = { ...item.draft, status: 'proposed' }
    return json(item.draft)
  }

  fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    if (this.offline) throw new TypeError('Failed to fetch')
    const method = init?.method ?? 'GET'
    const url = new URL(String(input).replace(/^\/api/, ''), 'http://fake')
    const path = url.pathname
    const body = typeof init?.body === 'string' ? JSON.parse(init.body) : undefined
    this.calls.push({ method, path: path + url.search, body })

    if (method === 'GET' && path === '/digest') return json(this.digest(url.searchParams.get('day')))
    if (method === 'GET' && path === '/drafts') return json(this.pending())
    if (method === 'GET' && path === '/metrics') return json(this.metrics())
    if (method === 'GET' && path === '/config') return json({ demo_mode: this.demoMode })
    if (method === 'POST' && path === '/pipeline/run') {
      await this.pipelineGate
      if (this.pipelineBusy) {
        return json({ detail: 'A run is already in progress. Wait for it to finish.' }, 409)
      }
      return json(this.pipelineResult)
    }
    if (method === 'POST' && (path === '/demo/run' || path === '/demo/reset')) {
      this.items = sampleItems()
      return json({ new_emails: this.items.length, analysed: this.items.length })
    }

    const draftRoute = path.match(/^\/drafts\/(\d+)(?:\/(approve|discard|restore))?$/)
    if (draftRoute) {
      const id = Number(draftRoute[1])
      if (method === 'PATCH') {
        const item = this.items.find((entry) => entry.draft?.id === id)
        if (!item?.draft) return json({ detail: `Draft ${id} does not exist.` }, 404)
        item.draft = { ...item.draft, body: body.body }
        return json(item.draft)
      }
      if (draftRoute[2] === 'approve') return this.decide(id, 'approved')
      if (draftRoute[2] === 'discard') return this.decide(id, 'discarded')
      if (draftRoute[2] === 'restore') return this.restore(id)
    }
    return json({ detail: 'Not found' }, 404)
  }

  // The calls that changed something, in order, as "METHOD path".
  writes() {
    return this.calls.filter((call) => call.method !== 'GET').map((call) => `${call.method} ${call.path}`)
  }
}
