import type { DigestItem } from '../api/client'
import { CATEGORIES } from '../lib/categories'
import { formatShort, nameOf } from '../lib/format'
import { Chip } from './Chip'
import { PriorityBars } from './PriorityBars'
import { StatusChip } from './StatusChip'

// One line of the inbox. The selected row (aria-current) looks pressed in.
export function EmailRow({
  item,
  selected,
  onSelect,
}: {
  item: DigestItem
  selected: boolean
  onSelect: () => void
}) {
  const { email, analysis, draft } = item
  const category = CATEGORIES[analysis.category]
  return (
    <button
      type="button"
      aria-current={selected}
      onClick={onSelect}
      className="grid w-full grid-cols-[auto_minmax(0,1fr)] items-start gap-4 rounded-[14px] bg-bg px-[18px] py-4 text-left shadow-raise-1 transition-shadow duration-200 hover:shadow-raise-2 aria-[current=true]:shadow-press aria-[current=true]:hover:shadow-press max-[760px]:gap-3 max-[760px]:p-3.5"
    >
      <PriorityBars priority={analysis.priority} />
      <span className="grid min-w-0 gap-1.5">
        <span className="text-[15px] font-bold [overflow-wrap:anywhere]">{email.subject}</span>
        <span className="text-[13px] text-fg-muted">
          {nameOf(email.sender)} &middot; {formatShort(email.received_at)}
        </span>
        <span className="line-clamp-2 text-sm text-fg-muted">{analysis.summary}</span>
        <span className="mt-1 flex flex-wrap gap-2">
          <Chip variant={category.tone} icon={category.icon}>
            {category.label}
          </Chip>
          <StatusChip status={draft?.status} />
        </span>
      </span>
    </button>
  )
}
