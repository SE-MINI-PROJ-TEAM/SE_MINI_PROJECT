/**
 * Client-side preview of the backend's rubric auto-normalisation (core/rubric.py): largest-remainder rounding to
 * cents so the shown weights always sum to exactly 100.00. The server result is authoritative.
 */
export function previewNormalized(rawWeights) {
  const weights = rawWeights.map((w) => Number(w));
  if (!weights.length || weights.some((w) => !(w > 0))) return null;
  const total = weights.reduce((a, b) => a + b, 0);
  const exactCents = weights.map((w) => (w / total) * 10000);
  const floored = exactCents.map(Math.floor);
  let leftover = 10000 - floored.reduce((a, b) => a + b, 0);
  exactCents
    .map((v, i) => [v - Math.floor(v), i])
    .sort((a, b) => b[0] - a[0])
    .forEach(([, i]) => {
      if (leftover > 0) {
        floored[i] += 1;
        leftover -= 1;
      }
    });
  return floored.map((c) => c / 100);
}
