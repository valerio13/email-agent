import { createContext, useContext } from 'react'

export type NoticeKind = 'success' | 'warn' | 'error'
export type Notice = { kind: NoticeKind; text: string }

type NoticeState = {
  notice: Notice | null
  notify: (kind: NoticeKind, text: string) => void
}

export const NoticeContext = createContext<NoticeState>({ notice: null, notify: () => {} })

// The message shown under the tabs after an action, and the function that sets it.
export const useNotice = () => useContext(NoticeContext)
