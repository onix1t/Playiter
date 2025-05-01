// LoadingSpinner.tsx
import { useState, useEffect } from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  fullPage?: boolean;
  messageInterval?: number;
  spinnerColor?: string;
  textColor?: string;
  size?: 'sm' | 'md' | 'lg';
}

const loadingMessages = [
  'Собираем лучшие рекомендации для вас...',
  'Машины думают быстрее, но всё равно нужно чуть подождать...',
  'Ещё секундочку...',
  'Ищем что-то интересное...',
  'Бип! Буп! Загрузка...',
  '10100101101101010110...',
  'Почти готово!',
  'Оптимизируем результаты...',
  'Проверяем ваши предпочтения...'
];

export default function LoadingSpinner({
  fullPage = false,
  messageInterval = 10000,
  spinnerColor = '#00bcd4',
  textColor = '#ffffff',
  size = 'md'
}: LoadingSpinnerProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const messageTimer = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setMessageIndex(prev => (prev + 1) % loadingMessages.length);
        setFade(true);
      }, 300);
    }, messageInterval);

    return () => clearInterval(messageTimer);
  }, [messageInterval]);

  const sizeStyles = {
    sm: { width: '30px', height: '30px', borderWidth: '3px' },
    md: { width: '50px', height: '50px', borderWidth: '4px' },
    lg: { width: '70px', height: '70px', borderWidth: '5px' }
  };

  return (
    <div className={`spinner-wrapper ${fullPage ? 'full-page' : ''}`}>
      <div className="spinner-content">
        <div
          className="spinner"
          style={{
            borderTopColor: spinnerColor,
            borderRightColor: 'transparent',
            borderBottomColor: 'transparent',
            borderLeftColor: 'transparent',
            ...sizeStyles[size]
          }}
        />
        <p
          className={`spinner-message ${fade ? 'fade-in' : 'fade-out'}`}
          style={{ color: textColor }}
        >
          {loadingMessages[messageIndex]}
        </p>
      </div>
    </div>
  );
}