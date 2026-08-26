import { useState } from "react";
import { X } from "lucide-react";

function ItemRow({ onRemove, children }) {
  const [isRemoving, setIsRemoving] = useState(false);

  return (
    <div
      className={`grid transition-[grid-template-rows,opacity] duration-300 ease-in-out ${
        isRemoving ? "grid-rows-[0fr] opacity-0" : "grid-rows-[1fr] opacity-100"
      }`}
      onTransitionEnd={(event) => {
        if (isRemoving && event.propertyName === "grid-template-rows") onRemove();
      }}
    >
      <div className="overflow-hidden">
        <div className="group relative mb-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 p-4 pr-10">
          <button
            type="button"
            onClick={() => setIsRemoving(true)}
            aria-label="Remove"
            className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors hover:bg-red-100 dark:hover:bg-red-500/20 hover:text-red-500 dark:hover:text-red-400"
          >
            <X className="h-4 w-4" />
          </button>
          {children}
        </div>
      </div>
    </div>
  );
}

export default ItemRow;
