/**
 * API client for STO Wiki Crawler backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface Ship {
  ship: string;
  faction?: string;
  tier?: string;
  type?: string;
  hull?: string;
  shields?: string;
  crew?: string;
  weapons_fore?: string;
  weapons_aft?: string;
  device_slots?: string;
  consoles_tactical?: string;
  consoles_engineering?: string;
  consoles_science?: string;
  turn_rate?: string;
  impulse_modifier?: string;
  inertia?: string;
  warp_core?: string;
  bonus_power?: string;
  bridge_officers?: string;
  link?: string;
}

export interface ShipsResponse {
  success: boolean;
  count: number;
  faction_filter?: string;
  ships: Ship[];
}

export interface ShipsMetadata {
  success: boolean;
  last_scraped: string | null;
  age_hours: number | null;
  ship_count: number;
  factions_scraped: string[];
  needs_refresh: boolean;
  is_scraping: boolean;
}

export interface ApiInfo {
  name: string;
  version: string;
  scraper: string;
  wiki_source: string;
  storage: string;
  cache_enabled: boolean;
  auto_refresh_enabled: boolean;
}

export interface Faction {
  name: string;
  key: string;
  url: string;
}

export const api = {
  /**
   * Get API information
   */
  getInfo: async (): Promise<ApiInfo> => {
    const response = await fetch(`${API_BASE_URL}/`);
    return response.json();
  },

  /**
   * Get all ships (optionally filtered by faction)
   */
  getShips: async (faction?: string): Promise<ShipsResponse> => {
    const url = faction
      ? `${API_BASE_URL}/ships?faction=${encodeURIComponent(faction)}`
      : `${API_BASE_URL}/ships`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get ships metadata (last scraped, age, etc.)
   */
  getShipsMetadata: async (): Promise<ShipsMetadata> => {
    const response = await fetch(`${API_BASE_URL}/ships/metadata`);
    return response.json();
  },

  /**
   * Trigger auto-refresh if data is stale
   */
  autoRefresh: async (maxAgeHours: number = 24): Promise<{ success: boolean; message: string; refreshing: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/ships/auto-refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_age_hours: maxAgeHours }),
    });
    return response.json();
  },

  /**
   * Get all available factions
   */
  getFactions: async (): Promise<{ success: boolean; factions: Faction[] }> => {
    const response = await fetch(`${API_BASE_URL}/factions`);
    return response.json();
  },

  /**
   * Scrape all factions (manual trigger)
   */
  scrapeAllFactions: async (): Promise<ShipsResponse> => {
    const response = await fetch(`${API_BASE_URL}/scrape/all`);
    return response.json();
  },

  /**
   * Scrape specific faction
   */
  scrapeFaction: async (faction: string): Promise<ShipsResponse> => {
    const response = await fetch(`${API_BASE_URL}/scrape/${faction}`);
    return response.json();
  },

  /**
   * Download ships as JSON file
   */
  downloadShips: (faction?: string): void => {
    const url = faction
      ? `${API_BASE_URL}/ships/download?faction=${encodeURIComponent(faction)}`
      : `${API_BASE_URL}/ships/download`;
    window.open(url, '_blank');
  },
};