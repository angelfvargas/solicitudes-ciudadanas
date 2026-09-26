// Fechas en el formato del ejemplo de la prueba: 10/09/2026 08:30 (hora local, 24 horas).
const pad = (n: number) => String(n).padStart(2, '0')

export function formatDate(iso: string): string {
  const d = new Date(iso)
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso)
  return `${formatDate(iso)} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
