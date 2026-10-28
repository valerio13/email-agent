import type { Category, Priority } from '../api/client'
import type { IconName } from '../components/Icon'

// How the color of a chip or a dot reads: the same names are used by Chip and Tile.
export type Tone = 'urgent' | 'reply' | 'info'

export const CATEGORIES: Record<Category, { label: string; tone: Tone; icon: IconName }> = {
  urgent: { label: 'Urgent', tone: 'urgent', icon: 'bolt' },
  needs_reply: { label: 'Needs reply', tone: 'reply', icon: 'reply' },
  informational: { label: 'Informational', tone: 'info', icon: 'info' },
}

export const PRIORITY_LABEL: Record<Priority, string> = {
  high: 'High priority',
  medium: 'Medium priority',
  low: 'Low priority',
}

// Number of filled bars in the priority indicator.
export const PRIORITY_LEVEL: Record<Priority, 1 | 2 | 3> = { low: 1, medium: 2, high: 3 }

// The colored dots of the tiles and the mix bar. 'ready' marks drafts waiting for a decision.
export type DotTone = Tone | 'ready'

export const DOT_COLORS: Record<DotTone, string> = {
  urgent: 'bg-rose',
  reply: 'bg-amber',
  info: 'bg-gray',
  ready: 'bg-mint',
}
