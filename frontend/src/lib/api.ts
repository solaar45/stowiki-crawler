/**
 * STOWiki Cargo API Client
 * 
 * Direct access to STOWiki's Cargo database via structured API.
 * No scraping needed - just query the database!
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export interface Ship {
  // Basic info
  name: string;
  image?: string;
  image2?: string;
  released?: string;
  internalname?: string;

  // Faction
  faction: string[];  // Array of factions
  factionlede?: string;  // Primary faction
  facsort?: string;

  // Tier & Rank
  tier?: number;
  rank?: string;
  ranklevel?: number;
  upgradecost?: string;

  // Ship type
  type: string[];  // Array of types
  displayprefix?: string;
  displayclass?: string;
  displaytype?: string;

  // Stats
  hull?: number;
  hullmod?: number;
  shieldmod?: number;
  turnrate?: number;
  impulse?: number;
  inertia?: number;

  // Power
  powerall?: number;
  powerweapons?: number;
  powershields?: number;
  powerengines?: number;
  powerauxiliary?: number;
  powerboost?: number;

  // Bridge Officers
  boffs?: string;

  // Weapons
  fore?: number;
  aft?: number;
  equipcannons?: string;  // "yes" or "no"

  // Equipment
  devices?: number;
  consolestac?: number;
  consoleseng?: number;
  consolessci?: number;
  consolesuni?: number;
  uniconsole?: string;
  t5uconsole?: string;
  experimental?: number;  // 0 or 1
  secdeflector?: number;  // 0 or 1
  hangars?: number;

  // Cost & Abilities
  cost?: string;
  abilities?: string;

  // Admiralty
  admiraltyeng?: number;
  admiraltytac?: number;
  admiraltysci?: number;

  // Internal
  fc?: number;

  // Computed properties (from backend)
  wiki_url: string;
  image_url?: string;
  can_use_cannons: boolean;
  total_consoles: number;
  total_weapons: number;
  has_hangar: boolean;
  has_experimental_weapon: boolean;
  has_secondary_deflector: boolean;
  is_carrier: boolean;
  display_name: string;
}

export interface ShipsResponse {
  success: boolean;
  count: number;
  filters?: {
    faction?: string;
    tier?: number;
    type?: string;
  };
  ships: Ship[];
}

export interface ShipResponse {
  success: boolean;
  ship: Ship;
}

export interface SearchResponse {
  success: boolean;
  query: string;
  count: number;
  results: Ship[];
}

export interface Faction {
  name: string;
  count: number;
  key: string;
}

export interface FactionsResponse {
  success: boolean;
  total: number;
  factions: Faction[];
}

export interface TypesResponse {
  success: boolean;
  count: number;
  types: string[];
}

export interface ApiInfo {
  name: string;
  version: string;
  description: string;
  data_source: string;
  wiki_url: string;
  advantages: string[];
  endpoints: Record<string, string>;
}

export interface ErrorResponse {
  success: false;
  error: string;
}

/**
 * Cargo API Client
 */
class CargoAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get API information
   */
  async getInfo(): Promise<ApiInfo> {
    const response = await fetch(`${this.baseUrl}/`);
    return response.json();
  }

  /**
   * Health check
   */
  async health(): Promise<{ status: string; api: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  /**
   * Get all ships with optional filtering
   * 
   * @param filters Optional filters (faction, tier, type, limit)
   * @returns Promise with ships response
   * 
   * @example
   * // Get all ships
   * const ships = await api.getShips();
   * 
   * // Get Dominion ships only
   * const dominion = await api.getShips({ faction: "dominion" });
   * 
   * // Get Tier 6 escorts
   * const t6escorts = await api.getShips({ tier: 6, type: "escort" });
   */
  async getShips(filters?: {
    faction?: string;
    tier?: number;
    type?: string;
    limit?: number;
  }): Promise<Ship[]> {
    const params = new URLSearchParams();

    if (filters?.faction) params.append("faction", filters.faction);
    if (filters?.tier) params.append("tier", filters.tier.toString());
    if (filters?.type) params.append("type", filters.type);
    if (filters?.limit) params.append("limit", filters.limit.toString());

    const url = `${this.baseUrl}/api/ships${params.toString() ? `?${params}` : ""}`;
    const response = await fetch(url);
    const data: ShipsResponse = await response.json();

    if (!data.success) {
      throw new Error((data as unknown as ErrorResponse).error);
    }

    return data.ships;
  }

  /**
   * Get single ship by exact name
   * 
   * @param name Ship name (will be URL-encoded)
   * @returns Promise with ship details
   * 
   * @example
   * const ship = await api.getShip("Jem'Hadar Strike Ship");
   */
  async getShip(name: string): Promise<Ship> {
    const response = await fetch(
      `${this.baseUrl}/api/ships/${encodeURIComponent(name)}`
    );
    const data: ShipResponse = await response.json();

    if (!data.success) {
      throw new Error((data as unknown as ErrorResponse).error);
    }

    return data.ship;
  }

  /**
   * Search ships by name (fuzzy match)
   * 
   * @param query Search query
   * @param limit Maximum results (default 100)
   * @returns Promise with matching ships
   * 
   * @example
   * const results = await api.searchShips("enterprise");
   * const jemhadar = await api.searchShips("jem'hadar", 20);
   */
  async searchShips(query: string, limit: number = 100): Promise<Ship[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    const response = await fetch(`${this.baseUrl}/api/ships/search?${params}`);
    const data: SearchResponse = await response.json();

    if (!data.success) {
      throw new Error((data as unknown as ErrorResponse).error);
    }

    return data.results;
  }

  /**
   * Get faction summary with ship counts
   * 
   * @returns Promise with faction list and counts
   * 
   * @example
   * const factions = await api.getFactions();
   * // [{ name: "Dominion", count: 43, key: "dominion" }, ...]
   */
  async getFactions(): Promise<Faction[]> {
    const response = await fetch(`${this.baseUrl}/api/factions`);
    const data: FactionsResponse = await response.json();

    if (!data.success) {
      throw new Error((data as unknown as ErrorResponse).error);
    }

    return data.factions;
  }

  /**
   * Get all unique ship types
   * 
   * @returns Promise with ship type list
   * 
   * @example
   * const types = await api.getShipTypes();
   * // ["Carrier", "Cruiser", "Destroyer", "Escort", ...]
   */
  async getShipTypes(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/api/types`);
    const data: TypesResponse = await response.json();

    if (!data.success) {
      throw new Error((data as unknown as ErrorResponse).error);
    }

    return data.types;
  }

  /**
   * Download ships as JSON file
   * 
   * @param faction Optional faction filter
   * 
   * @example
   * api.downloadShips();  // All ships
   * api.downloadShips("dominion");  // Dominion only
   */
  downloadShips(faction?: string): void {
    const params = faction ? `?faction=${encodeURIComponent(faction)}` : "";
    const url = `${this.baseUrl}/api/ships/download${params}`;
    window.open(url, "_blank");
  }
}

export const api = new CargoAPIClient();
