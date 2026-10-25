import { useState } from "react";
import "./App.css";
import { ProfilePage } from "./pages/ProfilePage";
import { CourseCatalogPage } from "./pages/CourseCatalogPage";

function App() {
  const [view, setView] = useState("profile");

  return (
    <>
      <nav className="app-tabs" aria-label="Main">
        <button
          type="button"
          className="app-tab"
          onClick={() => setView("profile")}
          aria-current={view === "profile" ? "page" : undefined}
        >
          Account Settings
        </button>
        <button
          type="button"
          className="app-tab"
          onClick={() => setView("courses")}
          aria-current={view === "courses" ? "page" : undefined}
        >
          Course Catalog
        </button>
      </nav>

      {view === "profile" ? (
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
      ) : (
        <CourseCatalogPage institutionalId="STU001" />
      )}
    </>
  );
}

export default App;
