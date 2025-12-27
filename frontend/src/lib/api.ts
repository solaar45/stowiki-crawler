import type { Ship, ShipsResponse, ScrapeResponse, FactionsResponse } from '../types/ship';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async getShips(faction?: string): Promise<ShipsResponse> {
    const query = faction ? `?faction=${encodeURIComponent(faction)}` : '';
    return this.request<ShipsResponse>(`/ships${query}`);
  }

  async scrapeAllFactions(): Promise<ScrapeResponse> {
    return this.request<ScrapeResponse>('/scrape/all');
  }

  async scrapeFaction(factionKey: string): Promise<ScrapeResponse> {
    return this.request<ScrapeResponse>(`/scrape/${factionKey}`);
  }

  async getFactions(): Promise<FactionsResponse> {
    return this.request<FactionsResponse>('/factions');
  }

  async getShipCount(): Promise<{ success: boolean; count: number }> {
    return this.request('/ships/count');
  }

  async downloadShips(faction?: string): Promise<Blob> {
    const query = faction ? `?faction=${encodeURIComponent(faction)}` : '';
    const url = `${this.baseUrl}/ships/download${query}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.blob();
  }

  async healthCheck(): Promise<{ status: string; storage: string }> {
    return this.request('/health');
  }
}

export const api = new ApiClient(API_BASE_URL);
