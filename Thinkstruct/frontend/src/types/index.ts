export type Scenario = 'invalidity' | 'infringement' | 'patentability';

export interface ScenarioInfo {
  label: string;
  icon: string;
  description: string;
}

export const SCENARIO_INFO: Record<Scenario, ScenarioInfo> = {
  invalidity: {
    label: 'Invalidity Search',
    icon: '📋',
    description: 'Find prior art that could invalidate a target patent'
  },
  infringement: {
    label: 'Infringement Monitoring',
    icon: '⚠️',
    description: 'Monitor new patents for potential infringement of your rights'
  },
  patentability: {
    label: 'Patentability Review',
    icon: '💡',
    description: 'Evaluate patentability of new inventions against prior art'
  }
};

export const EXAMPLE_QUERIES: Record<Scenario, { main: string; secondary?: string; patentNumber?: string }> = {
  invalidity: {
    main: 'A vehicle wheel comprising a substrate with a face defining multiple spokes extending radially from a central hub portion',
    patentNumber: '20240051333'
  },
  infringement: {
    main: 'A tire having retractable studs for driving in icy conditions, the studs being activated by a driver control',
    secondary: 'US20240001234',
    patentNumber: '20240051333'
  },
  patentability: {
    main: 'Novel pneumatic tire structure with enhanced durability and reduced rolling resistance using graphene-reinforced rubber compounds',
    patentNumber: '20240051333'
  }
};
