// The text to show when an action fails. API errors carry the message the API sent.
export const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : 'Something failed.'
