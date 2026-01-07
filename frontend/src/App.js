import { useState } from "react";
import Landing from "./components/Landing";
import Login from "./components/Login";
import Signup from "./components/Signup";
import TeacherHome from "./components/TeacherHome";
import StudentHome from "./components/StudentHome";
import Navbar from "./components/Navbar";

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(null);

  if (!user) {
    if (page === "landing")
      return (
        <Landing
          onLoginClick={() => setPage("login")}
          onSignupClick={() => setPage("signup")}
        />
      );

    if (page === "login")
      return <Login onSuccess={setUser} />;

    if (page === "signup")
      return <Signup onBack={() => setPage("landing")} />;
  }

  return (
    <>
      <Navbar user={user} onLogout={() => setUser(null)} />
      {user.role === "teacher" ? (
        <TeacherHome user={user} />
      ) : (
        <StudentHome user={user} />
      )}
    </>
  );
}
