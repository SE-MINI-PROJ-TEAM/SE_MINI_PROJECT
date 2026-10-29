import { describe, expect, it } from 'vitest';
import { previewNormalized } from './normalize.js';

const sum = (xs) => Math.round(xs.reduce((a, b) => a + b, 0) * 100) / 100;

describe('previewNormalized (mirrors backend rubric normalisation)', () => {
  it('always totals exactly 100', () => {
    [[1, 1, 1], [20, 30, 20, 30], [25, 25, 35], [7, 11, 13, 17, 19], [0.1, 0.2, 0.3]].forEach((raw) => {
      expect(sum(previewNormalized(raw))).toBe(100);
    });
  });

  it('keeps proportions', () => {
    expect(previewNormalized([1, 3])).toEqual([25, 75]);
  });

  it('gives the extra cent to the largest remainder like the server', () => {
    expect(previewNormalized([1, 1, 1])).toEqual([33.34, 33.33, 33.33]);
  });

  it('returns null for empty or non-positive weights', () => {
    expect(previewNormalized([])).toBeNull();
    expect(previewNormalized([0, 5])).toBeNull();
    expect(previewNormalized(['', 5])).toBeNull();
  });
});
