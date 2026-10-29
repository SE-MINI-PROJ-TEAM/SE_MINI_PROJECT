import { Suspense } from 'react';
import { useAuth } from './auth/AuthContext.jsx';
import { slotItems } from './registry.js';

const Placeholder = () => <div className="card skeleton" style={{ height: 120 }} aria-hidden />;

/**
 * Renders every feature contribution registered for `name` (see registry.js).
 * `wrap` puts each contribution in a grid cell (used by the dashboards); `props` is passed to each component.
 */
export function Slot({ name, props = {}, wrap = false }) {
  const { user } = useAuth();
  const items = slotItems(name, user?.role);
  return items.map(({ id, feature, component: Component, span }) => {
    const content = (
      <Suspense fallback={<Placeholder />}>
        <Component {...props} />
      </Suspense>
    );
    return wrap ? (
      <div key={`${feature}:${id}`} className={span === 2 ? 'span-2' : ''}>
        {content}
      </div>
    ) : (
      <Suspense key={`${feature}:${id}`} fallback={null}>
        <Component {...props} />
      </Suspense>
    );
  });
}
