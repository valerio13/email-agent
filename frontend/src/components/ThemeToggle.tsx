import { useTheme } from '../lib/theme'
import { Button } from './Button'
import { Icon } from './Icon'

export function ThemeToggle() {
  const [theme, toggle] = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <Button onClick={toggle} aria-label={`Switch to ${next} theme`}>
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
      {theme === 'dark' ? 'Light' : 'Dark'}
    </Button>
  )
}
