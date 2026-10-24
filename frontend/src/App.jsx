import "./App.css";
import { ProfilePage } from "./pages/ProfilePage";

function App() {
  return (
    <div className="app-container">
      <main className="main-content">
        <header className="page-header">
          <h1>Account Settings</h1>
          <p>Manage your institutional contact information and preferences.</p>
        </header>

        {/* Dynamically receives user session ID in future auth workflows */}
        <ProfilePage institutionalId="STU001" />
      </main>
    </div>
  );
}

export default App;