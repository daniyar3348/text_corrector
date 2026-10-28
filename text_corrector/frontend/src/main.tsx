import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import ModelVisualization from './pages/ModelVisualization'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* BASE_URL is the sub-path the site is served from (e.g. GitHub Pages) */}
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/visualization" element={<ModelVisualization />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
