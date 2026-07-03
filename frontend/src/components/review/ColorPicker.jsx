import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

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
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const selected =
    CALENDAR_COLORS.find((color) => color.id === value) ??
    CALENDAR_COLORS.find((color) => color.id === DEFAULT_COLOR_ID);

  useEffect(() => {
    if (!isOpen) return;

    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  return (
    <div ref={containerRef} className="relative mr-2 shrink-0">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        title={selected.name}
        aria-label={`Color: ${selected.name}`}
        className="group flex items-center gap-1"
      >
        <span
          className="h-5 w-5 rounded-full transition-transform duration-150 group-hover:scale-125"
          style={{ backgroundColor: selected.hex }}
        />
        <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute -left-1 top-7 z-30 grid w-52 grid-cols-6 gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-lg">
          {CALENDAR_COLORS.map((color) => (
            <button
              key={color.id}
              type="button"
              onClick={() => {
                onChange(color.id);
                setIsOpen(false);
              }}
              title={color.name}
              aria-label={color.name}
              className={`h-5 w-5 rounded-full transition-transform duration-150 hover:scale-125 ${
                color.id === selected.id ? "ring-2 ring-slate-400 ring-offset-2" : ""
              }`}
              style={{ backgroundColor: color.hex }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ColorPicker;
