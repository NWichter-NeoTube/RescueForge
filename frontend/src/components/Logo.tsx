export function Logo({ size = 36, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={className}
    >
      <defs>
        <linearGradient id="logo-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ef4444" />
          <stop offset="100%" stopColor="#b91c1c" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#logo-bg)" />
      {/* Shield shape */}
      <path
        d="M16 3 L27 8.5 V17 C27 23 22 28 16 29 C10 28 5 23 5 17 V8.5 Z"
        fill="white"
        opacity="0.12"
      />
      <path
        d="M16 5 L25 9.5 V17 C25 22 21 26.5 16 27.5 C11 26.5 7 22 7 17 V9.5 Z"
        fill="none"
        stroke="white"
        strokeWidth="1.3"
      />
      {/* 4-room floor plan inside shield */}
      <rect x="10" y="11" width="12" height="12" rx="0.5" fill="none" stroke="white" strokeWidth="1.4" />
      {/* Vertical center wall with door gap */}
      <line x1="16" y1="11" x2="16" y2="15" stroke="white" strokeWidth="1.2" />
      <line x1="16" y1="17" x2="16" y2="23" stroke="white" strokeWidth="1.2" />
      {/* Horizontal center wall with door gap */}
      <line x1="10" y1="17" x2="13.5" y2="17" stroke="white" strokeWidth="1.2" />
      <line x1="18.5" y1="17" x2="22" y2="17" stroke="white" strokeWidth="1.2" />
      {/* Door arcs */}
      <path d="M16 15 A2 2 0 0 1 14 17" fill="none" stroke="white" strokeWidth="0.7" opacity="0.6" />
      <path d="M16 17 A2 2 0 0 0 18.5 17" fill="none" stroke="white" strokeWidth="0.7" opacity="0.6" transform="translate(0.5,0)" />
    </svg>
  );
}
