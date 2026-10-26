import { localDateISO } from '@/utils/date'
// Pure helpers for the header meeting scheduler: meeting platforms, links, API record
// normalisation and the date labels shown on meeting cards.

export const detectPlatform = (url) => {
    if (!url) return 'other'
    const lower = url.toLowerCase()
    if (lower.includes('meet.jit.si')) return 'jitsi'
    if (lower.includes('meet.google.com')) return 'gmeet'
    if (lower.includes('zoom.us') || lower.includes('zoom.com')) return 'zoom'
    return 'other'
}

export const generateJitsiUrl = (topic) => {
    const slug = (topic || 'meeting')
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '')
        .substring(0, 30)
    const id = Math.random().toString(36).substring(2, 8)
    return `https://meet.jit.si/logistics-${slug}-${id}`
}

export const normalizeMeetingUrl = (value) => {
    const trimmed = String(value || '').trim()
    if (!trimmed) return ''
    if (/^https?:\/\//i.test(trimmed)) return trimmed
    if (/^(meet\.google\.com|[\w-]+\.zoom\.(us|com)|zoom\.us|zoom\.com)/i.test(trimmed)) {
        return `https://${trimmed}`
    }
    return trimmed
}

export const platformOptions = [
    {
        id: 'jitsi',
        label: 'Video Call (In-App)',
        dotColor: 'bg-violet-500',
        activeClass: 'border-violet-500 bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-400'
    },
    {
        id: 'gmeet',
        label: 'Google Meet',
        dotColor: 'bg-green-500',
        activeClass: 'border-green-500 bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400'
    },
    {
        id: 'zoom',
        label: 'Zoom',
        dotColor: 'bg-blue-500',
        activeClass: 'border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400'
    },
    {
        id: 'other',
        label: 'Other',
        dotColor: 'bg-gray-400',
        activeClass: 'border-gray-400 bg-gray-50 dark:bg-white/10 text-gray-700 dark:text-gray-300'
    }
]

export const getPlatformConfig = (type) => {
    const configs = {
        jitsi: {
            label: 'Video Call',
            badgeClass: 'bg-violet-100 dark:bg-violet-500/15 text-violet-700 dark:text-violet-400',
            dotClass: 'bg-violet-500',
            joinClass: 'bg-violet-600 hover:bg-violet-700 text-white'
        },
        gmeet: {
            label: 'Google Meet',
            badgeClass: 'bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-400',
            dotClass: 'bg-green-500',
            joinClass: 'bg-green-600 hover:bg-green-700 text-white'
        },
        zoom: {
            label: 'Zoom',
            badgeClass: 'bg-blue-100 dark:bg-blue-500/15 text-blue-700 dark:text-blue-400',
            dotClass: 'bg-blue-500',
            joinClass: 'bg-blue-600 hover:bg-blue-700 text-white'
        },
        other: {
            label: 'Meeting',
            badgeClass: 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300',
            dotClass: 'bg-gray-400',
            joinClass: 'bg-primary hover:bg-primary/90 text-white'
        }
    }
    return configs[type] || configs.other
}

export const getMeetingPlatform = (meeting) => meeting.meetingType || detectPlatform(meeting.link)

export const todayDate = () => localDateISO()
export const normalizeId = (value) => value == null ? '' : String(value)
export const titleCase = (value) => String(value || 'User')
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())

export const normalizeMeeting = (meeting) => {
    if (!meeting || typeof meeting !== 'object') return null

    const explicitType = String(meeting.meetingType || meeting.meeting_type || '').toLowerCase()
    const meetingType = ['gmeet', 'zoom', 'jitsi', 'other'].includes(explicitType)
        ? explicitType
        : detectPlatform(meeting.link)

    return {
        id: normalizeId(meeting.id),
        topic: String(meeting.topic || '').trim(),
        description: String(meeting.description || '').trim(),
        meetingType,
        link: normalizeMeetingUrl(meeting.link),
        date: String(meeting.date || ''),
        startTime: String(meeting.startTime || meeting.start_time || ''),
        endTime: String(meeting.endTime || meeting.end_time || ''),
        participants: Array.isArray(meeting.participants)
            ? meeting.participants.map(normalizeId).filter(Boolean)
            : [],
        createdById: normalizeId(meeting.createdById || meeting.created_by_id),
        warehouseId: normalizeId(meeting.warehouseId || meeting.warehouse_id),
        createdAt: String(meeting.createdAt || meeting.created_at || ''),
        updatedAt: String(meeting.updatedAt || meeting.updated_at || '')
    }
}

export const formatDate = (dateStr) => {
    const dateValue = new Date(dateStr)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (dateValue.toDateString() === today.toDateString()) return 'Today'
    if (dateValue.toDateString() === tomorrow.toDateString()) return 'Tomorrow'

    return dateValue.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export const isMeetingLive = (meeting) => {
    const now = new Date()
    const start = new Date(`${meeting.date}T${meeting.startTime}`)
    const end = new Date(`${meeting.date}T${meeting.endTime}`)
    return now >= new Date(start.getTime() - 10 * 60000) && now <= end
}
