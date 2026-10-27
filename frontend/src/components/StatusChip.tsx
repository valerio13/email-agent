import type { DraftStatus } from '../api/client'
import { Chip } from './Chip'

// What happened to the reply draft of an email. Emails without a draft show nothing.
export function StatusChip({ status }: { status: DraftStatus | undefined }) {
  if (status === 'proposed') return <Chip variant="ai" icon="sparkle">AI draft ready</Chip>
  if (status === 'approved') return <Chip variant="done" icon="check">In mailbox</Chip>
  if (status === 'discarded') return <Chip variant="muted" icon="x">Discarded</Chip>
  return null
}
