import '@testing-library/jest-dom/vitest'
import { cleanup, configure } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// The first visit to Metrics loads Recharts, which takes a few seconds the first time.
configure({ asyncUtilTimeout: 8000 })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  localStorage.clear()
  delete document.documentElement.dataset.theme
})

// jsdom has no layout, so these browser features are stubbed with the minimum the app needs.
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub

Element.prototype.scrollIntoView = () => {}

// axe-core asks for a canvas to measure colors. jsdom has none and only warns, so say there is none.
HTMLCanvasElement.prototype.getContext = () => null
