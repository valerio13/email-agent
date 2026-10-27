import type { Category, DigestItem } from '../api/client'
import { CATEGORIES } from '../lib/categories'
import { Card } from './Card'
import { FilterChip } from './Chip'
import { EmailRow } from './EmailRow'
import { Icon } from './Icon'
import type { Filter } from './SummaryCard'

const CATEGORY_FILTERS: Category[] = ['urgent', 'needs_reply', 'informational']

// The emails of the day by priority, with a search box and a filter per category.
export function InboxCard({
  items,
  visible,
  counts,
  filter,
  onFilter,
  query,
  onQuery,
  selectedId,
  onSelect,
}: {
  items: DigestItem[]
  visible: DigestItem[]
  counts: Record<Category, number>
  filter: Filter
  onFilter: (filter: Filter) => void
  query: string
  onQuery: (query: string) => void
  selectedId: string
  onSelect: (id: string) => void
}) {
  const toggle = (next: Filter) => onFilter(filter === next ? 'all' : next)
  return (
    <Card aria-labelledby="inbox-heading">
      <div className="mb-[22px] grid gap-[18px]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 id="inbox-heading">Inbox by priority</h3>
          <span className="text-[13px] text-fg-muted">Highest priority first</span>
        </div>
        <label className="flex items-center gap-2.5 rounded-full px-[18px] text-fg-muted shadow-press focus-within:outline-3 focus-within:outline-offset-[3px] focus-within:outline-ring">
          <Icon name="search" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQuery(event.target.value)}
            placeholder="Search subject or sender"
            autoComplete="off"
            className="min-w-0 flex-1 border-0 bg-transparent py-3 text-fg outline-none placeholder:text-fg-muted"
          />
        </label>
        <div className="flex flex-wrap gap-2.5" role="group" aria-label="Filter by category">
          <FilterChip pressed={filter === 'all'} count={items.length} onClick={() => onFilter('all')}>
            All
          </FilterChip>
          {CATEGORY_FILTERS.map((category) => (
            <FilterChip
              key={category}
              pressed={filter === category}
              count={counts[category]}
              onClick={() => toggle(category)}
            >
              {CATEGORIES[category].label}
            </FilterChip>
          ))}
        </div>
      </div>
      {visible.length > 0 ? (
        <ul className="-m-1 grid list-none gap-4 p-1">
          {visible.map((item) => (
            <li key={item.email.id}>
              <EmailRow
                item={item}
                selected={item.email.id === selectedId}
                onSelect={() => onSelect(item.email.id)}
              />
            </li>
          ))}
        </ul>
      ) : (
        <div className="grid justify-items-center gap-3 px-3 py-9 text-center text-fg-muted">
          <Icon name="search" size={22} />
          <p>No emails match this filter.</p>
        </div>
      )}
    </Card>
  )
}
