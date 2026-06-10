import React from 'react'

export default function Topbar({ title }: { title: string }) {
  return (
    <header className="topbar">
      <div>
        <p className="topbar-badge">Clinical DDI Analytics</p>
        <h1 className="topbar-title">{title}</h1>
      </div>
    </header>
  )
}
