import './Home.css';

export default function Home() {
  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/login';
  };

  return (
    <div className="home-container">
      <h1>PlayIter</h1>
      <p className="subtitle">Find your personal games in Steam</p>
      <button
        onClick={handleLogin}
        className="login-button"
      >
        Let's Go!
      </button>
    </div>
  );
}