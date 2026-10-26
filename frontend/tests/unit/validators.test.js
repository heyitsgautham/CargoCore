import { describe, expect, it } from 'vitest'
import {
  confirmPasswordError,
  emailError,
  isValidEmail,
  passwordStrength,
  pincodeError,
  requiredError,
  strongPasswordError,
} from '@/utils/validators'

describe('form validators', () => {
  it('checks emails', () => {
    expect(isValidEmail(' asha@example.com ')).toBe(true)
    expect(isValidEmail('asha@example')).toBe(false)
    expect(emailError('')).toBe('Required')
    expect(emailError('', { required: 'Email is required' })).toBe('Email is required')
    expect(emailError('nope')).toBe('Invalid email')
    expect(emailError('a@b.co')).toBe('')
  })

  it('names the first rule a weak password breaks', () => {
    expect(strongPasswordError('')).toBe('Required')
    expect(strongPasswordError('Ab1')).toBe('Min 8 chars')
    expect(strongPasswordError('abcdefg1')).toBe('Need uppercase')
    expect(strongPasswordError('ABCDEFG1')).toBe('Need lowercase')
    expect(strongPasswordError('Abcdefgh')).toBe('Need a number')
    expect(strongPasswordError('Abcdefg1')).toBe('')
    expect(confirmPasswordError('Abcdefg1', '')).toBe('Required')
    expect(confirmPasswordError('Abcdefg1', 'Abcdefg2')).toBe('Mismatch')
  })

  it('checks required fields and six-digit pincodes', () => {
    expect(requiredError('   ')).toBe('Required')
    expect(requiredError('x')).toBe('')
    expect(pincodeError('56001')).toBe('Invalid')
    expect(pincodeError('560001')).toBe('')
    expect(pincodeError('')).toBe('Required')
  })

  it('scores passwords from 0 to 5', () => {
    expect(passwordStrength('')).toBe(0)
    expect(passwordStrength('abcdefgh')).toBe(1)
    expect(passwordStrength('Abcdefgh1!xyz')).toBe(5)
  })
})
