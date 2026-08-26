import { useState } from "react";
import { X } from "lucide-react";

function ItemRow({ id, onRemove, children }) {
  const [isRemoving, setIsRemoving] = useState(false);

  return (
    <div
      id={id}
      className={`grid transition-[grid-template-rows,opacity] duration-300 ease-in-out ${
        isRemoving ? "grid-rows-[0fr] opacity-0" : "grid-rows-[1fr] opacity-100"
      }`}
      onTransitionEnd={(event) => {
        if (isRemoving && event.propertyName === "grid-template-rows") onRemove();
      }}
    >
      <div className="overflow-hidden">
        <div className="group relative mb-3 rounded-lg border border-slate-200 bg-white p-4 pr-10">
          <button
            type="button"
            onClick={() => setIsRemoving(true)}
            aria-label="Remove"
            className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-red-100 hover:text-red-500"
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
