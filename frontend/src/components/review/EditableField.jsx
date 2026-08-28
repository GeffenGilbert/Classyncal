import { X } from "lucide-react";

const BASE_CLASS =
  "mr-4 rounded border border-slate-200 dark:border-slate-800 bg-transparent px-1.5 py-1 text-sm text-slate-900 dark:text-slate-50 transition-colors hover:border-slate-300 dark:hover:border-slate-600 focus:border-indigo-400 focus:bg-white dark:focus:bg-slate-800 focus:outline-none";

// Date/time inputs shrink to fit their content so the browser's picker icon
// sits right next to the typed value instead of at the far edge of a
// stretched grid cell.
const WIDTH_CLASS = { date: "w-fit", time: "w-fit" };

function EditableField({ type = "text", value, onChange, placeholder, options, className = "" }) {
  const widthClass = WIDTH_CLASS[type] ?? "w-[calc(100%-1rem)]";

  if (type === "textarea") {
    return (
      <textarea
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={2}
        className={`${BASE_CLASS} ${widthClass} resize-none ${className}`}
      />
    );
  }

  if (type === "select") {
    return (
      <select
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        className={`${BASE_CLASS} ${widthClass} ${className}`}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }

  if (type === "time") {
    return (
      <span className="relative mr-4 inline-block">
        <input
          type="time"
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          className={`mr-0 ${BASE_CLASS.replace("mr-4 ", "")} ${widthClass} ${value ? "pr-6" : ""} ${className}`}
        />
        {value && (
          // iOS Safari's native time picker has no way to clear a value once set.
          <button
            type="button"
            onClick={() => onChange("")}
            aria-label="Clear time"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-400 dark:hover:text-slate-300"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </span>
    );
  }

  return (
    <input
      type={type}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      className={`${BASE_CLASS} ${widthClass} ${className}`}
    />
  );
}

export default EditableField;
