import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/oxanium/500.css'
import '@fontsource/oxanium/600.css'
import '@fontsource/oxanium/700.css'
import '@fontsource/manrope/400.css'
import '@fontsource/manrope/500.css'
import '@fontsource/manrope/600.css'
import '@fontsource/manrope/700.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// Installable on a phone ("Add to Home screen"); see public/sw.js.
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {});
  });
}
