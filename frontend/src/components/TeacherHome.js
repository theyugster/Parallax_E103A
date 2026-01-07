import { useState } from "react";
import "./TeacherHome.css";
import TeacherUpload from "./TeacherUpload";

export default function TeacherHome({ user }) {
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleCreateClassroom = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      const res = await fetch("http://localhost:8000/classrooms/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, description }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create classroom");
      }

      alert("Classroom created successfully!");
      setIsCreating(false);
      setName("");
      setDescription("");
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="home-wrapper">
      {/* Header */}
      <div className="home-header">
        <h2>Welcome, {user.full_name}</h2>
        <p className="home-subtitle">
          Manage classrooms, upload learning material, and track students
        </p>
      </div>

      {/* Quick Action Cards */}
      <div className="home-grid">
        <div 
          className={`home-card ${isCreating ? "active-card" : ""}`} 
          onClick={() => setIsCreating(!isCreating)}
          style={{ cursor: "pointer" }}
        >
          <h4>📘 Create Classroom</h4>
          <p>Organize subjects, chapters, and lessons.</p>
        </div>

        <div className="home-card">
          <h4>📊 Student Insights</h4>
          <p>Monitor engagement and performance.</p>
        </div>
      </div>

      {/* Create Classroom Form Section */}
      {isCreating && (
        <div className="create-form-container">
          <h3>New Classroom Details</h3>
          <form onSubmit={handleCreateClassroom} className="create-form">
            <div className="form-group">
              <label>Classroom Name</label>
              <input 
                type="text" 
                placeholder="e.g. Grade 10 Physics" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <input 
                type="text" 
                placeholder="e.g. Mechanics and Thermodynamics" 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary">Create Classroom</button>
              <button 
                type="button" 
                className="btn-secondary" 
                onClick={() => setIsCreating(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Upload Section */}
      <div className="upload-section">
        <h3>📄 Upload Learning Material</h3>
        <TeacherUpload />
      </div>
    </div>
  );
}