"use client";

import { useState, useCallback } from "react";
import { SupportedCountry, COUNTRY_CONFIGS, CountryConfig } from "../types";

const STORAGE_KEY = "coffeestudio_selected_country";
const DEFAULT_COUNTRY: SupportedCountry = "PE";

const getInitialCountry = (): SupportedCountry => {
  if (typeof window === "undefined") {
    return DEFAULT_COUNTRY;
  }
  const stored = localStorage.getItem(STORAGE_KEY) as SupportedCountry | null;
  if (stored && stored in COUNTRY_CONFIGS) {
    return stored;
  }
  return DEFAULT_COUNTRY;
};

/**
 * Hook for managing the currently selected origin country.
 * Selection is persisted to localStorage for cross-session persistence.
 * Uses a lazy initializer to read localStorage synchronously and avoid
 * a flash of the default value during hydration.
 */
export function useCountry() {
  const [selectedCountry, setSelectedCountryState] = useState<SupportedCountry>(() => getInitialCountry());

  const setSelectedCountry = useCallback((code: SupportedCountry) => {
    setSelectedCountryState(code);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, code);
    }
  }, []);

  const countryConfig: CountryConfig = COUNTRY_CONFIGS[selectedCountry];

  return {
    selectedCountry,
    setSelectedCountry,
    countryConfig,
  };
}
