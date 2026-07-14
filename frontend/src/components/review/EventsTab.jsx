import { MapPin } from "lucide-react";
import EditableField from "./EditableField";
import ItemRow from "./ItemRow";
import AddItemButton from "./AddItemButton";

const BLANK_EVENT = {
  title: "",
  date: "",
  start_time: "",
  end_time: "",
  location: "",
  description: "",
};

function EventsTab({ events, onUpdate, onRemove, onAdd }) {
  return (
    <div className="flex flex-col">
      {events.map((event, index) => (
        <ItemRow key={index} onRemove={() => onRemove("calendar_events", index)}>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <EditableField
              className="col-span-2 sm:col-span-4 font-medium"
              value={event.title}
              placeholder="Event title"
              onChange={(value) => onUpdate("calendar_events", index, "title", value)}
            />
            <EditableField
              type="date"
              value={event.date}
              onChange={(value) => onUpdate("calendar_events", index, "date", value)}
            />
            <div className="col-span-2 flex items-center justify-self-end gap-1.5 sm:col-start-3">
              <EditableField
                type="time"
                value={event.start_time}
                onChange={(value) => onUpdate("calendar_events", index, "start_time", value)}
              />
              <span className="text-slate-400">-</span>
              <EditableField
                type="time"
                value={event.end_time}
                onChange={(value) => onUpdate("calendar_events", index, "end_time", value)}
              />
            </div>
            <div className="col-span-2 flex items-center gap-1.5 sm:col-span-4">
              <MapPin className="h-4 w-4 shrink-0 text-slate-400" />
              <EditableField
                value={event.location}
                placeholder="Location"
                onChange={(value) => onUpdate("calendar_events", index, "location", value)}
              />
            </div>
            <EditableField
              type="textarea"
              className="col-span-2 sm:col-span-4"
              value={event.description}
              placeholder="Description"
              onChange={(value) => onUpdate("calendar_events", index, "description", value)}
            />
          </div>
        </ItemRow>
      ))}

      <AddItemButton label="Add event" onClick={() => onAdd("calendar_events", BLANK_EVENT)} />
    </div>
  );
}

export default EventsTab;
