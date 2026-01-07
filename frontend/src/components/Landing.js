import "./Landing.css";

export default function Landing({ onLoginClick, onSignupClick }) {
  return (
    <div className="landing">
      <div className="hero">
        <h1>EduVector</h1>
        <p>Smart Learning for Students & Teachers</p>

        <div className="hero-buttons">
          <button className="btn-primary" onClick={onLoginClick}>
            Sign In
          </button>
          <button className="btn-outline" onClick={onSignupClick}>
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}
