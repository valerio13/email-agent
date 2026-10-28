export type TabId = 'overview' | 'drafts' | 'metrics'

export const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'drafts', label: 'Drafts' },
  { id: 'metrics', label: 'Metrics' },
]

// The id of the panel the tabs control, and of the tab that labels it.
export const PANEL_ID = 'tabpanel'
export const tabElementId = (tab: TabId) => `tab-${tab}`
