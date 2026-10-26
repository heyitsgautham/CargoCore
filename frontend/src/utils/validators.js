// Input checks shared by the sign-in and sign-up forms, so every entry point applies
// the same rules before a request leaves the browser. Each check returns a message,
// or '' when the value passes.

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PINCODE = /^\d{6}$/

export function isValidEmail(value) {
    return EMAIL.test(String(value || '').trim())
}

export function emailError(value, { required = 'Required', invalid = 'Invalid email' } = {}) {
    if (!value) return required
    return isValidEmail(value) ? '' : invalid
}

export function requiredError(value, message = 'Required') {
    return String(value ?? '').trim() ? '' : message
}

/** At least 8 characters with an upper-case letter, a lower-case letter and a digit. */
export function strongPasswordError(value) {
    if (!value) return 'Required'
    if (value.length < 8) return 'Min 8 chars'
    if (!/[A-Z]/.test(value)) return 'Need uppercase'
    if (!/[a-z]/.test(value)) return 'Need lowercase'
    if (!/\d/.test(value)) return 'Need a number'
    return ''
}

export function confirmPasswordError(password, confirmation) {
    if (!confirmation) return 'Required'
    return confirmation === password ? '' : 'Mismatch'
}

export function pincodeError(value) {
    if (!String(value || '').trim()) return 'Required'
    return PINCODE.test(value) ? '' : 'Invalid'
}

/** 0 to 5: length 8, length 12, mixed case, a digit, a symbol. */
export function passwordStrength(value) {
    if (!value) return 0
    let score = 0
    if (value.length >= 8) score++
    if (value.length >= 12) score++
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score++
    if (/\d/.test(value)) score++
    if (/[^a-zA-Z0-9]/.test(value)) score++
    return score
}
