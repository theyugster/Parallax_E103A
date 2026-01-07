import "./Signup.css";

export default function Signup({ onBack }) {
  return (
    <div className="auth-container">
      <h3>Create Account</h3>

      <div className="auth-input-group">
        <input placeholder="Full Name" />
        <input placeholder="Email" />
        <input placeholder="Username" />
        <input type="password" placeholder="Password" />

        <select>
          <option>Student</option>
          <option>Teacher</option>
        </select>

        <button className="btn-primary">Register</button>
        <button className="btn-secondary" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  );
}
