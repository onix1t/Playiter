import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import GameCard from '../components/GameCard';
import { getRecommendations } from '../api/steam';
import LoadingSpinner from '../components/LoadingSpinner';
import Navbar from '../components/Navbar';
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
          setError('Steam ID not found. Please try logging in again.');
          return;
        }

        setLoading(true);
        const data = await getRecommendations(steamId);

        if (data.recommendations.length === 0) {
          setError('No recommendations found. You may need to play more games to get personalized recommendations.');
        } else {
          setGames(data.recommendations);
        }
      } catch (err) {
        setError('Failed to load recommendations. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [searchParams]);

  if (loading) return <LoadingSpinner fullPage />;

  if (error) return (
    <>
      <Navbar />
      <div className="recommendations-container">
        <div className="error-message">
          <h3>Oops!</h3>
          <p>{error}</p>
        </div>
      </div>
    </>
  );

  return (
    <>
      <Navbar />
      <div className="recommendations-container">
        <h1>Your Personal Recommendations</h1>
        {games.length > 0 && (
          <p style={{ textAlign: 'center', marginBottom: '2rem', color: '#aaa' }}>
            Based on your Steam library and playtime
          </p>
        )}
        <div className="games-grid">
          {games.map((game) => (
            <GameCard key={game.appid} game={game} />
          ))}
        </div>
      </div>
    </>
  );
}