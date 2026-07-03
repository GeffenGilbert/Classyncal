const BASE_CLASS =
  "rounded border border-transparent bg-transparent px-1.5 py-1 text-sm text-slate-900 transition-colors hover:border-slate-200 focus:border-indigo-400 focus:bg-white focus:outline-none";

// Date/time inputs shrink to fit their content so the browser's picker icon
// sits right next to the typed value instead of at the far edge of a
// stretched grid cell.
const WIDTH_CLASS = { date: "w-fit", time: "w-fit" };

function EditableField({ type = "text", value, onChange, placeholder, options, className = "" }) {
  const widthClass = WIDTH_CLASS[type] ?? "w-full";

  if (type === "textarea") {
    return (
      <textarea
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={2}
        className={`${BASE_CLASS} w-full resize-none ${className}`}
      />
    );
  }

  if (type === "select") {
    return (
      <select
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        className={`${BASE_CLASS} w-full ${className}`}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
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
