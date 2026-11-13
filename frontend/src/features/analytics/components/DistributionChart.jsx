/** Grade bracket histogram (A-F). Pure CSS bars with value labels and a text alternative. */
export default function DistributionChart({ distribution }) {
  const letters = Object.keys(distribution);
  const max = Math.max(1, ...Object.values(distribution));
  const summary = letters.map((l) => `${l}: ${distribution[l]}`).join(', ');
  return (
    <div className="bars" role="img" aria-label={`Grade distribution. ${summary}`}>
      {letters.map((letter) => (
        <div className="bars__col" key={letter}>
          <span className="bars__value">{distribution[letter]}</span>
          <div className={`bars__bar ${letter === 'F' ? 'is-low' : ''}`} style={{ height: `${(distribution[letter] / max) * 100}%` }} />
          <span className="bars__label">{letter}</span>
        </div>
      ))}
    </div>
  );
}
