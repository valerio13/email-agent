import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { describe, expect, it } from 'vitest'
import App from './App'
import { FakeApi } from './test/fakeApi'
import { renderApp } from './test/render'

// axe checks the page for accessibility rules it can verify from the markup. Colors are left out
// because jsdom has no layout or styles, so contrast cannot be measured here.
async function violations() {
  const result = await axe.run(document.body, { rules: { 'color-contrast': { enabled: false } } })
  return result.violations.map(
    (violation) => `${violation.id}: ${violation.nodes.map((node) => node.html.slice(0, 140)).join(' | ')}`,
  )
}

describe('accessibility', () => {
  it('has no violations in the Overview', async () => {
    new FakeApi().install()
    renderApp(App)
    await screen.findByRole('heading', { name: /urgent email/ })
    expect(await violations()).toEqual([])
  })

  it('has no violations in Drafts', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderApp(App)
    await user.click(await screen.findByRole('tab', { name: /Drafts/ }))
    await screen.findByRole('heading', { name: /drafts waiting/ })
    expect(await violations()).toEqual([])
  })

  it('has no violations in Metrics', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderApp(App)
    await user.click(await screen.findByRole('tab', { name: 'Metrics' }))
    await screen.findByText(/The agent handled/)
    expect(await violations()).toEqual([])
  })
})
