import React from "react";

const COLORS = [
  "rgb(66,135,245)",  
  "rgb(255,99,132)",  
  "rgb(54,203,137)",  
  "rgb(255,159,64)",  
  "rgb(153,102,255)", 
  "rgb(255,205,86)",  
  "rgb(90,200,250)",  
  "rgb(255,140,180)", 
];

const GAP_DEGREES = 1.5; 

function buildColorMap(schedule) {
  const map = new Map();
  let i = 0;
  for (const s of schedule) {
    if (!map.has(s.course_id)) {
      map.set(s.course_id, COLORS[i % COLORS.length]);
      i++;
    }
  }
  return map;
}

function donutArcPath(cx, cy, rOuter, rInner, startAngle, endAngle) {
  const toRad = a => (Math.PI / 180) * a;
  const x0 = cx + rOuter * Math.cos(toRad(startAngle));
  const y0 = cy + rOuter * Math.sin(toRad(startAngle));
  const x1 = cx + rOuter * Math.cos(toRad(endAngle));
  const y1 = cy + rOuter * Math.sin(toRad(endAngle));
  const x2 = cx + rInner * Math.cos(toRad(endAngle));
  const y2 = cy + rInner * Math.sin(toRad(endAngle));
  const x3 = cx + rInner * Math.cos(toRad(startAngle));
  const y3 = cy + rInner * Math.sin(toRad(startAngle));
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return [
    `M${x0},${y0}`,
    `A${rOuter},${rOuter} 0 ${largeArc} 1 ${x1},${y1}`,
    `L${x2},${y2}`,
    `A${rInner},${rInner} 0 ${largeArc} 0 ${x3},${y3}`,
    "Z"
  ].join(" ");
}

function createMiniSlices(schedule, totalWeeks) {
  const slices = [];
  let currentAngle = -90;
  schedule.forEach(course => {
    const weeksCount = course.end_week - course.start_week + 1;
    const totalDegrees = 360 * (weeksCount / totalWeeks);
    const sliceDegrees = (totalDegrees - GAP_DEGREES * (weeksCount - 1)) / weeksCount;

    for (let i = 0; i < weeksCount; i++) {
      const sliceStart = currentAngle + i * (sliceDegrees + GAP_DEGREES);
      const sliceEnd = sliceStart + sliceDegrees;
      slices.push({
        course_id: course.course_id,
        title: course.title,
        difficulty: course.difficulty,
        startAngle: sliceStart,
        endAngle: sliceEnd,
      });
    }
    currentAngle += totalDegrees;
  });
  return slices;
}

export default function PieTimeline({ schedule = [], totalWeeks = 0 }) {
  if (!schedule.length || !totalWeeks) {
    return <div className="donut-empty">No structured timeline available.</div>;
  }

  const colorMap = buildColorMap(schedule);
  const miniSlices = createMiniSlices(schedule, totalWeeks);

  return (
    <div className="donut-flex-wrap">
      <div className="donut-container-3d">
        <svg
          viewBox="0 0 320 320"
          width="320"
          height="320"
          className="donut-svg-3d"
        >
          
          {miniSlices.map((slice, i) => (
            <path
              key={`${slice.course_id}-${i}`}
              d={donutArcPath(160, 160, 120, 70, slice.startAngle, slice.endAngle)}
              fill={colorMap.get(slice.course_id)}
              stroke="#22243c"
              strokeWidth="1.7"
              style={{ filter: "drop-shadow(0 6px 16px rgba(40,30,60,0.24))" }}
            />
          ))}
          
          <circle cx="160" cy="160" r="70" fill="#181837" />
          
          <text
            x={160}
            y={150}
            textAnchor="middle"
            fontSize="2.9em"
            fontWeight="900"
            fill="#ecedfc"
            style={{ textShadow: "0 2px 16px #7160e0cc" }}
          >
            {totalWeeks}
          </text>
          <text
            x={160}
            y={178}
            textAnchor="middle"
            fontSize="1.13em"
            fontWeight="800"
            fill="#cce0ff"
          >
            Total weeks
          </text>
        </svg>
      </div>
      <div className="donut-legend-3d">
        {schedule.map((item) => (
          <div key={item.course_id} className="donut-legend-row-3d">
            <span className="donut-swatch-3d"
              style={{ background: colorMap.get(item.course_id) }} />
            <div>
              <div className="donut-legend-title-3d">{item.title}</div>
              <div className="donut-legend-sub-3d">{item.difficulty} — {item.end_week - item.start_week + 1} Weeks</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
