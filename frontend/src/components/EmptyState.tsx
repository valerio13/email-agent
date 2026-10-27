import type { ReactNode } from 'react'
import { Card } from './Card'
import { Icon, type IconName } from './Icon'

// A card that says why there is nothing to show yet: loading, an error or no data.
export function EmptyState({
  icon,
  title,
  children,
  action,
}: {
  icon: IconName
  title: string
  children?: ReactNode
  action?: ReactNode
}) {
  return (
    <Card role="status">
      <div className="grid justify-items-center gap-3 px-3 py-9 text-center text-fg-muted">
        <Icon name={icon} size={22} />
        <h3 className="text-fg">{title}</h3>
        {children && <p className="max-w-[52ch]">{children}</p>}
        {action}
      </div>
    </Card>
  )
}
