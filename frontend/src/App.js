import { useState, useEffect } from "react"; // Import useEffect
import Landing from "./components/Landing";
import Login from "./components/Login";
import Signup from "./components/Signup";
import TeacherHome from "./components/TeacherHome";
import StudentHome from "./components/StudentHome";
import Navbar from "./components/Navbar";

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(null);

  // 1. Check for token on application load
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetch("http://localhost:8000/users/me/", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Token invalid");
          return res.json();
        })
        .then((userData) => {
          setUser(userData); // Restore the user state
        })
        .catch(() => {
          localStorage.removeItem("token"); // Clear invalid token
          setUser(null);
        });
    }
  }, []);

  // 2. Update logout to actually remove the token
  const handleLogout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setPage("landing");
  };

  if (!user) {
    if (page === "landing")
      return (
        <Landing
          onLoginClick={() => setPage("login")}
          onSignupClick={() => setPage("signup")}
        />
      );

    if (page === "login")
      return (
        <Login
          onSuccess={setUser}
          onSignupClick={() => setPage("signup")}
          onBack={() => setPage("landing")}
        />
      );

    if (page === "signup")
      return <Signup onBack={() => setPage("landing")} />;
  }

  return (
    <>
      {/* Pass the new handleLogout function */}
      <Navbar user={user} onLogout={handleLogout} />
      {user.role === "teacher" ? (
        <TeacherHome user={user} />
      ) : (
        <StudentHome user={user} />
      )}
    </>
  );
}