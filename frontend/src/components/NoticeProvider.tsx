import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import { type Notice, type NoticeKind, NoticeContext, useNotice } from '../lib/notice'
import { Icon, type IconName } from './Icon'

const SECONDS_VISIBLE = 7

// Keeps the current notice. Wrap the app in it and show the notice with NoticeBar.
export function NoticeProvider({ children }: { children: ReactNode }) {
  const [notice, setNotice] = useState<Notice | null>(null)
  const timer = useRef<number | undefined>(undefined)

  const notify = useCallback((kind: NoticeKind, text: string) => {
    setNotice({ kind, text })
    window.clearTimeout(timer.current)
    // An info notice says that something is still going on, so it stays until another replaces it.
    if (kind !== 'info') {
      timer.current = window.setTimeout(() => setNotice(null), SECONDS_VISIBLE * 1000)
    }
  }, [])

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return <NoticeContext value={{ notice, notify }}>{children}</NoticeContext>
}

const KINDS: Record<NoticeKind, string> = {
  info: 'bg-bg text-fg shadow-raise-1',
  success: 'bg-mint text-on-mint',
  warn: 'bg-amber text-on-amber',
  error: 'bg-rose text-on-rose',
}

const ICONS: Record<NoticeKind, IconName> = {
  info: 'refresh',
  success: 'check',
  warn: 'info',
  error: 'info',
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
          <Icon name={ICONS[notice.kind]} />
          {notice.text}
        </div>
      )}
    </div>
  )
}
