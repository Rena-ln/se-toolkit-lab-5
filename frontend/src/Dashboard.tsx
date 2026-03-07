// src/App.tsx
import { useState } from 'react';
import Dashboard from './Dashboard';

// Import your ItemsTable component - adjust the path as needed
// If you don't have it yet, you can create a placeholder
import ItemsTable from './ItemsTable';

type Page = 'items' | 'dashboard';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('items');

  const handlePageChange = (page: Page) => {
    setCurrentPage(page);
  };

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="nav-brand">
          <h1>Learning Management System</h1>
        </div>
        <div className="nav-links">
          <button
            className={`nav-button ${currentPage === 'items' ? 'active' : ''}`}
            onClick={() => handlePageChange('items')}
            type="button"
          >
            Items
          </button>
          <button
            className={`nav-button ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => handlePageChange('dashboard')}
            type="button"
          >
            Dashboard
          </button>
        </div>
      </nav>

      <main className="app-main">
        {currentPage === 'items' ? <ItemsTable /> : <Dashboard />}
      </main>

      <style>{`
        .app {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .app-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 2rem;
          background-color: #2c3e50;
          color: white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .nav-brand h1 {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 500;
        }

        .nav-links {
          display: flex;
          gap: 1rem;
        }

        .nav-button {
          padding: 0.5rem 1.5rem;
          font-size: 1rem;
          border: none;
          border-radius: 4px;
          background-color: transparent;
          color: rgba(255,255,255,0.8);
          cursor: pointer;
          transition: all 0.3s ease;
          font-weight: 500;
        }

        .nav-button:hover {
          background-color: rgba(255,255,255,0.1);
          color: white;
        }

        .nav-button.active {
          background-color: #3498db;
          color: white;
        }

        .app-main {
          flex: 1;
          background-color: #f5f6fa;
        }

        @media (max-width: 768px) {
          .app-nav {
            flex-direction: column;
            gap: 1rem;
            padding: 1rem;
          }

          .nav-brand h1 {
            font-size: 1.2rem;
          }
        }
      `}</style>
    </div>
  );
}

export default App;
