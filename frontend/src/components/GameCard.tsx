import './GameCard.css';

interface GameCardProps {
  game: {
    appid: number;
    name: string;
    store_url: string;
    categories: string[];
    release_year?: number;
    recommendations: number;
  };
}

export default function GameCard({ game }: GameCardProps) {
  return (
    <a
      href={game.store_url}
      target="_blank"
      rel="noopener noreferrer"
      className="game-card"
    >
      <div className="game-image-container">
        <img
          src={`https://cdn.cloudflare.steamstatic.com/steam/apps/${game.appid}/header.jpg`}
          alt={game.name}
          className="game-image"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder-game.jpg';
          }}
        />
      </div>
      <div className="game-info">
        <h3 className="game-title">{game.name}</h3>
        <div className="game-meta">
          {game.release_year && (
            <span className="game-year">{game.release_year}</span>
          )}
          <span className="game-reviews">👍 {game.recommendations.toLocaleString()}</span>
        </div>
        <div className="game-categories">
          {game.categories.slice(0, 3).map(category => (
            <span key={category} className="game-category">{category}</span>
          ))}
        </div>
      </div>
    </a>
  );
}