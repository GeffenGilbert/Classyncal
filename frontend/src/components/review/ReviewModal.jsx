import { useState } from "react";
import { X, Check } from "lucide-react";
import EditableField from "./EditableField";
import ClassScheduleTab from "./ClassScheduleTab";
import EventsTab from "./EventsTab";
import DueItemsTab from "./DueItemsTab";
import ColorPicker from "./ColorPicker";
import { DEFAULT_COLOR_ID } from "./colorPickerConfig";

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
  tests: ["tests"],
  projects: ["projects"],
  assignments: ["assignments"],
  readings: ["readings"],
};

function ReviewModal({ data, onChange, onClose, onConfirm, isSubmitting, submitError }) {
  const tabs = [
    { id: "schedule", label: "Class Schedule", count: data.class_schedule.meetings.length },
    { id: "tests", label: "Tests", count: data.tests.length },
    { id: "projects", label: "Projects", count: data.projects.length },
    { id: "assignments", label: "Assignments", count: data.assignments.length },
    { id: "readings", label: "Readings", count: data.readings.length },
  ];
  // Categories with nothing extracted have nothing to select or review.
  // Captured once on mount so a category doesn't vanish from the selection
  // screen just because the user emptied it out while reviewing — live
  // counts still show (e.g. "Readings (0)"), the category just stays listed.
  const [availableTabIds] = useState(
    () => new Set(tabs.filter((tab) => tab.count > 0).map((tab) => tab.id)),
  );
  const availableTabs = tabs.filter((tab) => availableTabIds.has(tab.id));

  const [step, setStep] = useState("select");
  const [selectedTabs, setSelectedTabs] = useState(
    () => new Set(availableTabs.map((tab) => tab.id)),
  );
  const [colorId, setColorId] = useState(DEFAULT_COLOR_ID);

  // Ordered list of the categories the user opted into, one per review step.
  // Deliberately not filtered by live count: a category the user selected
  // must stay in the sequence even if they remove every item in it while
  // reviewing, otherwise the step index would point past the shrunk list.
  const reviewSteps = tabs.filter((tab) => selectedTabs.has(tab.id));
  const currentTab = typeof step === "number" ? reviewSteps[step] : null;

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
    onChange((prev) =>
      setIn(prev, path, [...getIn(prev, path), { ...blank, _key: crypto.randomUUID() }]),
    );
  }

  function updateCourse(field, value) {
    onChange((prev) => ({ ...prev, course: { ...prev.course, [field]: value } }));
  }

  function toggleTabSelected(tabId) {
    setSelectedTabs((prev) => {
      const next = new Set(prev);
      if (next.has(tabId)) {
        next.delete(tabId);
      } else {
        next.add(tabId);
      }
      return next;
    });
  }

  function handleNext() {
    if (reviewSteps.length === 0) return;
    setStep(0);
  }

  function handleBackFromReview() {
    setStep(step === 0 ? "select" : step - 1);
  }

  function handleNextFromReview() {
    setStep(step === reviewSteps.length - 1 ? "colors" : step + 1);
  }

  function handleBackFromColors() {
    setStep(reviewSteps.length - 1);
  }

  function handleConfirm() {
    let payload = data;
    for (const tabId of Object.keys(TAB_DATA_PATHS)) {
      for (const path of TAB_DATA_PATHS[tabId]) {
        const items = selectedTabs.has(tabId) ? getIn(payload, path) : [];
        payload = setIn(
          payload,
          path,
          items.map((item) => {
            const clean = { ...item };
            delete clean._key;
            return clean;
          }),
        );
      }
    }
    onConfirm({ ...payload, color_id: colorId });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div
        className={`flex w-full max-w-3xl flex-col rounded-2xl bg-white shadow-xl ${
          currentTab ? "h-[85vh]" : "max-h-[85vh]"
        }`}
      >
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

        {step === "select" && (
          <div className="flex-1 overflow-y-auto p-6">
            <p className="mb-4 text-sm text-slate-500">
              Choose which categories you&apos;d like to add to your calendar.
            </p>
            <div className="flex flex-col gap-2">
              {availableTabs.map((tab) => {
                const isSelected = selectedTabs.has(tab.id);
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => toggleTabSelected(tab.id)}
                    className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left transition-colors ${
                      isSelected
                        ? "border-indigo-500 bg-indigo-50"
                        : "border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <span className="text-sm font-medium text-slate-700">
                      {tab.label} <span className="text-slate-400">({tab.count})</span>
                    </span>
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded border transition-colors ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-500"
                          : "border-slate-300 bg-white"
                      }`}
                    >
                      {isSelected && <Check className="h-3.5 w-3.5 text-white" />}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {currentTab && (
          <>
            <div className="mt-4 border-b border-slate-200 px-6 pb-3">
              <p className="text-sm font-medium text-slate-500">
                Review and Edit the <span className="font-bold">{currentTab.label}</span> to Your Preferences
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {currentTab.id === "schedule" && (
                <ClassScheduleTab
                  meetings={data.class_schedule.meetings}
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {currentTab.id === "tests" && (
                <EventsTab
                  events={data.tests}
                  path="tests"
                  addLabel="Add test"
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {currentTab.id === "projects" && (
                <DueItemsTab
                  items={data.projects}
                  path="projects"
                  addLabel="Add project"
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {currentTab.id === "assignments" && (
                <DueItemsTab
                  items={data.assignments}
                  path="assignments"
                  addLabel="Add assignment"
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {currentTab.id === "readings" && (
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
          </>
        )}

        {step === "colors" && (
          <div className="flex-1 overflow-y-auto p-6">
            <p className="mb-4 text-sm text-slate-500">
              Pick a <span className="font-bold">calendar color</span> for the events.
            </p>
            <ColorPicker value={colorId} onChange={setColorId} />
          </div>
        )}

        <div className="flex items-center justify-between border-t border-slate-200 p-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          >
            Cancel
          </button>
          <div className="flex items-center gap-3">
            {submitError && <p className="text-sm text-red-500">{submitError}</p>}
            {step === "select" && (
              <button
                type="button"
                onClick={handleNext}
                disabled={selectedTabs.size === 0}
                className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Next
              </button>
            )}
            {currentTab && (
              <>
                <button
                  type="button"
                  onClick={handleBackFromReview}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleNextFromReview}
                  className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600"
                >
                  Next
                </button>
              </>
            )}
            {step === "colors" && (
              <>
                <button
                  type="button"
                  onClick={handleBackFromColors}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={isSubmitting}
                  className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Adding to Calendar..." : "Add to Calendar"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReviewModal;
