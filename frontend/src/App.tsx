import { lazy, Suspense, useState } from 'react'
import { useConfig, useDigest } from './api/hooks'
import { CheckMailButton } from './components/CheckMailButton'
import { EmptyState } from './components/EmptyState'
import { Icon } from './components/Icon'
import { NoticeBar, NoticeProvider } from './components/NoticeProvider'
import { ResetDemoButton } from './components/ResetDemoButton'
import { Tabs } from './components/Tabs'
import { ThemeToggle } from './components/ThemeToggle'
import { PANEL_ID, type TabId, tabElementId } from './lib/tabs'
import { Drafts } from './views/Drafts'
import { Overview } from './views/Overview'

// Recharts is large, so the Metrics view is fetched only when its tab is opened.
const Metrics = lazy(() => import('./views/Metrics').then((module) => ({ default: module.Metrics })))

export default function App() {
  const [tab, setTab] = useState<TabId>('overview')
  const { data: digest } = useDigest()
  const { data: config } = useConfig()

  return (
    <NoticeProvider>
      <a
        href="#content"
        className="sr-only font-bold focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-10 focus:rounded-full focus:bg-mint focus:px-5 focus:py-2.5 focus:text-on-mint focus:shadow-raise-2"
      >
        Skip to content
      </a>
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
          <div className="flex flex-wrap gap-3">
            <ThemeToggle />
            {config && (config.demo_mode ? <ResetDemoButton /> : <CheckMailButton />)}
          </div>
        </header>
        <main id="content" tabIndex={-1} className="grid gap-7 outline-none">
          <Tabs tab={tab} onChange={setTab} draftCount={digest?.pending_drafts ?? 0} />
          <NoticeBar />
          <div
            role="tabpanel"
            id={PANEL_ID}
            aria-labelledby={tabElementId(tab)}
            className="grid gap-7"
          >
            {tab === 'overview' && <Overview onOpenDrafts={() => setTab('drafts')} />}
            {tab === 'drafts' && <Drafts />}
            {tab === 'metrics' && (
              <Suspense fallback={<EmptyState icon="refresh" title="Loading the metrics" />}>
                <Metrics />
              </Suspense>
            )}
          </div>
        </main>
      </div>
    </NoticeProvider>
  )
}
