import { useState } from 'react'
import type { Draft, Email } from '../api/client'
import { useApproveDraft, useDiscardDraft, useEditDraft } from '../api/hooks'
import { messageOf } from '../lib/errors'
import { useNotice } from '../lib/notice'
import { SectionLabel } from './Card'
import { Button } from './Button'
import { Chip } from './Chip'
import { Icon } from './Icon'
import { UndoButton } from './UndoButton'

function DraftState({ status }: { status: Draft['status'] }) {
  if (status === 'approved') return <Chip variant="done" icon="check">Created in mailbox</Chip>
  if (status === 'discarded') return <Chip variant="muted" icon="x">Discarded</Chip>
  return <Chip variant="ready" icon="draft">Waiting for review</Chip>
}

// The reply draft written by the model, which the reviewer edits, approves or discards.
// Approving creates the draft in the mailbox. The email is never sent from here.
// Mount it with key={draft.id}, so the text restarts when another draft is shown.
export function DraftEditor({
  email,
  draft,
  big = false,
}: {
  email: Email
  draft: Draft
  big?: boolean
}) {
  const { notify } = useNotice()
  const edit = useEditDraft()
  const approve = useApproveDraft()
  const discard = useDiscardDraft()
  const [text, setText] = useState(draft.body)

  const locked = draft.status !== 'proposed'
  const empty = text.trim() === ''
  const changed = text !== draft.body
  // Not edit.isPending: a click that starts with the text box losing focus would find its own
  // button disabled by the save that the focus loss started, and would be lost.
  const busy = approve.isPending || discard.isPending

  // Edits are saved when the text box loses focus, so they survive choosing another email.
  const save = () => {
    if (changed && !empty && !locked) {
      edit.mutate({ id: draft.id, body: text }, { onError: (error) => notify('error', messageOf(error)) })
    }
  }

  const approveDraft = async () => {
    try {
      if (changed) await edit.mutateAsync({ id: draft.id, body: text })
      await approve.mutateAsync(draft.id)
      notify('success', `Draft for "${email.subject}" created in the mailbox. Nothing was sent.`)
    } catch (error) {
      notify('error', messageOf(error))
    }
  }

  const discardDraft = async () => {
    try {
      await discard.mutateAsync(draft.id)
      notify('warn', `Draft for "${email.subject}" discarded.`)
    } catch (error) {
      notify('error', messageOf(error))
    }
  }

  return (
    <>
      <div>
        <SectionLabel title="Reply draft" aside={<DraftState status={draft.status} />} />
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          onBlur={save}
          disabled={locked}
          aria-label={`Reply draft for ${email.subject}`}
          className="min-h-[168px] w-full resize-y rounded-xl border-0 bg-bg px-[18px] py-4 leading-[1.6] text-fg shadow-press disabled:text-fg-muted"
        />
      </div>
      <div className="flex flex-wrap gap-3">
        <Button variant="primary" onClick={approveDraft} disabled={locked || busy || empty}>
          <Icon name="check" />
          Approve and create draft
        </Button>
        <Button onClick={discardDraft} disabled={locked || busy}>
          <Icon name="x" />
          Discard
        </Button>
        {draft.status === 'discarded' && <UndoButton email={email} draftId={draft.id} />}
      </div>
      {!big && (
        <p className="text-[13px] text-fg-muted">
          Approving saves the draft in your mailbox. The email is never sent from here.
        </p>
      )}
    </>
  )
}
