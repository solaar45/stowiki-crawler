export interface ShipWeapons {
  fore: number;
  aft: number;
  can_equip_dual_cannons: boolean;
}

export interface ShipStats {
  max_hull: number | null;
  hull_modifier: number | null;
  shield_modifier: number | null;
  impulse_modifier: number | null;
  turn_rate: number | null;
  inertia_rating: number | null;
}

export interface Ship {
  name: string;
  link: string;
  tier: number | null;
  faction: string | null;
  type: string | null;
  released: string | null;
  device_slots: number | null;
  weapons: ShipWeapons | null;
  stats: ShipStats | null;
  bridge_officers: string | null;
  console_slots: string | null;
}

export interface Faction {
  name: string;
  key: string;
  url: string;
}

export interface ApiResponse<T> {
  success: boolean;
  count?: number;
  data?: T;
  error?: string;
}

export interface ShipsResponse {
  success: boolean;
  count: number;
  faction_filter: string | null;
  ships: Ship[];
}

export interface ScrapeResponse {
  success: boolean;
  total_count?: number;
  count?: number;
  faction?: string;
  by_faction?: Record<string, number>;
  ships: Ship[];
}

export interface FactionsResponse {
  success: boolean;
  count: number;
  factions: Faction[];
}
