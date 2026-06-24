// npm run dev

import { useState } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [backendMessage, setBackendMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  function connectGoogle() {
    window.location.href = "http://localhost:8000/auth/google";
  }

  async function callBackend() {
    try {
      const response = await fetch("http://localhost:8000/test");
      const data = await response.json();

      setBackendMessage(data.message);
    } catch (error) {
      console.error("Error calling backend:", error);
      setBackendMessage("Could not connect to backend");
    }
  }

  function handleFileChange(event) {
    setSelectedFile(event.target.files[0]);
    setErrorMessage("");
  }

  async function uploadFile() {
    console.log("uploading file...");

    if (!selectedFile) {
      console.error("Error: Trying to upload file without any selected file")
      return;
    }

    let formData = new FormData();
    formData.append("file", selectedFile);
    const response = await fetch("http://localhost:8000/upload-syllabus", {
      method: "POST", 
      body: formData
    });
    const data = await response.json();
    console.log(data);
    setBackendMessage(data);

    console.log("retrieved backend message");
  }

  // async function uploadFile() {
  //   const response = await fetch("http://localhost:8000/test-openai");
  //   const data = await response.json();
  //   setBackendMessage(data.message)
  // }

  async function addEvent() {
    const response = await fetch("http://localhost:8000/test-calendar");
    const data = await response.json();
    setBackendMessage(data.message)
  }

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Syllabus Calendar App</h1>

      <p>This is the barebones frontend/backend connection test.</p>

      <input type="file" onChange={handleFileChange} />

      <p style={{ marginTop: "20px" }}>
        File selected: 
      </p>

      {/* {backendMessage && (
        <div>
          <p>Selected file: {backendMessage.name}</p>
          <p>File type: {backendMessage.type}</p>
          <p>File size: {backendMessage.size} bytes</p>
          <p>Text preview: {backendMessage.text_preview}</p>
          <p>Backend message: {backendMessage.message}</p>
        </div>
      )} */}

      {backendMessage && (
        <div>
          <p>Message from backend: </p>
          <p>{backendMessage}</p>
        </div>
      )}

      <button onClick={uploadFile}>Upload File</button>
      <div>
        <button onClick={connectGoogle}>Connect Google</button>
      </div>
      <div>
        <button onClick={addEvent}>Test Calendar</button>
      </div>
    </div>
  );
}

export default App;