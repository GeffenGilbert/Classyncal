const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAY_LABELS = { Monday: "M", Tuesday: "T", Wednesday: "W", Thursday: "T", Friday: "F", Saturday: "S", Sunday: "S" };

function DaysOfWeekPicker({ value = [], onChange }) {
  function toggleDay(day) {
    onChange(value.includes(day) ? value.filter((d) => d !== day) : [...value, day]);
  }

  return (
    <div className="flex gap-1">
      {DAYS.map((day) => {
        const active = value.includes(day);
        return (
          <button
            key={day}
            type="button"
            onClick={() => toggleDay(day)}
            title={day}
            className={`flex h-6 w-6 items-center justify-center rounded-full text-xs transition-colors ${
              active
                ? "bg-indigo-500 text-white"
                : "bg-slate-100 text-slate-400 hover:bg-slate-200"
            }`}
          >
            {DAY_LABELS[day]}
          </button>
        );
      })}
    </div>
  );
}

export default DaysOfWeekPicker;
