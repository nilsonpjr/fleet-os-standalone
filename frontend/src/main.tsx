import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Listen for auth expiry from API client
window.addEventListener('auth:expired', () => {
  window.location.href = `${import.meta.env.BASE_URL}login`
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
