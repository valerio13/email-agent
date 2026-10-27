import type { Category, Digest } from '../api/client'
import { CATEGORIES } from '../lib/categories'
import { formatDay } from '../lib/format'
import { Card } from './Card'
import { Tile } from './Tile'

export type Filter = Category | 'all'

const TILE_CATEGORIES: Category[] = ['urgent', 'needs_reply', 'informational']

function headline(urgent: number, waiting: number) {
  if (waiting === 0) return 'You are all caught up.'
  if (urgent > 0) return `${urgent} urgent ${urgent === 1 ? 'email needs' : 'emails need'} you.`
  return `${waiting} ${waiting === 1 ? 'reply is' : 'replies are'} waiting for you.`
}

// The day at a glance. The figures come from the digest, which counts what the model decided.
export function SummaryCard({
  digest,
  day,
  filter,
  onFilter,
  onOpenDrafts,
}: {
  digest: Digest
  day: string
  filter: Filter
  onFilter: (filter: Filter) => void
  onOpenDrafts: () => void
}) {
  const waiting = digest.pending_drafts
  const review =
    waiting === 0
      ? 'Every draft has been reviewed.'
      : `${waiting} reply ${waiting === 1 ? 'draft is' : 'drafts are'} ready for your review.`
  return (
    <Card aria-labelledby="summary-heading" className="grid gap-6">
      <div>
        <p className="text-xs font-bold tracking-[0.08em] text-fg-muted uppercase">
          Daily summary &middot; {formatDay(day)}
        </p>
        <h2 id="summary-heading" className="mt-2.5">
          {headline(digest.counts.urgent, waiting)}
        </h2>
        <p className="mt-2 max-w-[62ch] text-fg-muted">
          {digest.total} emails analysed. {review} Nothing has been sent.
        </p>
      </div>
      <div className="grid grid-cols-4 gap-[18px] max-[1040px]:grid-cols-2">
        {TILE_CATEGORIES.map((category) => (
          <Tile
            key={category}
            label={CATEGORIES[category].label}
            value={digest.counts[category]}
            tone={CATEGORIES[category].tone}
            pressed={filter === category}
            onClick={() => onFilter(filter === category ? 'all' : category)}
          />
        ))}
        <Tile label="Drafts to review" value={waiting} tone="ready" onClick={onOpenDrafts} />
      </div>
    </Card>
  )
}
