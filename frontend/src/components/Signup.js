import { useState } from "react";
import "./Signup.css";

export default function Signup({ onBack }) {
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    username: "",
    password: "",
    role: "student" // Default role
  });

  function handleChange(e) {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  }

  async function handleRegister(e) {
    e.preventDefault(); // Prevent page reload

    try {
      // 1. Send POST request to your backend
      const response = await fetch("http://localhost:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });

      // 2. Handle Errors
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      // 3. Success!
      alert("Account created successfully! Please Sign In.");
      onBack(); // Returns to the Landing/Login page

    } catch (error) {
      alert("Error: " + error.message);
    }
  }

  return (
    <div className="auth-container">
      <h3>Create Account</h3>

      <div className="auth-input-group">
        <input 
          name="full_name" 
          placeholder="Full Name" 
          onChange={handleChange} 
          value={formData.full_name}
        />
        <input 
          name="email" 
          placeholder="Email" 
          onChange={handleChange} 
          value={formData.email}
        />
        <input 
          name="username" 
          placeholder="Username" 
          onChange={handleChange} 
          value={formData.username}
        />
        <input 
          name="password" 
          type="password" 
          placeholder="Password" 
          onChange={handleChange} 
          value={formData.password}
        />

        <select name="role" onChange={handleChange} value={formData.role}>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
        </select>

        <button className="btn-primary" onClick={handleRegister}>
          Register
        </button>
        <button className="btn-secondary" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  );
}