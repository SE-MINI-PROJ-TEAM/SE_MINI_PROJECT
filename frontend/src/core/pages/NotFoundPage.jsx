import { Link } from 'react-router-dom';
import { Compass, ShieldAlert } from 'lucide-react';
import { EmptyState } from '../ui/index.js';

export function NotFoundPage() {
  return (
    <EmptyState title="Page not found" icon={Compass}>
      The page you are looking for does not exist. <Link to="/">Back to dashboard</Link>
    </EmptyState>
  );
}

export function ForbiddenPage() {
  return (
    <EmptyState title="You don't have access to this page" icon={ShieldAlert}>
      Your role does not permit this area. <Link to="/">Back to dashboard</Link>
    </EmptyState>
  );
}
