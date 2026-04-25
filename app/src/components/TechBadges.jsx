// "Powered by Apache Spark + Delta Lake" strip.
// Used in two places:
//   - inline next to DownloadActions on each vertical page (compact pill)
//   - large two-card stack on the Home hero
//
// Theme-aware Delta logo: we ship two variants of the official asset (one with
// dark wordmark for light bg, one with white wordmark for dark bg) and swap via
// the useTheme hook. Cleaner than CSS color hacks on inline-injected SVG.

import { useTheme } from '../hooks/useTheme';

const base       = import.meta.env.BASE_URL;
const sparkSrc   = `${base}spark-logo.svg`.replace(/\/{2,}/g, '/');
const deltaLight = `${base}delta-lake-logo-light.svg`.replace(/\/{2,}/g, '/');
const deltaDark  = `${base}delta-lake-logo-rev.svg`.replace(/\/{2,}/g, '/');
const claudeSrc  = `${base}claude-code-logo.svg`.replace(/\/{2,}/g, '/');

function DeltaLogo({ className, height }) {
  const { theme } = useTheme();
  const src = theme === 'dark' ? deltaDark : deltaLight;
  return (
    <img
      src={src}
      alt="Delta Lake"
      className={className}
      style={height ? { height, width: 'auto' } : undefined}
    />
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
        <DeltaLogo />
      </a>
      <span className="tech-badges-sep">·</span>
      <a href="https://www.anthropic.com/claude-code" target="_blank" rel="noreferrer"
         title="Pipelines, infra e código construídos com Claude Code (Anthropic)">
        <img src={claudeSrc} alt="Claude Code" />
      </a>
    </div>
  );
}

// Larger Delta logo for the Home hero. Same theme switch under the hood.
export function DeltaLogoLarge({ height = 56 }) {
  return <DeltaLogo height={height} />;
}
