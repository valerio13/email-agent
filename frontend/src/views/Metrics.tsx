import { useDigest, useMetrics } from '../api/hooks'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { DayChart } from '../components/DayChart'
import { EmptyState } from '../components/EmptyState'
import { MixCard } from '../components/MixCard'
import { StatTile } from '../components/Tile'
import { formatDuration } from '../lib/format'

// What the agent did over the last seven days, and how the newest day split by category.
export function Metrics() {
  const metrics = useMetrics()
  const digest = useDigest()

  if (metrics.isPending || digest.isPending) return <EmptyState icon="refresh" title="Loading the metrics" />
  const error = metrics.error ?? digest.error
  if (error) {
    return (
      <EmptyState
        icon="info"
        title="Could not load the metrics"
        action={
          <Button
            onClick={() => {
              void metrics.refetch()
              void digest.refetch()
            }}
          >
            Try again
          </Button>
        }
      >
        {error.message}
      </EmptyState>
    )
  }
  if (metrics.data.days.length === 0) {
    return (
      <EmptyState icon="mail" title="No data yet">
        The metrics appear after the first emails have been analysed.
      </EmptyState>
    )
  }

  const { days, emails_processed, drafts_created, waiting_for_review, minutes_saved } = metrics.data
  return (
    <>
      <div>
        <p className="text-xs font-bold tracking-[0.08em] text-fg-muted uppercase">Last 7 days</p>
        <h2 className="mt-2">The agent handled {emails_processed} emails this week.</h2>
      </div>
      <div className="grid grid-cols-4 gap-[18px] max-[1040px]:grid-cols-2">
        <StatTile label="Emails processed" value={emails_processed} tone="info" />
        <StatTile label="Drafts created" value={drafts_created} tone="ready" />
        <StatTile label="Time saved (est.)" value={formatDuration(minutes_saved)} tone="reply" />
        <StatTile label="Waiting for review" value={waiting_for_review} tone="urgent" />
      </div>
      <div className="grid grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] items-start gap-7 max-[1040px]:grid-cols-1">
        <Card aria-labelledby="chart-heading" className="grid gap-2.5">
          <h3 id="chart-heading">Emails processed per day</h3>
          <DayChart days={days} />
        </Card>
        <MixCard
          counts={digest.data.counts}
          minutesPerEmail={metrics.data.minutes_per_email}
          minutesPerDraft={metrics.data.minutes_per_draft}
        />
      </div>
    </>
  )
}
