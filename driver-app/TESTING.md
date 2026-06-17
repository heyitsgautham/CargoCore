# Driver App Testing Guide

## 🚛 Testing Login Credentials

While the backend integration is in development, you can use the following mock credentials to log in and test the driver app flow (from pre-shift inspection to job execution).

**Password:** *(You can enter any password)*

| Driver ID | Role | Initial Path |
|-----------|------|--------------|
| `DRV-2049` | **Driver** | `/pre-shift` |

## 📝 Notes
- These credentials currently bypass real authentication as auth is mocked in the frontend component.
- Entering any Driver ID other than `DRV-2049` will trigger an "Invalid Driver ID or Password" error to help you test the error state validation.
- After a successful login, the app simulates a short network delay and routes you to the Vehicle Inspection (`/pre-shift`) step.
