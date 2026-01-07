import { useState } from "react";
import "./Login.css";

export default function Login({ onSuccess, onSignupClick, onBack }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function submit(e) {
    e.preventDefault();

    // 1. Prepare Form Data (Required by OAuth2PasswordRequestForm in backend)
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      // 2. Fetch Token
      const tokenRes = await fetch("http://localhost:8000/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!tokenRes.ok) throw new Error("Login failed");

      const tokenData = await tokenRes.json();
      const accessToken = tokenData.access_token;

      // 3. Save Token (Simplistic: localStorage)
      localStorage.setItem("token", accessToken);

      // 4. Fetch User Details immediately using the new token
      const userRes = await fetch("http://localhost:8000/users/me/", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!userRes.ok) throw new Error("Could not fetch user profile");

      const userData = await userRes.json();

      // 5. Pass real user data up to App.js
      onSuccess(userData); 

    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div className="auth-container">
      <h3>Sign In</h3>
      <form onSubmit={submit} className="auth-input-group">
        <input 
          placeholder="Username" 
          onChange={(e) => setUsername(e.target.value)} 
        />
        <input 
          type="password" 
          placeholder="Password" 
          onChange={(e) => setPassword(e.target.value)} 
        />
        <button className="btn-primary">Login</button>
      </form>
      <div className="auth-footer">
        <p>
          Don't have an account?{' '}
          <button type="button" className="link-button" onClick={() => onSignupClick && onSignupClick()}>
            Sign up
          </button>
        </p>
        <p>
          <button type="button" className="link-button" onClick={() => onBack && onBack()}>
            Back to landing
          </button>
        </p>
      </div>
    </div>
  );
}