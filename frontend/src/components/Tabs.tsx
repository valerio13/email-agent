import type { KeyboardEvent } from 'react'
import { PANEL_ID, TABS, type TabId, tabElementId } from '../lib/tabs'

// The three sections of the dashboard. The Drafts tab carries the number of drafts waiting.
// Keyboard: only the selected tab is in the tab order, and the arrow keys, Home and End move
// between tabs, as in the WAI-ARIA tabs pattern.
export function Tabs({
  tab,
  onChange,
  draftCount,
}: {
  tab: TabId
  onChange: (tab: TabId) => void
  draftCount: number
}) {
  const onKeyDown = (event: KeyboardEvent) => {
    const current = TABS.findIndex(({ id }) => id === tab)
    let next: number
    if (event.key === 'ArrowRight') next = (current + 1) % TABS.length
    else if (event.key === 'ArrowLeft') next = (current - 1 + TABS.length) % TABS.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = TABS.length - 1
    else return
    event.preventDefault()
    onChange(TABS[next].id)
    document.getElementById(tabElementId(TABS[next].id))?.focus()
  }

  return (
    <div
      role="tablist"
      aria-label="Sections"
      onKeyDown={onKeyDown}
      className="inline-flex max-w-full justify-self-start gap-1 overflow-x-auto rounded-full p-1.5 shadow-press"
    >
      {TABS.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          id={tabElementId(id)}
          aria-selected={tab === id}
          aria-controls={PANEL_ID}
          tabIndex={tab === id ? 0 : -1}
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
    </div>
  )
}
