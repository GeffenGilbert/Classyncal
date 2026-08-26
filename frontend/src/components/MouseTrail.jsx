import { useEffect, useRef, useState } from "react";

import { useTheme } from "../theme";

// Minimum mouse-move distance (px) before a new cluster spawns.
const SPAWN_DISTANCE = 24;
// Number of squares spawned per cluster.
const CLUSTER_SIZE = 12;
// Max distance (px) a square can spawn from the cursor within a cluster.
const CLUSTER_RADIUS = 10;
// Cap on squares kept on screen at once, oldest are dropped first.
const MAX_SQUARES = 150;
// How long (ms) a square takes to fade out before it's removed.
const LIFETIME_MS = 900;
// Opacity (0-1) applied to every square's fill.
const SQUARE_OPACITY = 0.2;
// Gray tones (Tailwind slate RGB values) squares are randomly assigned for
// visual variation. Kept as raw RGB, not Tailwind classes, so SQUARE_OPACITY
// can be applied dynamically via inline style. The squares are translucent
// fills, so the set has to invert with the theme - slate 300-500 reads against
// a light page and disappears against a near-black one.
const GRAY_SHADES_RGB = {
  light: ["203, 213, 225", "148, 163, 184", "100, 116, 139"],
  dark: ["148, 163, 184", "203, 213, 225", "226, 232, 240"],
};
// Smallest a square can be (px).
const MIN_SQUARE_SIZE = 2;
// Largest a square can be (px), on top of MIN_SQUARE_SIZE.
const MAX_SQUARE_SIZE_ADD = 4;
// How far (px) a square drifts, in a random direction, as it fades out.
const DRIFT_DISTANCE = 6;

// Monotonically increasing id used as the React key for each square.
let nextSquareId = 0;

function MouseTrail() {
  const [squares, setSquares] = useState([]);
  const lastPos = useRef(null);
  const { theme } = useTheme();

  useEffect(() => {
    const shades = GRAY_SHADES_RGB[theme];

    function handleMouseMove(event) {
      const { clientX: x, clientY: y } = event;
      const last = lastPos.current;

      if (last) {
        const dx = x - last.x;
        const dy = y - last.y;
        if (dx * dx + dy * dy < SPAWN_DISTANCE * SPAWN_DISTANCE) return;
      }
      lastPos.current = { x, y };

      const cluster = Array.from({ length: CLUSTER_SIZE }, () => {
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * CLUSTER_RADIUS;
        const driftAngle = Math.random() * Math.PI * 2;
        return {
          id: nextSquareId++,
          x: x + Math.cos(angle) * radius,
          y: y + Math.sin(angle) * radius,
          size: MIN_SQUARE_SIZE + Math.random() * MAX_SQUARE_SIZE_ADD,
          shadeRgb: shades[Math.floor(Math.random() * shades.length)],
          driftX: Math.cos(driftAngle) * DRIFT_DISTANCE,
          driftY: Math.sin(driftAngle) * DRIFT_DISTANCE,
        };
      });

      setSquares((prev) => [...prev.slice(-(MAX_SQUARES - cluster.length)), ...cluster]);

      const clusterIds = new Set(cluster.map((square) => square.id));
      setTimeout(() => {
        setSquares((prev) => prev.filter((square) => !clusterIds.has(square.id)));
      }, LIFETIME_MS);
    }

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [theme]);

  return (
    <div className="pointer-events-none fixed inset-0 z-10 overflow-hidden">
      {squares.map((square) => (
        <span
          key={square.id}
          className="absolute"
          style={{
            left: square.x,
            top: square.y,
            width: square.size,
            height: square.size,
            backgroundColor: `rgba(${square.shadeRgb}, ${SQUARE_OPACITY})`,
            "--drift-x": `${square.driftX}px`,
            "--drift-y": `${square.driftY}px`,
            animation: "fade-out-square 0.9s ease-out forwards",
          }}
        />
      ))}
    </div>
  );
}

export default MouseTrail;
