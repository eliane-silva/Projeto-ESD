export default function MetricCard({ label, value, variant, showBar }) {
  const isRate = typeof value === 'number' && value % 1 !== 0
  const display = isRate ? `${(value * 100).toFixed(1)}%` : value
  const barWidth = isRate ? Math.min(value * 100, 100) : 0

  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className={`card-value ${variant || ''}`}>
        {display}
      </div>
      {showBar && isRate && (
        <div className="metric-bar">
          <div
            className={`metric-bar-fill ${variant || ''}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      )}
    </div>
  )
}
