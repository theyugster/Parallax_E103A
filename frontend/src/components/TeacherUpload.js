import { useRef, useState, useEffect } from "react";
import "./TeacherUpload.css";

export default function TeacherUpload() {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [classrooms, setClassrooms] = useState([]); // Store list of classrooms
  const [selectedClassroomId, setSelectedClassroomId] = useState(""); // Store selected ID

  // 1. Fetch Classrooms on Component Mount
  useEffect(() => {
    async function fetchClassrooms() {
      const token = localStorage.getItem("token");
      try {
        const response = await fetch("http://localhost:8000/classrooms/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setClassrooms(data);
        } else {
            console.error("Failed to fetch classrooms");
        }
      } catch (error) {
        console.error("Error fetching classrooms:", error);
      }
    }
    fetchClassrooms();
  }, []);

  function openFilePicker() {
    fileInputRef.current.click();
  }

  function handleFileChange(e) {
    setFile(e.target.files[0]);
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!file) {
      alert("Please select a document first");
      return;
    }
    
    // 2. Validate Classroom Selection
    if (!selectedClassroomId) {
      alert("Please select a classroom to upload to.");
      return;
    }

    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);

    try {
      // 3. Use the selected ID in the URL
      const response = await fetch(
        `http://localhost:8000/classrooms/${selectedClassroomId}/documents`, 
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      alert(`Document "${file.name}" uploaded successfully!`);
      setFile(null);
      // Optional: clear selection
      // setSelectedClassroomId(""); 
    } catch (error) {
      console.error(error);
      alert("Upload Error: " + error.message);
    }
  }

  return (
    <div className="upload-wrapper">
      <h2>Upload Learning Material</h2>
      <p className="upload-subtitle">
        Select a classroom and upload files to generate learning vectors
      </p>

      <form onSubmit={handleSubmit} className="upload-card">
        {/* 4. Add Classroom Dropdown */}
        <select 
            className="classroom-select"
            value={selectedClassroomId}
            onChange={(e) => setSelectedClassroomId(e.target.value)}
            required
        >
            <option value="" disabled>-- Select a Classroom --</option>
            {classrooms.map((c) => (
                <option key={c.id} value={c.id}>
                    {c.name}
                </option>
            ))}
        </select>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          hidden
        />

        <div className="upload-zone" onClick={openFilePicker}>
          <div className="upload-content">
            <span className="upload-icon">📄</span>
            <p>{file ? file.name : "Click to select a document"}</p>
            <small>Supported: PDF, TXT, DOCX</small>
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary upload-btn"
          disabled={!selectedClassroomId || !file} // Disable if invalid
        >
          Upload Document
        </button>
      </form>
    </div>
  );
}