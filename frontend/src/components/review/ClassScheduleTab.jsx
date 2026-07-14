import { MapPin } from "lucide-react";
import EditableField from "./EditableField";
import ItemRow from "./ItemRow";
import AddItemButton from "./AddItemButton";
import DaysOfWeekPicker from "./DaysOfWeekPicker";

const BLANK_MEETING = {
  title: "",
  days_of_week: [],
  start_time: "",
  end_time: "",
  location: "",
  start_date: "",
  end_date: "",
};

function ClassScheduleTab({ meetings, onUpdate, onRemove, onAdd }) {
  return (
    <div className="flex flex-col">
      {meetings.map((meeting, index) => (
        <ItemRow
          key={meeting._key}
          onRemove={() => onRemove("class_schedule.meetings", index)}
        >
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <EditableField
              className="col-span-2 sm:col-span-4 font-medium"
              value={meeting.title}
              placeholder="Meeting title"
              onChange={(value) => onUpdate("class_schedule.meetings", index, "title", value)}
            />
            <div className="col-span-2 sm:col-span-4">
              <DaysOfWeekPicker
                value={meeting.days_of_week}
                onChange={(value) => onUpdate("class_schedule.meetings", index, "days_of_week", value)}
              />
            </div>
            <div className="col-span-2 flex items-center gap-1.5">
              <EditableField
                type="time"
                value={meeting.start_time}
                onChange={(value) => onUpdate("class_schedule.meetings", index, "start_time", value)}
              />
              <span className="text-slate-400">-</span>
              <EditableField
                type="time"
                value={meeting.end_time}
                onChange={(value) => onUpdate("class_schedule.meetings", index, "end_time", value)}
              />
            </div>
            <div className="col-span-2 flex items-center gap-1.5">
              <MapPin className="h-4 w-4 shrink-0 text-slate-400" />
              <EditableField
                value={meeting.location}
                placeholder="Location"
                onChange={(value) => onUpdate("class_schedule.meetings", index, "location", value)}
              />
            </div>
            <EditableField
              type="date"
              value={meeting.start_date}
              onChange={(value) => onUpdate("class_schedule.meetings", index, "start_date", value)}
            />
            <EditableField
              type="date"
              value={meeting.end_date}
              onChange={(value) => onUpdate("class_schedule.meetings", index, "end_date", value)}
            />
          </div>
        </ItemRow>
      ))}

      <AddItemButton
        label="Add class meeting"
        onClick={() => onAdd("class_schedule.meetings", BLANK_MEETING)}
      />
    </div>
  );
}

export default ClassScheduleTab;
