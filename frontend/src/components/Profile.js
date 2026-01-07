import "./Profile.css";

export default function Profile({ user }) {
  return (
    <div className="profile-card">
      <h3>Profile</h3>
      <p><strong>Name:</strong> {user.full_name}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>Role:</strong> {user.role}</p>
    </div>
  );
}
