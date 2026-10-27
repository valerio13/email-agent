import { useDigest } from './api/hooks'
import { Icon } from './components/Icon'
import { ThemeToggle } from './components/ThemeToggle'

// Placeholder that proves the chain works (proxy, API client, types, tokens). The Overview view
// replaces it in the next step.
function ConnectionCard() {
  const { data, error, isPending } = useDigest()
  let message = 'Loading the digest...'
  if (error) message = `Could not reach the API: ${error.message}`
  else if (data) {
    message = data.day
      ? `${data.total} emails on ${data.day}, ${data.pending_drafts} drafts waiting for review.`
      : 'The API is reachable but has no emails yet.'
  }
  return (
    <section
      className="min-w-0 rounded-card bg-bg p-7 shadow-raise-2"
      aria-busy={isPending}
      role="status"
    >
      <h3>API connection</h3>
      <p className="mt-1 text-fg-muted">{message}</p>
    </section>
  )
}

export default function App() {
  return (
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
      <ConnectionCard />
    </div>
  )
}
