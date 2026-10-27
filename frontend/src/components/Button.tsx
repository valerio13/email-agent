import type { ButtonHTMLAttributes } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'default' | 'primary'
}

const BASE =
  'inline-flex items-center justify-center gap-2 rounded-full px-[22px] py-[11px] text-sm font-bold shadow-raise-1 transition-shadow duration-200 enabled:active:shadow-press disabled:cursor-not-allowed disabled:bg-gray disabled:text-gray-ink disabled:shadow-none'

const VARIANTS = {
  default: 'bg-bg text-fg enabled:hover:shadow-raise-2',
  primary: 'bg-mint text-on-mint enabled:hover:shadow-[var(--raise-2),0_0_22px_var(--glow)]',
}

export function Button({ variant = 'default', className = '', ...props }: Props) {
  return <button className={`${BASE} ${VARIANTS[variant]} ${className}`} {...props} />
}
