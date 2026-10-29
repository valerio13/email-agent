import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { FakeApi } from '../test/fakeApi'
import { renderWithProviders } from '../test/render'
import { Overview } from './Overview'

const rowNames = () => screen.getAllByRole('listitem').map((row) => within(row).getByRole('button').textContent)

describe('Overview', () => {
  it('summarises the day and lists the emails by priority', async () => {
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    expect(await screen.findByRole('heading', { name: '1 urgent email needs you.' })).toBeInTheDocument()
    expect(screen.getByText(/3 emails analysed\. 2 reply drafts are ready/)).toBeInTheDocument()
    const rows = rowNames()
    expect(rows).toHaveLength(3)
    expect(rows[0]).toContain('Production API is down')
    expect(rows[2]).toContain('Your weekly product newsletter')
  })

  it('filters the inbox with a summary tile and clears the filter on a second click', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    // The same label is also a filter chip, so look for the tile inside the summary.
    const summary = await screen.findByRole('region', { name: /needs you/ })
    const tile = within(summary).getByRole('button', { name: /^Urgent/ })
    await user.click(tile)
    expect(tile).toHaveAttribute('aria-pressed', 'true')
    expect(rowNames()).toHaveLength(1)

    await user.click(tile)
    expect(tile).toHaveAttribute('aria-pressed', 'false')
    expect(rowNames()).toHaveLength(3)
  })

  it('searches by subject, sender or summary', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    await user.type(await screen.findByRole('searchbox', { name: /search/i }), 'priya')
    expect(rowNames()).toHaveLength(1)
    expect(rowNames()[0]).toContain('Quote for the Q4 website redesign')

    await user.clear(screen.getByRole('searchbox'))
    await user.type(screen.getByRole('searchbox'), 'nothing like this')
    expect(screen.getByText('No emails match this filter.')).toBeInTheDocument()
  })

  it('shows the email and its AI analysis in separate cards for the selected row', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    // The top email is selected until the reviewer chooses another one.
    const email = await screen.findByRole('region', { name: 'Email' })
    expect(within(email).getByRole('heading', { name: 'Production API is down' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Quote for the Q4 website redesign/ }))
    expect(within(screen.getByRole('region', { name: 'Email' })).getByRole('heading', { name: 'Quote for the Q4 website redesign' })).toBeInTheDocument()
    const ai = screen.getByRole('region', { name: /^AI analysis/ })
    expect(within(ai).getByText('Quote requested for the website redesign')).toBeInTheDocument()
    expect(within(ai).getByRole('textbox')).toHaveValue('Hi Priya,\n\nThanks for reaching out.')
  })

  it('lets a discarded draft be undone from its AI card', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    api.decideBehindTheScenes(1, 'discarded')
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    const ai = await screen.findByRole('region', { name: /^AI analysis/ })
    // A discarded draft is locked until it is restored.
    expect(within(ai).getByRole('textbox')).toBeDisabled()
    expect(within(ai).getByRole('button', { name: 'Approve and create draft' })).toBeDisabled()

    await user.click(within(ai).getByRole('button', { name: 'Undo discard' }))

    await waitFor(() => expect(within(ai).getByRole('textbox')).toBeEnabled())
    expect(within(ai).getByText('Waiting for review')).toBeInTheDocument()
    expect(within(ai).queryByRole('button', { name: 'Undo discard' })).not.toBeInTheDocument()
    expect(api.writes()).toEqual(['POST /drafts/1/restore'])
  })

  it('says so when an email needs no reply', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    await user.click(await screen.findByRole('button', { name: /Your weekly product newsletter/ }))
    expect(within(screen.getByRole('region', { name: /^AI analysis/ })).getByText('No reply needed for this email.')).toBeInTheDocument()
  })

  it('opens the Drafts tab from the drafts tile', async () => {
    const user = userEvent.setup()
    let opened = false
    new FakeApi().install()
    renderWithProviders(<Overview onOpenDrafts={() => (opened = true)} />)

    await user.click(await screen.findByRole('button', { name: /Drafts to review/ }))
    expect(opened).toBe(true)
  })

  it('offers to load the demo emails when there is no data, in demo mode only', async () => {
    const user = userEvent.setup()
    const api = new FakeApi({ items: [] }).install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    await user.click(await screen.findByRole('button', { name: 'Load demo emails' }))
    expect(await screen.findByRole('heading', { name: /urgent email/ })).toBeInTheDocument()
    expect(api.writes()).toEqual(['POST /demo/run'])
  })

  it('does not offer the demo outside demo mode', async () => {
    new FakeApi({ items: [], demoMode: false }).install()
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    expect(await screen.findByText('No emails analysed yet')).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Load demo emails' })).not.toBeInTheDocument())
  })

  it('explains an unreachable API and loads again on request', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    api.offline = true
    renderWithProviders(<Overview onOpenDrafts={() => {}} />)

    expect(await screen.findByText('Could not load the digest')).toBeInTheDocument()
    expect(screen.getByText('Could not reach the API.')).toBeInTheDocument()

    api.offline = false
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: /urgent email/ })).toBeInTheDocument()
  })
})
