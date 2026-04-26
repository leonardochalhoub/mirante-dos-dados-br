// "Powered by Apache Spark + Delta Lake + Claude Code" strip.
//
// Theme-aware logo swap is done via CSS, NOT useTheme(). Why: useTheme()
// uses per-instance React state. When the user toggles theme via the
// Layout switch, Layout's state updates but TechBadges instances keep
// their stale state — meaning logos didn't swap on theme toggle.
//
// CSS approach: render BOTH variants in DOM, hide the wrong one via
// `[data-theme="dark"]` selector on `<html>`. Layout's useEffect sets
// that attribute reliably.

const base       = import.meta.env.BASE_URL;
const sparkSrc   = `${base}spark-logo.svg`.replace(/\/{2,}/g, '/');
const deltaLight = `${base}delta-lake-logo-light.svg`.replace(/\/{2,}/g, '/');
const deltaDark  = `${base}delta-lake-logo-rev.svg`.replace(/\/{2,}/g, '/');
const claudeLight = `${base}claude-code-logo.svg`.replace(/\/{2,}/g, '/');
const claudeDark  = `${base}claude-code-logo-rev.svg`.replace(/\/{2,}/g, '/');

// Renders both variants; CSS shows the right one via [data-theme]
function ThemeImg({ light, dark, alt, height, className = '' }) {
  const style = height ? { height, width: 'auto' } : undefined;
  return (
    <>
      <img src={light}  alt={alt} className={`theme-img-light ${className}`.trim()} style={style} />
      <img src={dark}   alt={alt} className={`theme-img-dark  ${className}`.trim()} style={style} />
    </>
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
         title="Pipelines, infra e código construídos com Claude Code (Anthropic)">
        <ThemeImg light={claudeLight} dark={claudeDark} alt="Claude Code" />
      </a>
    </div>
  );
}

// Larger Delta logo for the Home hero.
export function DeltaLogoLarge({ height = 56 }) {
  return <ThemeImg light={deltaLight} dark={deltaDark} alt="Delta Lake" height={height} />;
}

// Larger Claude Code logo for the Home hero.
export function ClaudeLogoLarge({ height = 56 }) {
  return <ThemeImg light={claudeLight} dark={claudeDark} alt="Claude Code" height={height} />;
}
