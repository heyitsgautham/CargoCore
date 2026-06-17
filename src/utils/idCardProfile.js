const ROLE_CARD_CONFIG = {
  LOGISTIC_MANAGER: {
    prefix: 'LOG',
    defaultDesignation: 'Logistics Manager',
    department: 'Logistics Operations',
    cardTitle: 'Employee ID Card',
    infoTitle: 'Employee Information',
    footerBadge: 'Staff Access',
    support: {
      name: 'Logistics Support Desk',
      relation: 'Control Tower',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore People Ops',
      title: 'Corporate Administration',
    },
  },
  WAREHOUSE_MANAGER: {
    prefix: 'WH',
    defaultDesignation: 'Warehouse Manager',
    department: 'Warehouse Operations',
    cardTitle: 'Employee ID Card',
    infoTitle: 'Employee Information',
    footerBadge: 'Warehouse Access',
    support: {
      name: 'Warehouse Support Desk',
      relation: 'Operations Help',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore People Ops',
      title: 'Warehouse Administration',
    },
  },
  DISPATCHER: {
    prefix: 'DP',
    defaultDesignation: 'Dispatcher',
    department: 'Dispatch Operations',
    cardTitle: 'Employee ID Card',
    infoTitle: 'Employee Information',
    footerBadge: 'Dispatch Access',
    support: {
      name: 'Dispatch Support Desk',
      relation: 'Operations Help',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore People Ops',
      title: 'Dispatch Administration',
    },
  },
  DRIVER: {
    prefix: 'DRV',
    defaultDesignation: 'Driver',
    department: 'Fleet Operations',
    cardTitle: 'Employee ID Card',
    infoTitle: 'Employee Information',
    footerBadge: 'Fleet Access',
    support: {
      name: 'Fleet Support Desk',
      relation: 'Driver Help',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore Fleet Desk',
      title: 'Transport Operations',
    },
  },
  VENDOR: {
    prefix: 'VND',
    defaultDesignation: 'Vendor Partner',
    department: 'Commercial Vendor',
    cardTitle: 'Business ID Card',
    infoTitle: 'Business Information',
    footerBadge: 'Partner Access',
    support: {
      name: 'Vendor Success Desk',
      relation: 'Account Support',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore Partner Desk',
      title: 'Vendor Onboarding',
    },
  },
  INDIVIDUAL: {
    prefix: 'CUS',
    defaultDesignation: 'Customer',
    department: 'Personal Moves',
    cardTitle: 'Customer ID Card',
    infoTitle: 'Customer Information',
    footerBadge: 'Customer Access',
    support: {
      name: 'Customer Support Desk',
      relation: 'Move Assistance',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore Customer Desk',
      title: 'Customer Success',
    },
  },
  AI_SUPPORT: {
    prefix: 'AI',
    defaultDesignation: 'Internal Support AI',
    department: 'Internal AI Support',
    cardTitle: 'System ID Card',
    infoTitle: 'System Information',
    footerBadge: 'System Access',
    support: {
      name: 'Platform Operations',
      relation: 'Incident Response',
      phone: 'Internal routing only',
    },
    authorizedBy: {
      name: 'CargoCore Platform Security',
      title: 'System Governance',
    },
  },
  DEFAULT: {
    prefix: 'USR',
    defaultDesignation: 'CargoCore User',
    department: 'CargoCore Network',
    cardTitle: 'Identity Card',
    infoTitle: 'Profile Information',
    footerBadge: 'Verified Access',
    support: {
      name: 'CargoCore Support Desk',
      relation: 'Help Center',
      phone: 'Available via CargoCore support portal',
    },
    authorizedBy: {
      name: 'CargoCore Operations',
      title: 'Access Management',
    },
  },
}

function normalizeRole(role) {
  const normalized = String(role || '')
    .trim()
    .replace(/\s+/g, '_')
    .replace(/-/g, '_')
    .toUpperCase()
  if (normalized === 'LOGISTICS_MANAGER') return 'LOGISTIC_MANAGER'
  if (normalized === 'CUSTOMER') return 'INDIVIDUAL'
  if (normalized === 'AI_AGENT' || normalized === 'CUSTOMER_SUPPORT') return 'AI_SUPPORT'
  return normalized
}

function formatCardDate(value, fallback = 'Active account') {
  if (!value) return fallback
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return fallback
  return parsed.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

function deriveCardId(prefix, rawId) {
  if (!rawId) return `${prefix}-USER`
  const compact = String(rawId).replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 8)
  return compact ? `${prefix}-${compact}` : `${prefix}-USER`
}

export function buildIdCardProfile({
  user = {},
  role,
  roleLabel,
  name,
  designation,
  department,
  address,
  phone,
  email,
  joinDate,
  validUntil,
  emergencyContact,
  authorizedBy,
  cardTitle,
  infoTitle,
  footerBadge,
} = {}) {
  const normalizedRole = normalizeRole(role || user?.role)
  const config = ROLE_CARD_CONFIG[normalizedRole] || ROLE_CARD_CONFIG.DEFAULT

  return {
    name: name || user?.name || user?.fullName || user?.company_name || 'CargoCore User',
    id: deriveCardId(config.prefix, user?.id),
    designation: designation || roleLabel || config.defaultDesignation,
    department: department || config.department,
    address: address || user?.address || user?.business_address || 'On file with CargoCore',
    phone: phone || user?.phone || user?.business_phone || 'Managed via registered account',
    email: email || user?.email || user?.business_email || 'support@cargocore.local',
    joinDate: joinDate || formatCardDate(user?.created_at || user?.createdAt || user?.joiningDate || user?.joinDate),
    validUntil: validUntil || 'Active while account is enabled',
    emergencyContact: emergencyContact || config.support,
    authorizedBy: authorizedBy || config.authorizedBy,
    cardTitle: cardTitle || config.cardTitle,
    infoTitle: infoTitle || config.infoTitle,
    footerBadge: footerBadge || config.footerBadge,
  }
}

export { formatCardDate }
