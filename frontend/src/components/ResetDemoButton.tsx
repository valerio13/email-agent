import { useResetDemo } from '../api/hooks'
import { useNotice } from '../lib/notice'
import { Button } from './Button'
import { Icon } from './Icon'

// Wipes the demo data and loads the sample emails again, dated relative to today.
export function ResetDemoButton() {
  const { notify } = useNotice()
  const reset = useResetDemo()

  const resetDemo = async () => {
    try {
      const result = await reset.mutateAsync()
      notify('success', `Demo reset: ${result.new_emails} emails loaded and analysed.`)
    } catch (error) {
      notify('error', error instanceof Error ? error.message : 'Something failed.')
    }
  }

  return (
    <Button onClick={resetDemo} disabled={reset.isPending}>
      <Icon name="refresh" />
      {reset.isPending ? 'Resetting...' : 'Reset demo'}
    </Button>
  )
}
