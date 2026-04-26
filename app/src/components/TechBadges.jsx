// "Powered by Apache Spark + Delta Lake + Claude Code" strip.
//
// Claude logo: inline SVG (asterisk) + HTML <span> wordmark using
// CSS variables for color. Bulletproof — no font rendering issues
// inside <img src=svg>, no theme-state propagation issues.
//
// Delta logo: still uses the official .svg files (light + rev). Swap
// is CSS-driven (`[data-theme]` selector on <html>) — no JS state.

const base       = import.meta.env.BASE_URL;
const sparkSrc   = `${base}spark-logo.svg`.replace(/\/{2,}/g, '/');
const deltaLight = `${base}delta-lake-logo-light.svg`.replace(/\/{2,}/g, '/');
const deltaDark  = `${base}delta-lake-logo-rev.svg`.replace(/\/{2,}/g, '/');

// Renders both light + dark variants; CSS hides the wrong one based on
// data-theme attribute on <html>. Used for Delta which has 2 .svg files.
function ThemeImg({ light, dark, alt, height }) {
  const style = height ? { height, width: 'auto' } : undefined;
  return (
    <>
      <img src={light} alt={alt} className="theme-img-light" style={style} />
      <img src={dark}  alt={alt} className="theme-img-dark"  style={style} />
    </>
  );
}

// Inline Claude Code logo. Asterisk in brand orange, wordmark uses
// `color: var(--text)` so it auto-adapts to light/dark theme.
function ClaudeCodeMark({ height = 40 }) {
  // Aspect ratio 220:50 = 4.4:1. Render as flex row.
  return (
    <span
      className="claude-mark"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        height,
        lineHeight: 1,
      }}
    >
      <svg
        width={height * 0.55}
        height={height * 0.55}
        viewBox="-15 -15 30 30"
        aria-hidden="true"
        style={{ display: 'block', flexShrink: 0 }}
      >
        <g stroke="#D97757" strokeWidth="3" strokeLinecap="round" fill="none">
          <line x1="0"     y1="-12" x2="0"    y2="12"  />
          <line x1="-10.4" y1="-6"  x2="10.4" y2="6"   />
          <line x1="-10.4" y1="6"   x2="10.4" y2="-6"  />
        </g>
      </svg>
      <span
        style={{
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: height * 0.42,
          fontWeight: 700,
          color: 'var(--text)',
          letterSpacing: '-0.01em',
          whiteSpace: 'nowrap',
        }}
      >
        Claude Code
      </span>
    </span>
  );
}

export default function TechBadges() {
  return (
    <div className="tech-badges" aria-label="Stack de processamento">
      <span className="tech-badges-label">Pipeline:</span>
      <a href="https://spark.apache.org/" target="_blank" rel="noreferrer" title="Apache Spark">
        <img src={sparkSrc} alt="Apache Spark" />
      </a>
      <span className="tech-badges-sep">·</span>
      <a href="https://delta.io/" target="_blank" rel="noreferrer" title="Delta Lake">
        <ThemeImg light={deltaLight} dark={deltaDark} alt="Delta Lake" />
      </a>
      <span className="tech-badges-sep">·</span>
      <a href="https://www.anthropic.com/claude-code" target="_blank" rel="noreferrer"
         title="Pipelines, infra e código construídos com Claude Code (Anthropic)"
         style={{ color: 'inherit', textDecoration: 'none' }}>
        <ClaudeCodeMark height={40} />
      </a>
    </div>
  );
}

// Larger Delta logo for the Home hero.
export function DeltaLogoLarge({ height = 56 }) {
  return <ThemeImg light={deltaLight} dark={deltaDark} alt="Delta Lake" height={height} />;
}

// Larger Claude Code mark for the Home hero.
export function ClaudeLogoLarge({ height = 56 }) {
  return <ClaudeCodeMark height={height} />;
}
