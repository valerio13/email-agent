import { useRef, useState } from 'react'
import { useDigest, useRunDemo } from '../api/hooks'
import { Button } from '../components/Button'
import { EmailDetail } from '../components/EmailDetail'
import { EmptyState } from '../components/EmptyState'
import { InboxCard } from '../components/InboxCard'
import { type Filter, SummaryCard } from '../components/SummaryCard'

// The first screen: the day's summary, the inbox by priority and the selected email.
export function Overview({ onOpenDrafts }: { onOpenDrafts: () => void }) {
  const { data: digest, error, isPending, refetch } = useDigest()
  const runDemo = useRunDemo()
  const [filter, setFilter] = useState<Filter>('all')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const detailRef = useRef<HTMLDivElement>(null)

  if (isPending) return <EmptyState icon="refresh" title="Loading the digest" />
  if (error) {
    return (
      <EmptyState
        icon="info"
        title="Could not load the digest"
        action={<Button onClick={() => refetch()}>Try again</Button>}
      >
        {error.message}
      </EmptyState>
    )
  }
  if (!digest.day) {
    return (
      <EmptyState
        icon="mail"
        title="No emails analysed yet"
        action={
          <Button variant="primary" onClick={() => runDemo.mutate()} disabled={runDemo.isPending}>
            Load demo emails
          </Button>
        }
      >
        {runDemo.error?.message ?? 'New mail appears here after the next daily run.'}
      </EmptyState>
    )
  }

  // If nothing is selected, or the selection is gone after a refresh, show the top email.
  const selected = digest.items.find((item) => item.email.id === selectedId) ?? digest.items[0]
  const needle = query.trim().toLowerCase()
  const visible = digest.items.filter(
    ({ email, analysis }) =>
      (filter === 'all' || analysis.category === filter) &&
      (!needle || `${email.subject} ${email.sender} ${analysis.summary}`.toLowerCase().includes(needle)),
  )

  function select(id: string) {
    setSelectedId(id)
    // On narrow screens the detail sits below the list, so bring it into view.
    if (window.matchMedia('(max-width: 1040px)').matches) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      detailRef.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
    }
  }

  return (
    <>
      <SummaryCard
        digest={digest}
        day={digest.day}
        filter={filter}
        onFilter={setFilter}
        onOpenDrafts={onOpenDrafts}
      />
      <div className="grid grid-cols-[minmax(0,1.12fr)_minmax(0,1fr)] items-start gap-7 max-[1040px]:grid-cols-1">
        <InboxCard
          items={digest.items}
          visible={visible}
          counts={digest.counts}
          filter={filter}
          onFilter={setFilter}
          query={query}
          onQuery={setQuery}
          selectedId={selected.email.id}
          onSelect={select}
        />
        <EmailDetail ref={detailRef} item={selected} />
      </div>
    </>
  )
}
