import type { ButtonHTMLAttributes } from 'react'
import { DOT_COLORS, type DotTone } from '../lib/categories'

function TileContent({ label, value, tone }: { label: string; value: number | string; tone: DotTone }) {
  return (
    <>
      <span className="flex items-center gap-2 text-[13px] font-bold text-fg-muted">
        <span className={`size-2.5 flex-none rounded-full ${DOT_COLORS[tone]}`} />
        {label}
      </span>
      <span className="text-[38px] leading-none font-extrabold tracking-[-0.03em] tabular-nums max-[760px]:text-[32px]">
        {value}
      </span>
    </>
  )
}

// A figure with a label that acts as a button. Pressed (sunken) means its filter is active.
export function Tile({
  label,
  value,
  tone,
  pressed,
  ...props
}: Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-pressed'> & {
  label: string
  value: number
  tone: DotTone
  pressed?: boolean
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className="grid gap-2.5 rounded-tile bg-bg px-5 py-[18px] text-left shadow-raise-2 transition-shadow duration-200 hover:shadow-[var(--raise-2),0_0_0_2px_var(--ring)] aria-pressed:shadow-press aria-pressed:hover:shadow-press"
      {...props}
    >
      <TileContent label={label} value={value} tone={tone} />
    </button>
  )
}

// The same figure, only to read.
export function StatTile(props: { label: string; value: number | string; tone: DotTone }) {
  return (
    <div className="grid gap-2.5 rounded-tile bg-bg px-5 py-[18px] shadow-raise-2">
      <TileContent {...props} />
    </div>
  )
}
