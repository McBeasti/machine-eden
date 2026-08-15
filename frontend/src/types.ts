export interface Hardware {
  chassis_size: number;
  movement_speed: number;
  carrying_capacity: number;
  armour: number;
  sensor_range: number;
  communication_range: number;
  energy_capacity: number;
  energy_consumption: number;
  mining_ability: number;
  construction_ability: number;
  manufacturing_ability: number;
  attack_power: number;
  repair_ability: number;
  processing_capacity: number;
}

export interface Software {
  cooperation_tendency: number;
  aggression_tendency: number;
  exploration_tendency: number;
  risk_tolerance: number;
  resource_sharing_tendency: number;
  loyalty_tendency: number;
  mutation_rate: number;
  communication_protocol_version: number;
}

export interface Agent {
  id: string;
  x: number;
  y: number;
  generation: number;
  parent_ids: string[];
  lineage_id: string;
  created_tick: number;
  age: number;
  colony_id: string | null;
  role: string | null;
  hardware: Hardware;
  software: Software;
  energy: number;
  damage: number;
  inventory: Record<string, number>;
  current_task: string;
  alive: boolean;
  energy_ratio: number;
  decisions?: DecisionRecord[];
}

export interface DecisionRecord {
  agent_id: string;
  tick: number;
  observed_inputs: Record<string, unknown>;
  selected_action: string;
  competing_actions: string[];
  policy_scores: Record<string, number>;
  current_goal: string;
  interpretation: string;
  source: string;
}

export interface TickMetrics {
  tick: number;
  population: number;
  births: number;
  deaths: number;
  mean_energy: number;
  mean_age: number;
  total_stored_resources: number;
  world_resource_total: number;
  mining_rate: number;
  energy_production: number;
  energy_consumption: number;
  mean_lifespan_deaths: number;
  territorial_concentration: number;
  genetic_diversity: number;
  idle_fraction: number;
}

export interface SimEvent {
  tick: number;
  event_type: string;
  actor_id?: string;
  location?: [number, number];
  resources?: Record<string, number>;
  outcome?: string;
  metadata?: Record<string, unknown>;
}

export interface SimConfig {
  seed: number;
  world_width: number;
  world_height: number;
  initial_population: number;
  resource_density: number;
  renewable_rate: number;
  energy_scarcity: number;
  environmental_danger: number;
  max_agents: number;
  ticks_per_second: number;
}

export interface WorldState {
  width: number;
  height: number;
  terrain: number[][];
  resources: number[][];
}

export interface SimulationState {
  tick: number;
  running: boolean;
  speed: number;
  config: SimConfig;
  world: WorldState;
  agents: Agent[];
  metrics: TickMetrics[];
  events: SimEvent[];
}

export const TERRAIN_COLORS: Record<number, string> = {
  0: '#0a0e17',
  1: '#2d6a4f',
  2: '#5c4d3c',
  3: '#7b2cbf',
  4: '#ffd60a',
  5: '#00b4d8',
  6: '#e63946',
  7: '#6c757d',
};

export const TERRAIN_NAMES: Record<number, string> = {
  0: 'empty',
  1: 'mineral',
  2: 'metal',
  3: 'rare',
  4: 'energy_source',
  5: 'charging_station',
  6: 'hazard',
  7: 'abandoned',
};
