import { Link } from 'react-router-dom'
import Card from '../components/Card'

export default function NotFound() {
  return (
    <Card>
      <div className="not-found">
        <h2>Page not found</h2>
        <p>The page you are looking for does not exist.</p>
        <Link to="/dashboard" className="button secondary">
          Go to Dashboard
        </Link>
      </div>
    </Card>
  )
}
