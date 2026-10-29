import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import App from './App'
import { FakeApi } from './test/fakeApi'
import { renderApp } from './test/render'

describe('App', () => {
  it('shows the number of drafts waiting on the Drafts tab', async () => {
    new FakeApi().install()
    renderApp(App)

    const tab = await screen.findByRole('tab', { name: /Drafts/ })
    await waitFor(() => expect(tab).toHaveTextContent('2'))
  })

  it('switches sections with the mouse', async () => {
    // Metrics is loaded lazily with Recharts. Loading it first keeps a slow machine from
    // running out of the time that the screen is given to show it.
    await import('./views/Metrics')
    const user = userEvent.setup()
    new FakeApi().install()
    renderApp(App)

    await user.click(await screen.findByRole('tab', { name: /Drafts/ }))
    expect(await screen.findByRole('heading', { name: '2 drafts waiting for you' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Drafts/ })).toHaveAttribute('aria-selected', 'true')

    await user.click(screen.getByRole('tab', { name: 'Metrics' }))
    expect(await screen.findByText(/The agent handled/)).toBeInTheDocument()
  })

  it('moves between sections with the arrow keys, Home and End', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderApp(App)

    const overview = await screen.findByRole('tab', { name: 'Overview' })
    overview.focus()
    // Only the selected tab is in the tab order.
    expect(screen.getByRole('tab', { name: 'Metrics' })).toHaveAttribute('tabindex', '-1')

    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: /Drafts/ })).toHaveFocus()
    expect(screen.getByRole('tab', { name: /Drafts/ })).toHaveAttribute('aria-selected', 'true')

    await user.keyboard('{End}')
    expect(screen.getByRole('tab', { name: 'Metrics' })).toHaveFocus()

    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Overview' })).toHaveFocus()

    await user.keyboard('{ArrowLeft}')
    expect(screen.getByRole('tab', { name: 'Metrics' })).toHaveFocus()

    await user.keyboard('{Home}')
    expect(screen.getByRole('tab', { name: 'Overview' })).toHaveFocus()
  })

  it('links every tab to the panel it controls', async () => {
    new FakeApi().install()
    renderApp(App)

    const panel = await screen.findByRole('tabpanel')
    expect(screen.getByRole('tab', { name: 'Overview' })).toHaveAttribute('aria-controls', panel.id)
    expect(panel).toHaveAccessibleName('Overview')
  })

  it('offers a skip link to the main content', async () => {
    new FakeApi().install()
    renderApp(App)

    expect(await screen.findByRole('link', { name: 'Skip to content' })).toHaveAttribute('href', '#content')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'content')
  })

  it('shows Reset demo only in demo mode', async () => {
    new FakeApi({ demoMode: false }).install()
    const { unmount } = renderApp(App)
    await screen.findByRole('heading', { name: /urgent email/ })
    expect(screen.queryByRole('button', { name: 'Reset demo' })).not.toBeInTheDocument()
    unmount()

    new FakeApi({ demoMode: true }).install()
    renderApp(App)
    expect(await screen.findByRole('button', { name: 'Reset demo' })).toBeInTheDocument()
  })

  it('resets the demo and tells how many emails were loaded', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderApp(App)

    await user.click(await screen.findByRole('button', { name: 'Reset demo' }))
    expect(await screen.findByText('Demo reset: 3 emails loaded and analysed.')).toBeInTheDocument()
    expect(api.writes()).toEqual(['POST /demo/reset'])
  })

  it('remembers the chosen theme', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderApp(App)

    await user.click(await screen.findByRole('button', { name: 'Switch to dark theme' }))
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(localStorage.getItem('email-agent-theme')).toBe('dark')
    expect(screen.getByRole('button', { name: 'Switch to light theme' })).toBeInTheDocument()
  })
})
