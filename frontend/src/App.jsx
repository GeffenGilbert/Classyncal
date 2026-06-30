// npm run dev

import { useEffect, useState } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [backendMessage, setBackendMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [googleAuthMessage, setGoogleAuthMessage] = useState("");

  useEffect(() => {
    function handleMessage(event) {
      if (event.origin !== "http://localhost:8000") {
        return;
      }

      if (event.data?.type === "google-auth-success") {
        setGoogleAuthMessage("Google account connected successfully");
      }
    }

    window.addEventListener("message", handleMessage);

    return () => {
      window.removeEventListener("message", handleMessage);
    };
  }, []);

  function connectGoogle() {
    window.open(
      "http://localhost:8000/auth/google",
      "google-auth-popup",
      "width=500,height=700"
    );
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

  async function addEvents() {
    console.log("Calling add_events");

    if (!backendMessage) {
      console.error("Error: No backend message available to send")
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/add-events", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(backendMessage),
      });

      const data = await response.json();
      console.log(data);
      setBackendMessage(data.message);
    } catch (error) {
      console.error("Error sending events to backend:", error);
      setErrorMessage("Could not send extracted events to backend");
    }
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

  function DisplayClassSchedule() {
    const meetings = backendMessage.class_schedule.meetings;
    return (
      <div>
        <h2>Class Times</h2>
        {meetings.map((meeting) => (
          <div key={meeting.title}>
            <h2>Title: {meeting.title}</h2>
            <p>Every {meeting.days_of_week.join(', ')}</p>
            <p>From: {meeting.start_time} to {meeting.end_time}</p>
            <p>At: {meeting.location}</p>
          </div>
        ))}
      </div>
    );
  }

  function DisplayTasks() {
    const tasks = backendMessage.tasks;
    return (
      <div>
        <h2>Tasks</h2>
        {tasks.map((task) => (
          <div key={task.title}>
            <p>Title: {task.title}</p>
            <p>Due Date: {task.due_date}</p>
          </div>
        ))}
      </div>
    );
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

      {backendMessage?.course?.course_name && (
        <div>
          <p>Message from backend: </p>
          <h1>{backendMessage.course.course_name}</h1>
          <DisplayClassSchedule />
          <DisplayTasks />
        </div>
      )}

      {googleAuthMessage && <p>{googleAuthMessage}</p>}

      <button onClick={uploadFile}>Upload File</button>
      <div>
        <button onClick={connectGoogle}>Connect Google</button>
      </div>
      {/* <div>
        <button onClick={addEvent}>Test Calendar</button>
      </div> */}
      <div>
        <button onClick={addEvents}>Add Events</button>
      </div>
    </div>
  );
}

export default App;