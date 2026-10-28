import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { NoticeBar, NoticeProvider } from '../components/NoticeProvider'

// A fresh query cache per test, with no retries so that a failure shows up at once.
function client() {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
}

export function renderWithProviders(ui: ReactElement) {
  return render(
    <QueryClientProvider client={client()}>
      <NoticeProvider>
        <NoticeBar />
        {ui}
      </NoticeProvider>
    </QueryClientProvider>,
  )
}

export function renderApp(App: () => ReactElement) {
  return render(
    <QueryClientProvider client={client()}>
      <App />
    </QueryClientProvider>,
  )
}
