import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { FakeApi } from '../test/fakeApi'
import { renderWithProviders } from '../test/render'
import { Drafts } from './Drafts'

describe('Drafts', () => {
  it('lists the pending drafts next to the email they answer, most urgent first', async () => {
    new FakeApi().install()
    renderWithProviders(<Drafts />)

    expect(await screen.findByRole('heading', { name: '2 drafts waiting for you' })).toBeInTheDocument()
    const cards = screen.getAllByRole('article')
    expect(cards.map((card) => card.getAttribute('aria-label'))).toEqual([
      'Draft for Production API is down',
      'Draft for Quote for the Q4 website redesign',
    ])
    expect(within(cards[0]).getByRole('textbox')).toHaveValue('Hi Marcus,\n\nThanks for your message.')
  })

  it('saves the text when the box loses focus, so an edit survives moving on', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    const textbox = within(card).getByRole('textbox')
    await user.clear(textbox)
    await user.type(textbox, 'On it, calling you now.')
    await user.tab()

    await waitFor(() => expect(api.items[0].draft?.body).toBe('On it, calling you now.'))
    expect(api.writes()).toEqual(['PATCH /drafts/1'])
  })

  it('saves the edited text before approving, then confirms that nothing was sent', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    // fireEvent changes the text without moving focus, so only approving can save it.
    fireEvent.change(within(card).getByRole('textbox'), { target: { value: 'On it, calling you now.' } })
    await user.click(within(card).getByRole('button', { name: 'Approve and create draft' }))

    expect(await screen.findByText('Draft for "Production API is down" created in the mailbox. Nothing was sent.')).toBeInTheDocument()
    // The text is saved first, so the mailbox gets what the reviewer wrote.
    const writes = api.writes()
    expect(writes.indexOf('PATCH /drafts/1')).toBeGreaterThanOrEqual(0)
    expect(writes.indexOf('PATCH /drafts/1')).toBeLessThan(writes.indexOf('POST /drafts/1/approve'))
    expect(api.items[0].draft?.body).toBe('On it, calling you now.')
    // The card leaves the pending list and appears under Reviewed.
    expect(await screen.findByRole('heading', { name: '1 draft waiting for you' })).toBeInTheDocument()
    const reviewed = screen.getByRole('region', { name: 'Reviewed' })
    expect(within(reviewed).getByText('In mailbox')).toBeInTheDocument()
  })

  it('does not save anything when the text was not edited', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    await user.click(within(card).getByRole('button', { name: 'Approve and create draft' }))
    await screen.findByText(/created in the mailbox/)
    expect(api.writes()).toEqual(['POST /drafts/1/approve'])
  })

  it('discards a draft and says so', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[1]
    await user.click(within(card).getByRole('button', { name: 'Discard' }))

    expect(await screen.findByText('Draft for "Quote for the Q4 website redesign" discarded.')).toBeInTheDocument()
    expect(api.writes()).toEqual(['POST /drafts/2/discard'])
    expect(within(screen.getByRole('region', { name: 'Reviewed' })).getByText('Discarded')).toBeInTheDocument()
  })

  it('undoes a discard from the Reviewed list and brings the draft back as it was', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[1]
    await user.click(within(card).getByRole('button', { name: 'Discard' }))
    const reviewed = await screen.findByRole('region', { name: 'Reviewed' })

    await user.click(within(reviewed).getByRole('button', { name: 'Undo discard' }))

    expect(
      await screen.findByText('Draft for "Quote for the Q4 website redesign" is back in review.'),
    ).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: '2 drafts waiting for you' })).toBeInTheDocument()
    expect(api.writes()).toEqual(['POST /drafts/2/discard', 'POST /drafts/2/restore'])
    const restored = screen.getAllByRole('article')[1]
    expect(within(restored).getByRole('textbox')).toHaveValue('Hi Priya,\n\nThanks for reaching out.')
  })

  it('offers no undo for an approved draft', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    await user.click(within(card).getByRole('button', { name: 'Approve and create draft' }))
    const reviewed = await screen.findByRole('region', { name: 'Reviewed' })

    expect(within(reviewed).getByText('In mailbox')).toBeInTheDocument()
    expect(within(reviewed).queryByRole('button', { name: 'Undo discard' })).not.toBeInTheDocument()
  })

  it('shows the API message when the draft changed meanwhile, and refreshes', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[1]
    await user.click(within(card).getByRole('button', { name: 'Discard' }))
    const reviewed = await screen.findByRole('region', { name: 'Reviewed' })
    api.decideBehindTheScenes(2, 'approved')

    await user.click(within(reviewed).getByRole('button', { name: 'Undo discard' }))

    expect(await screen.findByText('Draft 2 is not discarded (it is approved).')).toBeInTheDocument()
    await waitFor(() =>
      expect(
        within(screen.getByRole('region', { name: 'Reviewed' })).queryByRole('button', { name: 'Undo discard' }),
      ).not.toBeInTheDocument(),
    )
  })

  it('cannot approve an empty draft', async () => {
    const user = userEvent.setup()
    new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    await user.clear(within(card).getByRole('textbox'))
    expect(within(card).getByRole('button', { name: 'Approve and create draft' })).toBeDisabled()
  })

  it('shows the API message and refreshes when the draft was decided elsewhere', async () => {
    const user = userEvent.setup()
    const api = new FakeApi().install()
    renderWithProviders(<Drafts />)

    const card = (await screen.findAllByRole('article'))[0]
    api.decideBehindTheScenes(1, 'approved')
    await user.click(within(card).getByRole('button', { name: 'Approve and create draft' }))

    expect(await screen.findByText('Draft 1 is already approved.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getAllByRole('article')).toHaveLength(1))
  })

  it('says everything is reviewed when no draft is left', async () => {
    new FakeApi({ items: [] }).install()
    renderWithProviders(<Drafts />)

    expect(await screen.findByRole('heading', { name: 'No drafts waiting' })).toBeInTheDocument()
    expect(screen.getByText('All caught up')).toBeInTheDocument()
  })
})
