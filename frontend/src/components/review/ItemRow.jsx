import { X } from "lucide-react";

function ItemRow({ onRemove, children }) {
  return (
    <div className="group relative rounded-lg border border-slate-200 bg-white p-4 pr-10">
      <button
        type="button"
        onClick={onRemove}
        aria-label="Remove"
        className="absolute right-3 top-3 text-slate-300 transition-colors hover:text-red-500"
      >
        <X className="h-4 w-4" />
      </button>
      {children}
    </div>
  );
}

export default ItemRow;
