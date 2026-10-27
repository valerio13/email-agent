import type { ButtonHTMLAttributes, ReactNode } from 'react'
import type { Tone } from '../lib/categories'
import { Icon, type IconName } from './Icon'

export type ChipVariant = 'default' | Tone | 'ready' | 'ai' | 'done' | 'muted'

const BASE =
  'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-[13px] py-[5px] text-[13px] font-bold'

const VARIANTS: Record<ChipVariant, string> = {
  default: 'bg-bg text-fg shadow-raise-1',
  urgent: 'bg-rose text-on-rose shadow-raise-1',
  reply: 'bg-amber text-on-amber shadow-raise-1',
  info: 'bg-gray text-fg shadow-raise-1',
  ready: 'bg-mint text-on-mint shadow-raise-1',
  ai: 'bg-ai text-on-ai shadow-raise-1',
  done: 'bg-bg text-mint-ink shadow-press',
  muted: 'bg-bg text-fg-muted shadow-press',
}

// A small label. Not interactive: for a toggle use FilterChip.
export function Chip({
  variant = 'default',
  icon,
  children,
}: {
  variant?: ChipVariant
  icon?: IconName
  children: ReactNode
}) {
  return (
    <span className={`${BASE} ${VARIANTS[variant]}`}>
      {icon && <Icon name={icon} />}
      {children}
    </span>
  )
}

// A chip that turns a filter on or off. aria-pressed tells which state it is in.
export function FilterChip({
  pressed,
  count,
  children,
  ...props
}: Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-pressed'> & {
  pressed: boolean
  count: number
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className={`${BASE} bg-bg px-4 py-2 text-fg shadow-raise-1 transition-shadow duration-200 hover:shadow-raise-2 aria-pressed:bg-mint aria-pressed:text-on-mint`}
      {...props}
    >
      {children} <span className="tabular-nums opacity-80">{count}</span>
    </button>
  )
}
