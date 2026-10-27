import type { Priority } from '../api/client'
import { PRIORITY_LABEL, PRIORITY_LEVEL } from '../lib/categories'

const HEIGHTS = ['h-[7px]', 'h-[13px]', 'h-[19px]']

// Three bars that fill up with the priority, like a signal meter.
export function PriorityBars({ priority }: { priority: Priority }) {
  const level = PRIORITY_LEVEL[priority]
  return (
    <span
      className="mt-0.5 inline-flex h-5 items-end gap-[3px]"
      role="img"
      aria-label={PRIORITY_LABEL[priority]}
    >
      {HEIGHTS.map((height, index) => (
        <span key={height} className={`w-[5px] ${height} ${index < level ? 'bg-fg' : 'bg-gray'}`} />
      ))}
    </span>
  )
}
