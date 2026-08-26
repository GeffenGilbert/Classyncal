import { useEffect } from "react";
import EditableField from "./EditableField";
import ItemRow from "./ItemRow";
import AddItemButton from "./AddItemButton";
import { useFrozenSortedIndices } from "./sortByDate";

// Shared by every tab whose items are a deadline rather than a duration:
// Assignments, Projects, and Readings. `indices` selects which of `items` this
// tab shows; `blankItem` carries the type field that keeps a newly added item
// in the tab that created it.
function DueItemsTab({
  items,
  indices,
  path,
  onUpdate,
  onRemove,
  onAdd,
  addLabel,
  blankItem,
  showDateErrors,
  scrollToFirstMissingDate,
}) {
  const sortedIndices = useFrozenSortedIndices(items, "due_date", "due_time", indices);

  // Runs once when this tab mounts (it remounts on every tab switch - see the
  // `key` in ReviewModal) so a failed Add to Calendar attempt doesn't just
  // land the user on the right tab, it lands them on the exact row to fix.
  useEffect(() => {
    if (!scrollToFirstMissingDate) return;
    const missingIndex = sortedIndices.find((index) => !items[index].due_date);
    if (missingIndex === undefined) return;
    document
      .getElementById(`item-${items[missingIndex]._key}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col">
      {sortedIndices.map((index) => {
        const item = items[index];
        return (
          <ItemRow key={item._key} id={`item-${item._key}`} onRemove={() => onRemove(path, index)}>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <EditableField
                className="col-span-2 sm:col-span-4 font-medium"
                value={item.title}
                placeholder="Title"
                onChange={(value) => onUpdate(path, index, "title", value)}
              />
              <EditableField
                type="date"
                value={item.due_date}
                invalid={showDateErrors && !item.due_date}
                onChange={(value) => onUpdate(path, index, "due_date", value)}
              />
              <EditableField
                type="time"
                value={item.due_time}
                placeholder="--:--"
                onChange={(value) => onUpdate(path, index, "due_time", value)}
              />
              <EditableField
                type="textarea"
                className="col-span-2 sm:col-span-2"
                value={item.description}
                placeholder="Description"
                onChange={(value) => onUpdate(path, index, "description", value)}
              />
            </div>
          </ItemRow>
        );
      })}

      <AddItemButton label={addLabel} onClick={() => onAdd(path, blankItem)} />
    </div>
  );
}

export default DueItemsTab;
