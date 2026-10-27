import { useState } from 'react'
import { useDigest } from './api/hooks'
import { EmptyState } from './components/EmptyState'
import { Icon } from './components/Icon'
import { NoticeBar, NoticeProvider } from './components/NoticeProvider'
import { type TabId, Tabs } from './components/Tabs'
import { ThemeToggle } from './components/ThemeToggle'
import { Drafts } from './views/Drafts'
import { Overview } from './views/Overview'

export default function App() {
  const [tab, setTab] = useState<TabId>('overview')
  const { data: digest } = useDigest()

  return (
    <NoticeProvider>
      <div className="mx-auto grid max-w-[1240px] gap-7 pt-7 pr-[max(16px,env(safe-area-inset-right,0px))] pb-14 pl-[max(16px,env(safe-area-inset-left,0px))]">
        <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-4">
          <div className="flex min-w-0 items-center gap-3.5">
            <div className="grid size-[46px] place-items-center rounded-lg bg-mint text-on-mint shadow-[var(--raise-2),0_0_20px_var(--glow)]">
              <Icon name="mail" size={22} />
            </div>
            <div>
              <h1>Email agent</h1>
              <p className="text-[13px] text-fg-muted">
                Daily summary and reply drafts, approved by you
              </p>
            </div>
          </div>
          <ThemeToggle />
        </header>
        <Tabs tab={tab} onChange={setTab} draftCount={digest?.pending_drafts ?? 0} />
        <NoticeBar />
        <div role="tabpanel" aria-labelledby={`tab-${tab}`} className="grid gap-7">
          {tab === 'overview' && <Overview onOpenDrafts={() => setTab('drafts')} />}
          {tab === 'drafts' && <Drafts />}
          {/* The Metrics view arrives in the next step. */}
          {tab === 'metrics' && (
            <EmptyState icon="refresh" title="Coming soon">
              This section is built in a later step.
            </EmptyState>
          )}
        </div>
      </div>
    </NoticeProvider>
  )
}
