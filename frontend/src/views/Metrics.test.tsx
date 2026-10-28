import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FakeApi } from '../test/fakeApi'
import { renderWithProviders } from '../test/render'
import { Metrics } from './Metrics'

describe('Metrics', () => {
  it('shows the figures of the week and the estimated time saved', async () => {
    new FakeApi().install()
    renderWithProviders(<Metrics />)

    expect(await screen.findByRole('heading', { name: 'The agent handled 35 emails this week.' })).toBeInTheDocument()
    expect(screen.getByText('3h 16m')).toBeInTheDocument()
    expect(screen.getByText(/2 minutes per email triaged and 6 minutes per draft created/)).toBeInTheDocument()
  })

  it('describes the chart and the mix for people who cannot see them', async () => {
    new FakeApi().install()
    renderWithProviders(<Metrics />)

    expect(await screen.findByRole('img', { name: /Emails processed per day: Tue 2, Wed 3/ })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: '3 emails: 1 urgent, 1 needs reply, 1 informational' })).toBeInTheDocument()
  })

  it('waits for the first emails before showing numbers', async () => {
    new FakeApi({ items: [] }).install()
    renderWithProviders(<Metrics />)

    expect(await screen.findByText('No data yet')).toBeInTheDocument()
  })
})
