import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import GameCard from '../components/GameCard';
import { getRecommendations } from '../api/steam';
import LoadingSpinner from '../components/LoadingSpinner';
import './Recommendations.css';

interface Game {
  appid: number;
  name: string;
  store_url: string;
  categories: string[];
  recommendations: number;
  release_year?: number;
}

export default function Recommendations() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const steamId = searchParams.get('steam_id');
        if (!steamId) {
          setError('Steam ID не найден');
          return;
        }

        setLoading(true);
        const data = await getRecommendations(steamId);

        if (data.recommendations.length === 0) {
          setError('Не найдено рекомендаций. Возможно, у вас нет игр с достаточным временем игры.');
        } else {
          setGames(data.recommendations);
        }
      } catch (err) {
        setError('Ошибка загрузки рекомендаций');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [searchParams]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="recommendations-container">
      <h1>Your personal recommendations:</h1>
      <div className="games-grid">
        {games.map(game => (
          <GameCard
            key={game.appid}
            game={game}
          />
        ))}
      </div>
    </div>
  );
}