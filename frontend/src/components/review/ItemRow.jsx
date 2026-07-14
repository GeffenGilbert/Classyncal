import { X } from "lucide-react";

function ItemRow({ onRemove, children }) {
  return (
    <div className="group relative rounded-lg border border-slate-200 bg-white p-4 pr-10">
      <button
        type="button"
        onClick={onRemove}
        aria-label="Remove"
        className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-red-100 hover:text-red-500"
      >
        <X className="h-4 w-4" />
      </button>
      {children}
    </div>
  );
}

export default ItemRow;
