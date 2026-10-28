import type { Category } from '../api/client'
import { CATEGORIES, DOT_COLORS } from '../lib/categories'
import { Card } from './Card'

const ORDER: Category[] = ['urgent', 'needs_reply', 'informational']

// How the latest day split between the three categories, as one segmented bar.
export function MixCard({
  counts,
  minutesPerEmail,
  minutesPerDraft,
}: {
  counts: Record<Category, number>
  minutesPerEmail: number
  minutesPerDraft: number
}) {
  const total = ORDER.reduce((sum, category) => sum + counts[category], 0)
  const summary = ORDER.map((category) => `${counts[category]} ${CATEGORIES[category].label.toLowerCase()}`).join(', ')
  return (
    <Card aria-labelledby="mix-heading" className="grid gap-[22px]">
      <h3 id="mix-heading">Mix of the latest day</h3>
      <div
        role="img"
        aria-label={`${total} emails: ${summary}`}
        className="flex h-[22px] gap-1 overflow-hidden rounded-full p-1 shadow-press"
      >
        {ORDER.map((category) => (
          <span
            key={category}
            className={`min-w-2 rounded-full ${DOT_COLORS[CATEGORIES[category].tone]}`}
            style={{ flex: Math.max(counts[category], 0.001) }}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-2 text-[13px] font-semibold text-fg-muted">
        {ORDER.map((category) => (
          <span key={category} className="inline-flex items-center gap-2">
            <span className={`size-2.5 rounded-full ${DOT_COLORS[CATEGORIES[category].tone]}`} />
            {CATEGORIES[category].label} {counts[category]}
          </span>
        ))}
      </div>
      <p className="text-[13px] text-fg-muted">
        Time saved is estimated at {minutesPerEmail} minutes per email triaged and {minutesPerDraft}{' '}
        minutes per draft created.
      </p>
    </Card>
  )
}
