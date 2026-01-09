import './App.css'

import { Navigate, Route, Routes } from 'react-router-dom'

import { getAccessToken } from './api/client'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import TeamPage from './pages/TeamPage'


function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = getAccessToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/home" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/team"
        element={
          <RequireAuth>
            <TeamPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  )
}

export default App
