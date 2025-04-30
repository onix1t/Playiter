import axios from 'axios';

const API_BASE = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000'
  : '/api';

interface RecommendationResponse {
  recommendations: Array<{
    appid: number;
    name: string;
    store_url: string;
    categories: string[];
    recommendations: number;
    release_year?: number;
  }>;
}

export const getRecommendations = async (steamId: string): Promise<RecommendationResponse> => {
  try {
    const response = await axios.get(`${API_BASE}/recommend/${steamId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    throw error;
  }
};