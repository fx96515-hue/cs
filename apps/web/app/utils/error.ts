import { ApiError } from "../../lib/api";

/**
 * Wandelt einen unbekannten Fehler in einen lesbaren deutschen String um.
 * Erkennt ApiError-Instanzen und gibt kontextreiche Meldungen zurück.
 */
export function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isUnauthorized) return "Sitzung abgelaufen. Bitte erneut anmelden.";
    if (error.isForbidden)    return "Keine Berechtigung für diese Aktion.";
    if (error.isNotFound)     return "Datensatz nicht gefunden.";
    if (error.isValidation)   return `Ungültige Eingabe: ${error.message}`;
    if (error.isServerError)  return `Serverfehler (${error.status}). Bitte später erneut versuchen.`;
    return error.message;
  }
  if (error instanceof Error) {
    if (error.message.includes("fetch") || error.message.includes("network")) {
      return "Backend nicht erreichbar. Bitte Verbindung prüfen.";
    }
    return error.message;
  }
  return String(error);
}
