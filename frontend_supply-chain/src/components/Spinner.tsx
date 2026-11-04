export function Spinner({ label, size = "medium" }: { label?: string; size?: "small" | "medium" | "large" }) {
  return (
    <span className={`loading-indicator loading-${size}`} role="status" aria-live="polite">
      <span className="loading-spinner" aria-hidden="true" />
      {label && <span>{label}</span>}
    </span>
  );
}
