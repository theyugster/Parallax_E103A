import "./Dashboard.css";

export default function Dashboard({ user }) {
  return (
    <div className="dashboard-wrapper">
      <span className={`user-badge role-${user.role}`}>
        {user.role}
      </span>

      <h2>Hello, {user.full_name}</h2>

      <div className="dashboard-grid">
        <div className="study-card">
          <h4>📚 Classrooms</h4>
          <p>Manage and explore classrooms.</p>
        </div>

        <div className="study-card">
          <h4>📄 Learning Materials</h4>
          <div className="file-upload-zone">
            Drag & drop study documents
          </div>
        </div>

        <div className="study-card">
          <h4>🧠 AI Learning</h4>
          <p>Smart content powered by embeddings.</p>
        </div>
      </div>
    </div>
  );
}
