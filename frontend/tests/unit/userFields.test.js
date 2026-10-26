import { describe, expect, it } from 'vitest'
import {
  approvalBadgeClass,
  avatarGradient,
  emptyStaffForm,
  filterUsersByTab,
  formatApprovalStatus,
  formatLastLogin,
  getInitials,
  normalizeFieldValue,
} from '@/LWD-views/LogisticManager/userManagement/userFields'

const users = [
  { name: 'Ellen Ripley', role: 'Warehouse Manager' },
  { name: 'John Wick', role: 'Dispatcher' },
  { name: 'Arjun Mehta', role: 'Vendor', approvalStatus: 'PENDING' },
  { name: 'Asha', role: 'Customer Support' },
]

describe('user management fields', () => {
  it('lists users per tab, with pending vendors under Vendor Requests', () => {
    expect(filterUsersByTab(users, 'All Users')).toHaveLength(4)
    expect(filterUsersByTab(users, 'Vendor Requests').map((u) => u.name)).toEqual(['Arjun Mehta'])
    expect(filterUsersByTab(users, 'Managers').map((u) => u.name)).toEqual(['Ellen Ripley'])
    expect(filterUsersByTab(users, 'Support').map((u) => u.name)).toEqual(['Asha'])
  })

  it('formats initials, avatar colours, approval states and logins', () => {
    expect(getInitials('ellen louise ripley')).toBe('EL')
    expect(getInitials('')).toBe('?')
    expect(avatarGradient('Ellen')).toBe(avatarGradient('Ellen'))
    expect(formatApprovalStatus('PENDING_REVIEW')).toBe('Pending Review')
    expect(formatApprovalStatus(null)).toBe('Approved')
    expect(approvalBadgeClass('REJECTED')).toContain('text-red-600')
    expect(formatLastLogin(null)).toBe('Never')
  })

  it('starts each create form with the right role and hub', () => {
    expect(emptyStaffForm('create-driver', 'wh-1')).toMatchObject({
      role: 'Driver',
      hubId: 'wh-1',
      status: 'Active',
    })
    expect(emptyStaffForm('create-support', null).role).toBe('Customer Support')
    expect(emptyStaffForm('edit', 'wh-1')).toBeNull()
  })

  it('tidies Aadhaar, phone, PAN, IFSC and bank account input', () => {
    expect(normalizeFieldValue('aadharCard', '1234 5678 9012 99')).toBe('1234-5678-9012')
    expect(normalizeFieldValue('mobile', '9876543210')).toBe('+91 9876543210')
    expect(normalizeFieldValue('mobile', '+919876543210')).toBe('+91 9876543210')
    expect(normalizeFieldValue('panCard', 'abcde-1234f!')).toBe('ABCDE1234F')
    expect(normalizeFieldValue('ifscCode', 'sbin0001234xyz')).toBe('SBIN0001234')
    expect(normalizeFieldValue('bankAccount', '12-34 56')).toBe('123456')
    expect(normalizeFieldValue('name', 'Ravi')).toBe('Ravi')
  })
})
