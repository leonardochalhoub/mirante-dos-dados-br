// Small "Powered by Delta Lake + Apache Spark" strip used at the top of each vertical
// page (and stacked larger on the Home hero).
//
// Delta Lake SVG uses currentColor for the wordmark so it adapts to light/dark theme.
// We inline-fetch the SVG into the DOM (instead of <img>) so CSS color cascades into it.

import { useEffect, useRef, useState } from 'react';

const deltaSrc = `${import.meta.env.BASE_URL}delta-lake-logo.svg`.replace(/\/{2,}/g, '/');
const sparkSrc = `${import.meta.env.BASE_URL}spark-logo.svg`.replace(/\/{2,}/g, '/');

// Cache the SVG markup so we only fetch once per page load.
let deltaSvgPromise = null;
function loadDeltaSvg() {
  if (!deltaSvgPromise) {
    deltaSvgPromise = fetch(deltaSrc)
      .then((r) => r.text())
      .catch(() => null);
  }
  return deltaSvgPromise;
}

function DeltaLogo({ height = 22 }) {
  const ref = useRef(null);
  const [svg, setSvg] = useState(null);

  useEffect(() => {
    let alive = true;
    loadDeltaSvg().then((markup) => { if (alive) setSvg(markup); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!ref.current || !svg) return;
    ref.current.innerHTML = svg;
    const el = ref.current.querySelector('svg');
    if (!el) return;
    el.removeAttribute('width');
    el.setAttribute('height', String(height));
    el.style.height = `${height}px`;
    el.style.width = 'auto';
    el.style.display = 'block';
  }, [svg, height]);

  // Until SVG is fetched, render a sized placeholder to avoid layout shift.
  return (
    <span
      ref={ref}
      className="delta-logo"
      role="img"
      aria-label="Delta Lake"
      style={{ display: 'inline-block', height, lineHeight: 0 }}
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
    </div>
  );
}

// Reusable larger Delta + Spark stack for the Home hero.
export function DeltaLogoLarge({ height = 56 }) {
  return <DeltaLogo height={height} />;
}
