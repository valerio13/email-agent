import type { PipelineResult } from '../api/client'
import { useRunPipeline } from '../api/hooks'
import { messageOf } from '../lib/errors'
import { useNotice } from '../lib/notice'
import { Button } from './Button'
import { Icon } from './Icon'

function summary({ new_emails, analysed }: PipelineResult) {
  if (new_emails === 0 && analysed === 0) return 'No new emails.'
  return `${new_emails} new ${new_emails === 1 ? 'email' : 'emails'}, ${analysed} analysed.`
}

// Fetches the new mail and analyses it now, instead of waiting for the daily run. With a real
// model it can take a minute, so a notice says that the work is going on until it ends.
export function CheckMailButton() {
  const { notify } = useNotice()
  const run = useRunPipeline()

  const check = async () => {
    notify('info', 'Fetching the new emails and analysing them. This can take a minute...')
    try {
      notify('success', summary(await run.mutateAsync()))
    } catch (error) {
      notify('error', messageOf(error))
    }
  }

  return (
    <Button variant="primary" onClick={check} disabled={run.isPending}>
      <Icon name="refresh" />
      {run.isPending ? 'Checking...' : 'Check new mail'}
    </Button>
  )
}
