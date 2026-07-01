import { useEffect, useState } from "react";
import "./App.css";

type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend health check failed");
        }
        return response.json();
      })
      .then((data: HealthResponse) => {
        setHealth(data);
        setError("");
      })
      .catch(() => {
        setHealth(null);
        setError("Backend is not reachable. Please start the FastAPI server.");
      });
  }, []);

  return (
    <main className="app-shell">
      <section className="hero-card">
        <p className="eyebrow">CoursePilot</p>
        <h1>Course Registration and Waitlist Management</h1>

        <p className="description">
          CoursePilot connects a React frontend with a FastAPI backend for course
          registration, waitlist management, advisor review, and student schedule tracking.
        </p>

        <div className="status-card">
          <h2>Backend Connection</h2>

          {health ? (
            <div className="status-grid">
              <div>
                <span>Status</span>
                <strong>{health.status}</strong>
              </div>
              <div>
                <span>Service</span>
                <strong>{health.service}</strong>
              </div>
              <div>
                <span>Environment</span>
                <strong>{health.environment}</strong>
              </div>
            </div>
          ) : (
            <p className="error-message">
              {error || "Checking backend status..."}
            </p>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
