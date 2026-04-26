// "Powered by Apache Spark + Delta Lake + Claude Code" strip.
// Used in two places:
//   - inline next to DownloadActions on each vertical page (compact pill)
//   - large logo cards on the Home hero
//
// Theme-aware: cada logo cuja wordmark é texto colorido tem 2 variantes
// (light bg / dark bg) e troca via useTheme. O símbolo do Spark é
// monocromático colorido (laranja), funciona em ambos os modos.

import { useTheme } from '../hooks/useTheme';

const base       = import.meta.env.BASE_URL;
const sparkSrc   = `${base}spark-logo.svg`.replace(/\/{2,}/g, '/');
const deltaLight = `${base}delta-lake-logo-light.svg`.replace(/\/{2,}/g, '/');
const deltaDark  = `${base}delta-lake-logo-rev.svg`.replace(/\/{2,}/g, '/');
const claudeLight = `${base}claude-code-logo.svg`.replace(/\/{2,}/g, '/');
const claudeDark  = `${base}claude-code-logo-rev.svg`.replace(/\/{2,}/g, '/');

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

function ClaudeLogo({ className, height }) {
  const { theme } = useTheme();
  const src = theme === 'dark' ? claudeDark : claudeLight;
  return (
    <img
      src={src}
      alt="Claude Code"
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
        <ClaudeLogo />
      </a>
    </div>
  );
}

// Larger Delta logo for the Home hero. Same theme switch under the hood.
export function DeltaLogoLarge({ height = 56 }) {
  return <DeltaLogo height={height} />;
}

// Larger Claude Code logo for the Home hero.
export function ClaudeLogoLarge({ height = 56 }) {
  return <ClaudeLogo height={height} />;
}
