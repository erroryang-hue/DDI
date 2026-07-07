import { NavLink } from 'react-router-dom'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/analysis', label: 'Interaction Analysis' },
  { to: '/polypharmacy', label: 'Polypharmacy' },
  { to: '/search', label: 'Drug Search' },
  { to: '/graph', label: 'Graph Explorer' },
  { to: '/recommendations', label: 'Recommendations' },
  { to: '/analytics', label: 'Analytics' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">DDI Intelligence</div>
      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
