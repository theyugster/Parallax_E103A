import "./Navbar.css";

export default function Navbar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <h2 className="logo">EduVector</h2>
      <div className="nav-right">
        <span className="role">{user.role}</span>
        <button onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}
