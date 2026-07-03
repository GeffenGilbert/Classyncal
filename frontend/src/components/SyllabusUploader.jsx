import { useRef, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";

function SyllabusUploader() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef(null);

  function handleFiles(files) {
    const file = files?.[0];
    if (!file || file.type !== "application/pdf") return;
    setSelectedFile(file);
    setUploadError("");
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
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error("Error uploading syllabus:", error);
      setUploadError("Could not upload your syllabus. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <>
      <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
        Upload Your Syllabus
      </h1>

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
          accept="application/pdf"
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
                Drag & drop your syllabus PDF here
              </p>
              <p className="mt-1 text-sm text-slate-500">or click to browse</p>
            </div>
          </>
        )}
      </label>

      {selectedFile && (
        <button
          type="button"
          onClick={uploadSyllabus}
          disabled={isUploading}
          className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isUploading ? "Uploading..." : "Upload Syllabus"}
        </button>
      )}

      {uploadError && <p className="text-sm text-red-500">{uploadError}</p>}
    </>
  );
}

export default SyllabusUploader;
