import { useState } from "react";
import { X, Check } from "lucide-react";
import EditableField from "./EditableField";
import ClassScheduleTab from "./ClassScheduleTab";
import EventsTab from "./EventsTab";
import DueItemsTab from "./DueItemsTab";
import ColorPicker, { DEFAULT_COLOR_ID } from "./ColorPicker";

function getIn(obj, path) {
  return path.split(".").reduce((acc, key) => acc?.[key], obj);
}

// Shallow-clones every object along `path` so React state updates stay immutable.
function setIn(obj, path, value) {
  const keys = path.split(".");
  const next = { ...obj };
  let cursor = next;
  for (let i = 0; i < keys.length - 1; i++) {
    cursor[keys[i]] = { ...cursor[keys[i]] };
    cursor = cursor[keys[i]];
  }
  cursor[keys[keys.length - 1]] = value;
  return next;
}

// Maps a tab id to the payload path(s) that should be emptied when the
// user disables that tab, so its category is excluded from the calendar.
const TAB_DATA_PATHS = {
  schedule: ["class_schedule.meetings"],
  events: ["calendar_events"],
  tasks: ["tasks"],
  readings: ["readings"],
};

function ReviewModal({ data, onChange, onClose, onConfirm, isSubmitting, submitError }) {
  const [activeTab, setActiveTab] = useState("schedule");
  const [disabledTabs, setDisabledTabs] = useState(() => new Set());
  const [colorId, setColorId] = useState(DEFAULT_COLOR_ID);

  function updateItem(path, index, field, value) {
    onChange((prev) => {
      const array = getIn(prev, path).slice();
      array[index] = { ...array[index], [field]: value };
      return setIn(prev, path, array);
    });
  }

  function removeItem(path, index) {
    onChange((prev) => setIn(prev, path, getIn(prev, path).filter((_, i) => i !== index)));
  }

  function addItem(path, blank) {
    onChange((prev) => setIn(prev, path, [...getIn(prev, path), blank]));
  }

  function updateCourse(field, value) {
    onChange((prev) => ({ ...prev, course: { ...prev.course, [field]: value } }));
  }

  function toggleTabDisabled(tabId) {
    setDisabledTabs((prev) => {
      const next = new Set(prev);
      if (next.has(tabId)) {
        next.delete(tabId);
      } else {
        next.add(tabId);
        if (activeTab === tabId) {
          const fallback = tabs.find((tab) => tab.id !== tabId && !next.has(tab.id));
          if (fallback) setActiveTab(fallback.id);
        }
      }
      return next;
    });
  }

  function handleConfirm() {
    let payload = data;
    for (const tabId of disabledTabs) {
      for (const path of TAB_DATA_PATHS[tabId]) {
        payload = setIn(payload, path, []);
      }
    }
    onConfirm({ ...payload, color_id: colorId });
  }

  const tabs = [
    { id: "schedule", label: "Class Schedule", count: data.class_schedule.meetings.length },
    { id: "events", label: "Events", count: data.calendar_events.length },
    { id: "tasks", label: "Tasks", count: data.tasks.length },
    { id: "readings", label: "Readings", count: data.readings.length },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl bg-white shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-6">
          <div className="flex flex-1 flex-col gap-2">
            <EditableField
              className="text-lg font-semibold"
              value={data.course.course_name}
              placeholder="Course name"
              onChange={(value) => updateCourse("course_name", value)}
            />
            <div className="grid grid-cols-3 gap-3">
              <EditableField
                value={data.course.course_code}
                placeholder="Course code"
                onChange={(value) => updateCourse("course_code", value)}
              />
              <EditableField
                value={data.course.instructor}
                placeholder="Instructor"
                onChange={(value) => updateCourse("instructor", value)}
              />
              <EditableField
                value={data.course.term}
                placeholder="Term"
                onChange={(value) => updateCourse("term", value)}
              />
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-slate-400 transition-colors hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 flex items-center justify-between border-b border-slate-200 px-6">
          <div className="flex gap-1">
            {tabs.map((tab) => {
              const isDisabled = disabledTabs.has(tab.id);
              return (
                <div
                  key={tab.id}
                  className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                    isDisabled
                      ? "border-transparent text-slate-300"
                      : activeTab === tab.id
                        ? "border-indigo-500 text-indigo-600"
                        : "border-transparent text-slate-500 hover:text-slate-700"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    disabled={isDisabled}
                    className={isDisabled ? "cursor-not-allowed line-through" : ""}
                  >
                    {tab.label} ({tab.count})
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleTabDisabled(tab.id)}
                    aria-label={isDisabled ? `Enable ${tab.label}` : `Disable ${tab.label}`}
                    className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                      isDisabled
                        ? "border-slate-300 bg-white"
                        : "border-indigo-500 bg-indigo-500"
                    }`}
                  >
                    {!isDisabled && <Check className="h-3 w-3 text-white" />}
                  </button>
                </div>
              );
            })}
          </div>

          <ColorPicker value={colorId} onChange={setColorId} />
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === "schedule" && (
            <ClassScheduleTab
              meetings={data.class_schedule.meetings}
              onUpdate={updateItem}
              onRemove={removeItem}
              onAdd={addItem}
            />
          )}
          {activeTab === "events" && (
            <EventsTab
              events={data.calendar_events}
              onUpdate={updateItem}
              onRemove={removeItem}
              onAdd={addItem}
            />
          )}
          {activeTab === "tasks" && (
            <DueItemsTab
              items={data.tasks}
              path="tasks"
              addLabel="Add task"
              onUpdate={updateItem}
              onRemove={removeItem}
              onAdd={addItem}
            />
          )}
          {activeTab === "readings" && (
            <DueItemsTab
              items={data.readings}
              path="readings"
              addLabel="Add reading"
              onUpdate={updateItem}
              onRemove={removeItem}
              onAdd={addItem}
            />
          )}
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-slate-200 p-6">
          {submitError && <p className="mr-auto text-sm text-red-500">{submitError}</p>}
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isSubmitting}
            className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Adding to Calendar..." : "Add to Calendar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ReviewModal;
