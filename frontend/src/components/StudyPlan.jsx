export default function StudyPlan({ schedule = [], totalWeeks = 0 }) {
  if (!schedule.length) {
    return (
      <div className="studyplan-empty">
        No structured study plan available.
      </div>
    );
  }

  const weeks = totalWeeks || Math.max(...schedule.map(s => s.end_week || 0));

  return (
    <div className="studyplan-container">
      <h3 className="studyplan-title">Structured Study Plan</h3>

      
      <div className="studyplan-ruler">
        {Array.from({ length: weeks }, (_, i) => (
          <div key={i} className="ruler-cell">{i + 1}</div>
        ))}
      </div>

      
      <div className="studyplan-timeline">
        {schedule.map((item, idx) => {
          const span = (item.end_week - item.start_week + 1);
          const offset = (item.start_week - 1);

          return (
            <div key={idx} className="timeline-row">
              <div className="course-label">
                <div className="course-title">{item.title}</div>
                <div className={`course-badge ${item.difficulty.toLowerCase()}`}>
                  {item.difficulty}
                </div>
                <div className="course-meta">{item.weeks} weeks</div>
              </div>
              <div className="course-bar-wrapper">
                <div
                  className={`course-bar ${item.difficulty.toLowerCase()}`}
                  style={{
                    marginLeft: `${offset * 40}px`,
                    width: `${span * 40}px`
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
