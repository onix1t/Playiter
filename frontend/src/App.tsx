import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Recommendations from './pages/Recommendations';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Routes>
    </BrowserRouter>
  );
}