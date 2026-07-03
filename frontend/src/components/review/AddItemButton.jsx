import { Plus } from "lucide-react";

function AddItemButton({ onClick, label }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 py-3 text-sm text-slate-500 transition-colors hover:border-indigo-400 hover:text-indigo-500"
    >
      <Plus className="h-4 w-4" />
      {label}
    </button>
  );
}

export default AddItemButton;
