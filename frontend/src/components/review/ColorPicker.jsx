// Google Calendar's fixed event color palette (colorId -> name/hex).
export const CALENDAR_COLORS = [
  { id: "1", name: "Lavender", hex: "#7986cb" },
  { id: "2", name: "Sage", hex: "#33b679" },
  { id: "3", name: "Grape", hex: "#8e24aa" },
  { id: "4", name: "Flamingo", hex: "#e67c73" },
  { id: "5", name: "Banana", hex: "#f6c026" },
  { id: "6", name: "Tangerine", hex: "#f5511d" },
  { id: "7", name: "Peacock", hex: "#039be5" },
  { id: "8", name: "Graphite", hex: "#616161" },
  { id: "9", name: "Blueberry", hex: "#3f51b5" },
  { id: "10", name: "Basil", hex: "#0b8043" },
  { id: "11", name: "Tomato", hex: "#d60000" },
];

export const DEFAULT_COLOR_ID = "1";

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
        <div className="grid grid-cols-6 gap-3 rounded-xl bg-white p-4 shadow-lg">
          {CALENDAR_COLORS.map((color) => (
            <button
              key={color.id}
              type="button"
              onClick={() => onChange(color.id)}
              title={color.name}
              aria-label={color.name}
              className={`h-7 w-7 rounded-full transition-transform duration-150 hover:scale-125 ${
                color.id === selected.id ? "ring-2 ring-slate-700 ring-offset-2" : ""
              }`}
              style={{ backgroundColor: color.hex }}
            />
          ))}
        </div>
      </div>
      <p className="text-sm font-medium text-slate-600">{selected.name}</p>
    </div>
  );
}

export default ColorPicker;
