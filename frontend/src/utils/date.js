/**
 * YYYY-MM-DD for a moment in the browser's own time zone.
 * toISOString() gives the UTC date instead, which is yesterday in India until 5:30 AM,
 * and turns local midnight into the previous day.
 */
export function localDateISO(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
