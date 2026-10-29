import type { Email } from '../api/client'
import { useRestoreDraft } from '../api/hooks'
import { messageOf } from '../lib/errors'
import { useNotice } from '../lib/notice'
import { Button } from './Button'
import { Icon } from './Icon'

// Brings a discarded draft back to the review list. An approved draft cannot come back: it is
// already in the mailbox.
export function UndoButton({ email, draftId }: { email: Email; draftId: number }) {
  const { notify } = useNotice()
  const restore = useRestoreDraft()

  const undo = async () => {
    try {
      await restore.mutateAsync(draftId)
      notify('success', `Draft for "${email.subject}" is back in review.`)
    } catch (error) {
      notify('error', messageOf(error))
    }
  }

  return (
    <Button onClick={undo} disabled={restore.isPending}>
      <Icon name="undo" />
      Undo discard
    </Button>
  )
}
