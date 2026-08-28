import { useEffect } from "react";
import { MapPin } from "lucide-react";
import EditableField from "./EditableField";
import ItemRow from "./ItemRow";
import AddItemButton from "./AddItemButton";
import { useFrozenSortedIndices } from "./sortByDate";

// Any tab whose items render as one-off calendar entries: a date, an optional
// time range, and a location. `indices` selects which of `events` this tab
// shows; `blankItem` carries the type field for newly added items.
function EventsTab({
  events,
  indices,
  path,
  addLabel,
  blankItem,
  onUpdate,
  onRemove,
  onAdd,
  showDateErrors,
  scrollToFirstMissingDate,
}) {
  const sortedIndices = useFrozenSortedIndices(events, "date", "start_time", indices);

  // Runs once when this tab mounts (it remounts on every tab switch - see the
  // `key` in ReviewModal) so a failed Add to Calendar attempt doesn't just
  // land the user on the right tab, it lands them on the exact row to fix.
  useEffect(() => {
    if (!scrollToFirstMissingDate) return;
    const missingIndex = sortedIndices.find((index) => !events[index].date);
    if (missingIndex === undefined) return;
    document
      .getElementById(`item-${events[missingIndex]._key}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col">
      {sortedIndices.map((index) => {
        const event = events[index];
        return (
          <ItemRow key={event._key} id={`item-${event._key}`} onRemove={() => onRemove(path, index)}>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <EditableField
                className="col-span-2 sm:col-span-4 font-medium"
                value={event.title}
                placeholder="Event title"
                onChange={(value) => onUpdate(path, index, "title", value)}
              />
              <EditableField
                type="date"
                value={event.date}
                invalid={showDateErrors && !event.date}
                onChange={(value) => onUpdate(path, index, "date", value)}
              />
              <div className="col-span-2 flex items-center justify-self-end gap-1.5 sm:col-start-3">
                <EditableField
                  type="time"
                  value={event.start_time}
                  placeholder="--:--"
                  onChange={(value) => onUpdate(path, index, "start_time", value)}
                />
                <span className="text-slate-400 dark:text-slate-500">-</span>
                <EditableField
                  type="time"
                  value={event.end_time}
                  placeholder="--:--"
                  onChange={(value) => onUpdate(path, index, "end_time", value)}
                />
              </div>
              <div className="col-span-2 flex items-center gap-1.5 sm:col-span-4">
                <MapPin className="h-4 w-4 shrink-0 text-slate-400 dark:text-slate-500" />
                <EditableField
                  value={event.location}
                  placeholder="Location"
                  onChange={(value) => onUpdate(path, index, "location", value)}
                />
              </div>
              <EditableField
                type="textarea"
                className="col-span-2 sm:col-span-4"
                value={event.description}
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

export default EventsTab;
