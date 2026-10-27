import type { Email } from '../api/client'
import { addressOf, formatLong, nameOf } from '../lib/format'
import { Card, SectionLabel, Well } from './Card'

// The email exactly as it arrived. Nothing here comes from the model.
export function EmailCard({ email }: { email: Email }) {
  return (
    <Card aria-label="Email" className="grid content-start gap-5">
      <div className="grid gap-2.5">
        <h2>{email.subject}</h2>
        <p className="text-fg-muted">
          From {nameOf(email.sender)} &lt;{addressOf(email.sender)}&gt;
          <br />
          {formatLong(email.received_at)}
        </p>
      </div>
      <div>
        <SectionLabel title="Original email" />
        <Well className="whitespace-pre-wrap [overflow-wrap:anywhere]">{email.body}</Well>
      </div>
    </Card>
  )
}
