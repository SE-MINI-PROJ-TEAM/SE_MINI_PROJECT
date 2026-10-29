import { useCallback, useEffect, useRef, useState } from 'react';

/** Run an async loader on mount / when deps change. Ignores results from superseded calls. */
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const run = useRef(0);

  const load = useCallback(
    async ({ silent = false } = {}) => {
      const id = ++run.current;
      if (!silent) setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const data = await loader();
        if (id === run.current) setState({ data, error: null, loading: false });
      } catch (error) {
        if (id === run.current) setState((s) => ({ data: silent ? s.data : null, error, loading: false }));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps,
  );

  useEffect(() => {
    load();
    return () => {
      run.current++;
    };
  }, [load]);

  return { ...state, reload: load, setData: (data) => setState((s) => ({ ...s, data })) };
}

export function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}
