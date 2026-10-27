export type TabId = 'overview' | 'drafts' | 'metrics'

const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'drafts', label: 'Drafts' },
  { id: 'metrics', label: 'Metrics' },
]

// The three sections of the dashboard. The Drafts tab carries the number of drafts waiting.
export function Tabs({
  tab,
  onChange,
  draftCount,
}: {
  tab: TabId
  onChange: (tab: TabId) => void
  draftCount: number
}) {
  return (
    <nav
      role="tablist"
      aria-label="Sections"
      className="inline-flex max-w-full justify-self-start gap-1 overflow-x-auto rounded-full p-1.5 shadow-press"
    >
      {TABS.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          id={`tab-${id}`}
          aria-selected={tab === id}
          onClick={() => onChange(id)}
          className="group inline-flex items-center gap-2 rounded-full px-5 py-[9px] text-sm font-bold whitespace-nowrap text-fg-muted transition-shadow duration-200 hover:text-fg aria-selected:bg-mint aria-selected:text-on-mint aria-selected:shadow-raise-1 aria-selected:hover:text-on-mint"
        >
          {label}
          {id === 'drafts' && draftCount > 0 && (
            <span className="rounded-full bg-gray px-2 py-px text-xs text-fg tabular-nums group-aria-selected:bg-white/55 group-aria-selected:text-on-mint">
              {draftCount}
            </span>
          )}
        </button>
      ))}
    </nav>
  )
}
