// Senders arrive as "Name <address>". Either part can be missing.
export const nameOf = (sender: string) => sender.split('<')[0].trim() || sender
export const addressOf = (sender: string) => sender.match(/<([^>]+)>/)?.[1] ?? sender

const short = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})
const long = new Intl.DateTimeFormat('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})
const wholeDay = new Intl.DateTimeFormat('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
})

// Moments are shown in the viewer's timezone, for example "Mon, 09:14".
export const formatShort = (iso: string) => short.format(new Date(iso))
export const formatLong = (iso: string) => long.format(new Date(iso))
const weekday = new Intl.DateTimeFormat('en-GB', { weekday: 'short', timeZone: 'UTC' })

// "2026-10-26" as "Mon".
export const formatWeekday = (day: string) => weekday.format(new Date(`${day}T00:00:00Z`))

// The digest day is a UTC calendar day ("2026-10-26"), so it is shown as that same day.
export const formatDay = (day: string) => wholeDay.format(new Date(`${day}T00:00:00Z`))

// 126 minutes read as "2h 06m". Under an hour it is just minutes.
export function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return hours > 0 ? `${hours}h ${String(rest).padStart(2, '0')}m` : `${rest}m`
}
