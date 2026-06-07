// Shared domain types for the Obee extension. These mirror the relevant
// CoffeeStudio API contracts (see apps/api/app/domains/{auth,roasters}).

export interface UserOut {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: UserOut;
  baseUrl: string;
}

/** Heuristic data extracted from the active tab before the user confirms it. */
export interface ExtractedPage {
  title: string;
  sourceUrl: string;
  name?: string;
  website?: string;
  contactEmail?: string;
  description?: string;
}

/** Editable payload the popup sends back; mapped onto RoasterCreate. */
export interface RoasterDraft {
  name: string;
  website?: string;
  city?: string;
  contact_email?: string;
  peru_focus: boolean;
  notes?: string;
  meta?: Record<string, unknown>;
}

export interface RoasterCreated {
  id: number;
  name: string;
}
