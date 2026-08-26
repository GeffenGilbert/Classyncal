import { CALENDAR_COLORS, DEFAULT_COLOR_ID } from "./colorPickerConfig";

function ColorPicker({ value, onChange }) {
  const selected =
    CALENDAR_COLORS.find((color) => color.id === value) ??
    CALENDAR_COLORS.find((color) => color.id === DEFAULT_COLOR_ID);

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className="flex w-full max-w-md items-center justify-center rounded-2xl p-10 transition-colors duration-200"
        style={{ backgroundColor: selected.hex }}
      >
        <div className="grid grid-cols-6 gap-3 rounded-xl bg-white dark:bg-slate-900 p-4 shadow-lg">
          {CALENDAR_COLORS.map((color) => (
            <button
              key={color.id}
              type="button"
              onClick={() => onChange(color.id)}
              title={color.name}
              aria-label={color.name}
              className={`h-7 w-7 rounded-full transition-transform duration-150 hover:scale-125 ${
                color.id === selected.id ? "ring-2 ring-slate-700 ring-offset-2 dark:ring-slate-200 dark:ring-offset-slate-900" : ""
              }`}
              style={{ backgroundColor: color.hex }}
            />
          ))}
        </div>
      </div>
      <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{selected.name}</p>
    </div>
  );
}

export default ColorPicker;
