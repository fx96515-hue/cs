/**
 * hooks/query-keys.ts
 * Alle React-Query-Cache-Keys an einem Ort.
 * Änderungen an Endpoint-Pfaden wirken sich nur hier aus.
 */
export const QK = {
  roasters: {
    all: ["roasters"] as const,
    list: (params?: object) => ["roasters", "list", params] as const,
    detail: (id: number) => ["roasters", "detail", id] as const,
  },
  cooperatives: {
    all: ["cooperatives"] as const,
    list: (params?: object) => ["cooperatives", "list", params] as const,
    detail: (id: number) => ["cooperatives", "detail", id] as const,
  },
  lots: {
    all: ["lots"] as const,
    list: (params?: object) => ["lots", "list", params] as const,
    detail: (id: number) => ["lots", "detail", id] as const,
  },
  shipments: {
    all: ["shipments"] as const,
    list: (params?: object) => ["shipments", "list", params] as const,
    detail: (id: number) => ["shipments", "detail", id] as const,
  },
  deals: {
    all: ["deals"] as const,
    list: (params?: object) => ["deals", "list", params] as const,
    detail: (id: number) => ["deals", "detail", id] as const,
  },
  alerts: {
    all: ["alerts"] as const,
    list: (params?: object) => ["alerts", "list", params] as const,
  },
} as const;
