/**
 * Feature registry.
 *
 * Every folder in src/features/ that has a manifest.js is discovered at build time. A manifest declares:
 *   id      unique feature id
 *   routes  [{ path, component, roles?, layout?: 'app'|'bare', allowTemp?, nav?: { label, icon, section, order, useBadge? } }]
 *   slots   { [slotName]: [{ id, component, roles?, order?, span? }] }   (widgets other pages render with <Slot />)
 *
 * Adding or removing a story is therefore just adding / removing its folder - no shared file changes.
 */
const modules = import.meta.glob('../features/*/manifest.js', { eager: true });

export const features = Object.values(modules)
  .map((m) => m.default)
  .filter(Boolean);

export const routes = features.flatMap((f) => (f.routes || []).map((r) => ({ ...r, feature: f.id })));

const allowed = (item, role) => !item.roles || item.roles.includes(role);

export function navSections(role) {
  const items = routes.filter((r) => r.nav && allowed(r, role));
  const sections = new Map();
  items
    .sort((a, b) => (a.nav.order ?? 50) - (b.nav.order ?? 50))
    .forEach((r) => {
      const name = r.nav.section || 'General';
      if (!sections.has(name)) sections.set(name, []);
      sections.get(name).push(r);
    });
  return [...sections.entries()].map(([name, list]) => ({ name, items: list }));
}

export function slotItems(slot, role) {
  return features
    .flatMap((f) => (f.slots?.[slot] || []).map((item) => ({ ...item, feature: f.id })))
    .filter((item) => allowed(item, role))
    .sort((a, b) => (a.order ?? 50) - (b.order ?? 50));
}
