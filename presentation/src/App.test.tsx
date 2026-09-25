import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

describe('presentation controls', () => {
  beforeEach(() => window.history.replaceState(null, '', '/'))

  it('starts with the opening and advances with space', () => {
    render(<App />)
    expect(screen.getByText('click or press space to begin')).toBeInTheDocument()
    fireEvent.keyDown(window, { key: ' ' })
    expect(new URLSearchParams(window.location.search).get('act')).toBe('0')
  })

  it('supports deep links', () => {
    window.history.replaceState(null, '', '/?act=1&scene=0')
    render(<App />)
    expect(screen.getByText('Earn each handoff before the workflow runs')).toBeInTheDocument()
  })

  it('restarts from the brand control', () => {
    window.history.replaceState(null, '', '/?act=1&scene=0')
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Restart presentation' }))
    expect(window.location.search).toBe('')
  })

  it('has a fullscreen control', () => {
    Object.defineProperty(document.documentElement, 'requestFullscreen', { value: vi.fn(), configurable: true })
    window.history.replaceState(null, '', '/?act=0&scene=0')
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Toggle fullscreen' }))
    expect(document.documentElement.requestFullscreen).toHaveBeenCalled()
  })

  it('shows presenter guidance on demand', () => {
    window.history.replaceState(null, '', '/?act=0&scene=0')
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Toggle presenter prompt' }))
    expect(screen.getByText(/Open on the governance problem/)).toBeInTheDocument()
  })
})
