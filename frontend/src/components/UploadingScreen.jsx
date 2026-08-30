import { useEffect, useState } from "react";
import { FileSearch } from "lucide-react";

// No real progress signal exists (a single blocking backend call), so these
// rotate on a timer to show the wait is active rather than faking a percent.
const PROCESSING_MESSAGES = [
  "Reading your syllabus...",
  "Finding your class schedule...",
  "Looking for exams and assignments...",
  "Sorting out readings and due dates...",
  "Almost done organizing everything...",
];

function formatElapsed(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function UploadingScreen({ fileName }) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const tick = setInterval(() => setElapsedSeconds((seconds) => seconds + 1), 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let timeoutId;
    let index = 0;

    function scheduleNext() {
      if (index >= PROCESSING_MESSAGES.length - 1) return;
      // Randomized so the cadence doesn't read as a mechanical fixed tick.
      const delay = 12000 + Math.random() * 6000;
      timeoutId = setTimeout(() => {
        index += 1;
        setMessageIndex(index);
        scheduleNext();
      }, delay);
    }

    scheduleNext();
    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="flex w-full max-w-xl flex-col items-center gap-4 rounded-2xl border-2 border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 px-10 py-16 text-center">
      <div className="relative flex h-16 w-16 items-center justify-center">
        {/* dark:border-slate-800 and border-t-indigo-500 have equal specificity - the
            dark variant is :where()-based, which adds none - so the dark rule lands
            later in the sheet and repaints the top border too, leaving a uniform ring
            that spins invisibly. The dark top colour has to be restated to win. */}
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-slate-200 dark:border-slate-800 border-t-indigo-500 dark:border-t-indigo-400" />
        <FileSearch className="h-7 w-7 text-indigo-500" />
      </div>

      <div>
        <p className="font-medium text-slate-900 dark:text-slate-50">
          {fileName ? `Processing ${fileName}` : "Processing your syllabus"}
        </p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{PROCESSING_MESSAGES[messageIndex]}</p>
      </div>

      <p className="text-xs text-slate-400 dark:text-slate-400">
        {formatElapsed(elapsedSeconds)} elapsed &middot; longer syllabi can take a minute or more
      </p>
    </div>
  );
}

export default UploadingScreen;
