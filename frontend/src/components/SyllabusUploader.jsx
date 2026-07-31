import { useCallback, useEffect, useRef, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";
import ReviewModal from "./review/ReviewModal";
import UploadingScreen from "./UploadingScreen";

const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
];

// Item arrays come straight from the backend with no stable id, but React
// list rendering needs one that survives removals — using array index as a
// key makes a component get reused for a different item once an earlier one
// is removed, leaking that component's local state onto the wrong row.
function withStableKeys(data) {
  const addKeys = (items) => items.map((item) => ({ ...item, _key: crypto.randomUUID() }));
  return {
    ...data,
    class_schedule: { ...data.class_schedule, meetings: addKeys(data.class_schedule.meetings) },
    events: addKeys(data.events),
    tasks: addKeys(data.tasks),
    readings: addKeys(data.readings),
  };
}

function SyllabusUploader() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [extractedData, setExtractedData] = useState(null);
  const [isAddingToCalendar, setIsAddingToCalendar] = useState(false);
  const [addToCalendarError, setAddToCalendarError] = useState("");
  const [justAddedToCalendar, setJustAddedToCalendar] = useState(false);
  const fileInputRef = useRef(null);
  const pendingPayloadRef = useRef(null);

  function connectGoogleAndRetry(payload) {
    pendingPayloadRef.current = payload;
    window.open(
      "http://localhost:8000/auth/google",
      "google-auth-popup",
      "width=500,height=700"
    );
  }

  const addToCalendar = useCallback(async (payload) => {
    setIsAddingToCalendar(true);
    setAddToCalendarError("");

    try {
      const response = await fetch("http://localhost:8000/add-events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        const errorData = await response.json().catch(() => ({}));
        if (errorData.error === "not_authenticated") {
          connectGoogleAndRetry(payload);
          return;
        }
      }

      if (!response.ok) throw new Error("Request failed");

      setExtractedData(null);
      setSelectedFile(null);
      setJustAddedToCalendar(true);
    } catch (error) {
      console.error("Error adding events to calendar:", error);
      setAddToCalendarError("Could not add these events to your calendar. Please try again.");
    } finally {
      setIsAddingToCalendar(false);
    }
  }, []);

  useEffect(() => {
    function handleMessage(event) {
      if (event.origin !== "http://localhost:8000") return;
      if (event.data?.type !== "google-auth-success") return;

      const payload = pendingPayloadRef.current;
      pendingPayloadRef.current = null;
      if (payload) addToCalendar(payload);
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [addToCalendar]);

  function handleFiles(files) {
    const file = files?.[0];
    if (!file || !ALLOWED_FILE_TYPES.includes(file.type)) return;
    setSelectedFile(file);
    setUploadError("");
    setJustAddedToCalendar(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  }

  async function uploadSyllabus() {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const response = await fetch("http://localhost:8000/upload-syllabus", {
        method: "POST",
        body: formData,
      });

      // If backend returned an error status, surface the error message to the user
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData?.message || errorData?.detail || errorData?.error || "Could not upload your syllabus. Please try again.";
        setUploadError(message);
        return;
      }

      const data = await response.json().catch(() => null);
      if (!data) {
        setUploadError("Could not parse server response. Please try again.");
        return;
      }

      // Validate shape and protect against unexpected responses
      try {
        setExtractedData(withStableKeys(data));
      } catch {
        setUploadError("Server returned unexpected data. Please try again or contact support.");
      }
    } catch (error) {
      console.error("Error uploading syllabus:", error);
      setUploadError("Could not upload your syllabus. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <>
      {justAddedToCalendar && (
        <p className="relative -top-22 text-sm font-medium text-emerald-600">
          Syllabus Added to Calendar!
        </p>
      )}

      <div className="flex flex-col items-center gap-1 text-center">
        {justAddedToCalendar && <p className="text-sm text-slate-500">Feel Free to</p>}
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
          {justAddedToCalendar ? "Upload Another Syllabus" : "Upload Your Syllabus"}
        </h1>
      </div>

      {isUploading ? (
        <UploadingScreen fileName={selectedFile?.name} />
      ) : (
        <label
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`relative z-20 flex w-full max-w-xl cursor-pointer flex-col items-center gap-4 rounded-2xl border-2 border-dashed px-10 py-16 text-center transition-colors ${
            isDragging
              ? "border-indigo-500 bg-indigo-50"
              : "border-slate-300 bg-slate-50 hover:border-slate-400"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_FILE_TYPES.join(",")}
            className="hidden"
            onChange={(event) => handleFiles(event.target.files)}
          />

          {selectedFile ? (
            <>
              <FileText className="h-10 w-10 text-indigo-500" />
              <div>
                <p className="font-medium text-slate-900">{selectedFile.name}</p>
                <p className="mt-1 text-sm text-slate-500">
                  Click or drop a file to replace it
                </p>
              </div>
            </>
          ) : (
            <>
              <UploadCloud className="h-10 w-10 text-slate-400" />
              <div>
                <p className="font-medium text-slate-900">
                  Drag & drop your syllabus here
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  or click to browse
                </p>
              </div>
            </>
          )}
        </label>
      )}

      {selectedFile && !isUploading && (
        <button
          type="button"
          onClick={uploadSyllabus}
          className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600"
        >
          Upload Syllabus
        </button>
      )}

      {uploadError && <p className="text-sm text-red-500">{uploadError}</p>}

      {extractedData && (
        <ReviewModal
          data={extractedData}
          onChange={setExtractedData}
          onClose={() => setExtractedData(null)}
          onConfirm={addToCalendar}
          isSubmitting={isAddingToCalendar}
          submitError={addToCalendarError}
        />
      )}
    </>
  );
}

export default SyllabusUploader;
