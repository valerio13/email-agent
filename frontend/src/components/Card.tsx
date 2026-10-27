import type { HTMLAttributes, ReactNode } from 'react'

// A raised surface. Pass aria-label or aria-labelledby so it is announced as a region.
export function Card({ className = '', ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={`min-w-0 rounded-card bg-bg p-7 shadow-raise-2 max-[760px]:p-5 ${className}`}
      {...props}
    />
  )
}

// A sunken area inside a card, for text the reader only consumes.
export function Well({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`rounded-xl px-[18px] py-4 shadow-press ${className}`} {...props} />
}

// A small heading for a block inside a card, with an optional element on the right.
export function SectionLabel({ title, aside }: { title: string; aside?: ReactNode }) {
  return (
    <div className="mb-2.5 flex items-center justify-between gap-3">
      <h3>{title}</h3>
      {aside}
    </div>
  )
}
