import { forwardRef } from 'react'
import type { DigestItem } from '../api/client'
import { AiCard } from './AiCard'
import { EmailCard } from './EmailCard'

// The email and its analysis, side by side with the inbox. On wide screens it stays in view and
// scrolls on its own. The negative margins leave room for the card shadows, which an overflow
// container would otherwise cut off.
export const EmailDetail = forwardRef<HTMLDivElement, { item: DigestItem }>(({ item }, ref) => (
  <div
    ref={ref}
    className="sticky top-1.5 -mt-3.5 -mr-3 -mb-10 -ml-[34px] grid max-h-[calc(100vh+14px)] gap-7 overflow-y-auto pt-3.5 pr-3 pb-10 pl-[34px] [scrollbar-width:thin] max-[1040px]:static max-[1040px]:m-0 max-[1040px]:max-h-none max-[1040px]:overflow-visible max-[1040px]:p-0"
  >
    <EmailCard email={item.email} />
    <AiCard item={item} />
  </div>
))
