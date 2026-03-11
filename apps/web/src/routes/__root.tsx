import { createRootRoute, Outlet } from '@tanstack/react-router'

export const rootRoute = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Firm-level supply chains</p>
          <h1>Australian, Chinese, and US firm link explorer</h1>
        </div>
        <p className="subtitle">
          Real downloaded-source evidence, explicit links, undisclosed placeholders, and ranked candidate hints.
        </p>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
