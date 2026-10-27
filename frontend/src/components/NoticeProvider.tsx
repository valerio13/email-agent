import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import { type Notice, type NoticeKind, NoticeContext, useNotice } from '../lib/notice'
import { Icon } from './Icon'

const SECONDS_VISIBLE = 7

// Keeps the current notice. Wrap the app in it and show the notice with NoticeBar.
export function NoticeProvider({ children }: { children: ReactNode }) {
  const [notice, setNotice] = useState<Notice | null>(null)
  const timer = useRef<number | undefined>(undefined)

  const notify = useCallback((kind: NoticeKind, text: string) => {
    setNotice({ kind, text })
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setNotice(null), SECONDS_VISIBLE * 1000)
  }, [])

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return <NoticeContext value={{ notice, notify }}>{children}</NoticeContext>
}

const KINDS: Record<NoticeKind, string> = {
  success: 'bg-mint text-on-mint',
  warn: 'bg-amber text-on-amber',
  error: 'bg-rose text-on-rose',
}

// A live region, so screen readers announce a notice when it appears. It takes no space when empty.
export function NoticeBar() {
  const { notice } = useNotice()
  return (
    <div role="status" aria-live="polite" className="empty:hidden">
      {notice && (
        <div
          className={`flex items-center gap-2.5 rounded-[10px] px-[18px] py-3 text-sm font-semibold ${KINDS[notice.kind]}`}
        >
          <Icon name={notice.kind === 'success' ? 'check' : 'info'} />
          {notice.text}
        </div>
      )}
    </div>
  )
}
