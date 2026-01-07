import "./StudentHome.css";

export default function StudentHome({ user }) {
  return (
    <div className="home-wrapper">
      <h2>Welcome, {user.full_name}</h2>

      <div className="home-grid">
        <div className="home-card student">
          <h4>📚 Join Classrooms</h4>
          <p>Access teacher-led learning spaces.</p>
        </div>

        <div className="home-card student">
          <h4>🧠 Smart Learning</h4>
          <p>Personalized content based on your interests.</p>
        </div>

        <div className="home-card student">
          <h4>📝 Assessments</h4>
          <p>Test your knowledge dynamically.</p>
        </div>
      </div>
    </div>
  );
}
