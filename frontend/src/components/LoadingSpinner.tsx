import './LoadingSpinner.css';

export default function LoadingSpinner() {
  return (
    <div className="spinner-container">
      <div className="loading-spinner"></div>
      <p>Загружаем ваши рекомендации...</p>
    </div>
  );
}