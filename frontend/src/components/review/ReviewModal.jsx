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

// The payload has two content arrays — events (things that occupy time) and
// tasks (things with a deadline) — and each carries a type field. Tabs are
// views over those arrays rather than arrays of their own: `match` selects the
// items a tab owns, and `blank` seeds a new item so it lands in that same tab.
//
// Where two tabs share a path, one owns a named set of types and the other is
// the catch-all for the rest. The catch-all is written as a negation on
// purpose: a positive list would leave an event with an unexpected or missing
// event_type in no tab at all, invisible in review but still synced.
const TEST_TYPES = ["exam", "quiz", "final_exam"];
const isTest = (item) => TEST_TYPES.includes(item.event_type);

const TAB_CONFIG = [
  {
    id: "schedule",
    label: "Class Schedule",
    path: "class_schedule.meetings",
  },
  {
    id: "tests",
    label: "Tests",
    path: "events",
    match: isTest,
    addLabel: "Add test",
    blank: {
      title: "",
      event_type: "exam",
      date: "",
      start_time: "",
      end_time: "",
      location: "",
      description: "",
    },
  },
  {
    id: "assignments",
    label: "Assignments",
    path: "tasks",
    match: (item) => item.task_type !== "project",
    addLabel: "Add assignment",
    blank: { title: "", task_type: "assignment", due_date: "", due_time: "", description: "" },
  },
  {
    id: "projects",
    label: "Projects",
    path: "tasks",
    match: (item) => item.task_type === "project",
    addLabel: "Add project",
    blank: { title: "", task_type: "project", due_date: "", due_time: "", description: "" },
  },
  {
    id: "readings",
    label: "Readings",
    path: "readings",
    addLabel: "Add reading",
    blank: { title: "", reading_type: "other", due_date: "", due_time: "", description: "" },
  },
  // Last on purpose: this is the catch-all for events no other tab claimed, so it is
  // the least predictable list and the one a user is most likely to skim.
  {
    id: "events",
    label: "Other Events",
    path: "events",
    match: (item) => !isTest(item),
    addLabel: "Add event",
    blank: {
      title: "",
      event_type: "other",
      date: "",
      start_time: "",
      end_time: "",
      location: "",
      description: "",
    },
  },
];

// Distinct paths, for the _key strip that runs over everything on confirm.
const ALL_PATHS = [...new Set(TAB_CONFIG.map((tab) => tab.path))];

function ReviewModal({ data, onChange, onClose, onConfirm, isSubmitting, submitError }) {
  // Indices into each tab's source array, so a tab can render its own subset
  // while still updating and removing items by their real position.
  const tabs = TAB_CONFIG.map((tab) => {
    const items = getIn(data, tab.path);
    const indices = items.reduce(
      (acc, item, index) => (!tab.match || tab.match(item) ? [...acc, index] : acc),
      [],
    );
    return { ...tab, items, indices, count: indices.length };
  });
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

    // Drop the items belonging to each category the user opted out of. Tabs can
    // share a path (Assignments and Projects are both tasks), so this removes
    // only the items that tab owns rather than emptying the whole array.
    for (const tab of TAB_CONFIG) {
      if (selectedTabs.has(tab.id)) continue;
      payload = setIn(
        payload,
        tab.path,
        getIn(payload, tab.path).filter((item) => tab.match && !tab.match(item)),
      );
    }

    // _key is a client-side render key and is not part of the backend contract.
    for (const path of ALL_PATHS) {
      payload = setIn(
        payload,
        path,
        getIn(payload, path).map((item) => {
          const clean = { ...item };
          delete clean._key;
          return clean;
        }),
      );
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
                  meetings={currentTab.items}
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {["tests", "events"].includes(currentTab.id) && (
                <EventsTab
                  events={currentTab.items}
                  indices={currentTab.indices}
                  path={currentTab.path}
                  addLabel={currentTab.addLabel}
                  blankItem={currentTab.blank}
                  onUpdate={updateItem}
                  onRemove={removeItem}
                  onAdd={addItem}
                />
              )}
              {["assignments", "projects", "readings"].includes(currentTab.id) && (
                <DueItemsTab
                  items={currentTab.items}
                  indices={currentTab.indices}
                  path={currentTab.path}
                  addLabel={currentTab.addLabel}
                  blankItem={currentTab.blank}
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
