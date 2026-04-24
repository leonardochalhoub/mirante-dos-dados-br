// Small "Powered by Delta Lake + Apache Spark" strip used at the top of each vertical page.
// Reinforces the data-engineering positioning (pipeline-as-portfolio).

const deltaSrc = `${import.meta.env.BASE_URL}delta-lake-logo.svg`.replace(/\/{2,}/g, '/');
const sparkSrc = `${import.meta.env.BASE_URL}spark-logo.svg`.replace(/\/{2,}/g, '/');

export default function TechBadges() {
  return (
    <div className="tech-badges" aria-label="Stack de processamento">
      <span className="tech-badges-label">Pipeline:</span>
      <a href="https://spark.apache.org/" target="_blank" rel="noreferrer" title="Apache Spark">
        <img src={sparkSrc} alt="Apache Spark" />
      </a>
      <span className="tech-badges-sep">·</span>
      <a href="https://delta.io/" target="_blank" rel="noreferrer" title="Delta Lake">
        <img src={deltaSrc} alt="Delta Lake" />
      </a>
    </div>
  );
}
