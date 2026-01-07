import "./TeacherHome.css";
import TeacherUpload from "./TeacherUpload";

export default function TeacherHome({ user }) {
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
        <div className="home-card">
          <h4>📘 Create Classroom</h4>
          <p>Organize subjects, chapters, and lessons.</p>
        </div>

        <div className="home-card">
          <h4>📊 Student Insights</h4>
          <p>Monitor engagement and performance.</p>
        </div>
      </div>

      {/* Upload Section */}
      <div className="upload-section">
        <h3>📄 Upload Learning Material</h3>
        <TeacherUpload />
      </div>
    </div>
  );
}
