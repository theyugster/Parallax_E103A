import { useState } from "react";
import "./Login.css";

export default function Login({ onSuccess }) {
  const [role, setRole] = useState("student");

  function submit(e) {
    e.preventDefault();
    onSuccess({
      full_name: "Demo User",
      role,
      email: "demo@edu.com"
    });
  }

  return (
    <div className="auth-container">
      <h3>Sign In</h3>

      <form onSubmit={submit} className="auth-input-group">
        <input placeholder="Username" />
        <input type="password" placeholder="Password" />

        <select onChange={(e) => setRole(e.target.value)}>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
        </select>

        <button className="btn-primary">Login</button>
      </form>
    </div>
  );
}
