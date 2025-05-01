import Navbar from '../components/Navbar';
import './Home.css';
import { useEffect, useRef } from 'react';

type Particle = {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  color: string;
};

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/login';
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Инициализация canvas
    const initCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      createParticles();
    };

    // Создание частиц
    const createParticles = () => {
      const particleCount = Math.floor((canvas.width * canvas.height) / 10000);
      particlesRef.current = Array.from({ length: particleCount }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        speedX: Math.random() * 0.5 - 0.25,
        speedY: Math.random() * 0.5 - 0.25,
        color: `rgba(0, 188, 212, ${Math.random() * 0.2 + 0.05})`
      }));
    };

    // Отрисовка кадра анимации
    const animate = () => {
      if (!canvas || !ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Обновление и отрисовка частиц
      particlesRef.current.forEach((p, i) => {
        // Обновление позиции
        p.x += p.speedX;
        p.y += p.speedY;

        // Отскок от границ
        if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
        if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

        // Отрисовка частицы
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();

        // Соединение близких частиц
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const other = particlesRef.current[j];
          const dx = p.x - other.x;
          const dy = p.y - other.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 100) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(0, 188, 212, ${1 - distance/100})`;
            ctx.lineWidth = 0.2;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        }
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    // Обработчик изменения размера
    const handleResize = () => {
      if (!canvas) return;
      cancelAnimationFrame(animationRef.current);
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      createParticles();
      animationRef.current = requestAnimationFrame(animate);
    };

    // Инициализация
    initCanvas();
    animationRef.current = requestAnimationFrame(animate);
    window.addEventListener('resize', handleResize);

    // Очистка
    return () => {
      cancelAnimationFrame(animationRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <>
      <Navbar />
      <div className="home-container">
        <canvas ref={canvasRef} className="animated-background" />
        <div className="content-wrapper">
          <h1 className="main-title">WELCOME TO PLAYITER</h1>
          <p className="subtitle">Discover your next favorite game</p>
          <button onClick={handleLogin} className="login-button">
            <span className="button-text">Let's Go</span>
            <span className="button-icon">→</span>
          </button>
        </div>
      </div>
    </>
  );
}