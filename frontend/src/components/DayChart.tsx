import { Bar, BarChart, Cell, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import type { DailyCount } from '../api/client'
import { formatWeekday } from '../lib/format'
import { Well } from './Card'

// Emails per day. The newest day is drawn solid and glowing, the earlier ones fainter.
export function DayChart({ days }: { days: DailyCount[] }) {
  const data = days.map(({ day, emails }) => ({ label: formatWeekday(day), emails }))
  const description = data.map(({ label, emails }) => `${label} ${emails}`).join(', ')
  return (
    <Well className="px-4 pt-5 pb-3.5">
      <div role="img" aria-label={`Emails processed per day: ${description}`} className="h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 18, right: 4, bottom: 0, left: -8 }} style={{ overflow: 'visible' }}>
            <CartesianGrid vertical={false} strokeDasharray="4 4" stroke="var(--gray)" />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--fg-muted)', fontSize: 13, fontWeight: 600 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              width={34}
              tick={{ fill: 'var(--fg-muted)', fontSize: 12 }}
            />
            <Bar dataKey="emails" maxBarSize={44} radius={[4, 4, 0, 0]} isAnimationActive={false}>
              {data.map((entry, index) => {
                const latest = index === data.length - 1
                return (
                  <Cell
                    key={`${entry.label}-${index}`}
                    fill="var(--mint)"
                    fillOpacity={latest ? 1 : 0.55}
                    className={latest ? 'chart-bar-latest' : 'chart-bar'}
                  />
                )
              })}
              <LabelList dataKey="emails" position="top" fill="var(--fg)" fontSize={12} fontWeight={700} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Well>
  )
}
