function normalizeLines(value) {
  return String(value || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
}

const RECIPIENT_PATTERNS = [
  /^Delivered to:\s*(.+)$/i,
  /^Signed off by:\s*(.+)$/i,
  /^Recipient:\s*(.+)$/i,
]

export function parsePodDeliveryNotes(value) {
  const lines = normalizeLines(value)
  let recipientName = null
  const notes = []

  for (const line of lines) {
    const matchedPattern = RECIPIENT_PATTERNS.find((pattern) => pattern.test(line))
    if (matchedPattern) {
      const match = line.match(matchedPattern)
      if (match?.[1]?.trim()) {
        recipientName = match[1].trim()
        continue
      }
    }

    notes.push(line)
  }

  return {
    recipientName,
    notes: notes.join('\n') || null,
  }
}

export function getPodPhotos(source) {
  const pod = source?.pod

  if (Array.isArray(pod?.photos)) {
    return pod.photos.filter(Boolean)
  }

  if (pod?.photo) {
    return [pod.photo]
  }

  if (Array.isArray(source?.pod_photos)) {
    return source.pod_photos.filter(Boolean)
  }

  return []
}

export function getPodSignature(source) {
  return source?.pod?.signature || source?.poc_signature || source?.pod_signature || null
}

export function buildPodData(
  source,
  {
    timestamp = 'Delivered',
    location = '—',
    signedByFallback = 'Receiver',
  } = {}
) {
  const pod = source?.pod || {}
  const parsedNotes = parsePodDeliveryNotes(pod.notes ?? source?.delivery_notes ?? source?.deliveryNotes)
  const photos = getPodPhotos(source)
  const signature = getPodSignature(source)
  const signedBy =
    pod.signedBy ||
    parsedNotes.recipientName ||
    source?.customer_name ||
    source?.customerName ||
    signedByFallback

  const timeLabel = pod.time || pod.timestamp || timestamp

  return {
    photo: pod.photo || photos[0] || null,
    photos,
    photoCount: photos.length,
    signature,
    signatureCaptured: Boolean(signature),
    timestamp: pod.timestamp || timeLabel,
    time: timeLabel,
    location: pod.location || location || '—',
    signedBy,
    recipient: signedBy,
    notes: pod.notes || parsedNotes.notes || null,
    confirmed: pod.confirmed ?? true,
  }
}
