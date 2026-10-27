import { useDigest, useDrafts } from '../api/hooks'
import { AiCard } from '../components/AiCard'
import { Button } from '../components/Button'
import { Card, Well } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { StatusChip } from '../components/StatusChip'
import { formatShort, nameOf } from '../lib/format'

// Human review: every draft waiting for a decision, next to the email it answers, and below
// them what has already been decided.
export function Drafts() {
  const drafts = useDrafts()
  const digest = useDigest()

  if (drafts.isPending) return <EmptyState icon="refresh" title="Loading the drafts" />
  if (drafts.error) {
    return (
      <EmptyState
        icon="info"
        title="Could not load the drafts"
        action={<Button onClick={() => drafts.refetch()}>Try again</Button>}
      >
        {drafts.error.message}
      </EmptyState>
    )
  }

  const pending = drafts.data
  const reviewed = (digest.data?.items ?? []).filter(
    ({ draft }) => draft && draft.status !== 'proposed',
  )

  return (
    <>
      <div>
        <p className="text-xs font-bold tracking-[0.08em] text-fg-muted uppercase">Human review</p>
        <h2 className="mt-2">
          {pending.length
            ? `${pending.length} ${pending.length === 1 ? 'draft' : 'drafts'} waiting for you`
            : 'No drafts waiting'}
        </h2>
      </div>
      {pending.length > 0 ? (
        pending.map((item) => (
          <article
            key={item.email.id}
            aria-label={`Draft for ${item.email.subject}`}
            className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)] items-start gap-7 max-[760px]:grid-cols-1"
          >
            <Card className="grid content-start gap-3">
              <h3>{item.email.subject}</h3>
              <p className="text-fg-muted">
                {nameOf(item.email.sender)} &middot; {formatShort(item.email.received_at)}
              </p>
              <Well className="whitespace-pre-wrap [overflow-wrap:anywhere]">{item.email.body}</Well>
            </Card>
            <AiCard item={item} big />
          </article>
        ))
      ) : (
        <EmptyState icon="check" title="All caught up">
          Every draft has been reviewed. New ones appear after the next daily run.
        </EmptyState>
      )}
      {reviewed.length > 0 && (
        <Card aria-labelledby="reviewed-heading" className="grid gap-3">
          <h3 id="reviewed-heading">Reviewed</h3>
          {reviewed.map(({ email, draft }) => (
            <div
              key={email.id}
              className="flex flex-wrap items-center justify-between gap-2.5 rounded-[10px] px-[18px] py-3 shadow-press"
            >
              <span>
                <strong>{email.subject}</strong>{' '}
                <span className="text-fg-muted">to {nameOf(email.sender)}</span>
              </span>
              <StatusChip status={draft?.status} />
            </div>
          ))}
        </Card>
      )}
    </>
  )
}
