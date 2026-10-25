# Cargo-Core Frontend 🚚

This is the frontend repository for the **Cargo-Core** logistics platform, a Software Engineering Project (2026) for IIT Madras. The platform is designed to digitize and optimize workflows for small logistics businesses.

## 🚀 Tech Stack

- **Framework:** [Vue 3](https://vuejs.org/) (Composition API with `<script setup>`)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) with PostCSS
- **State Management:** [Pinia](https://pinia.vuejs.org/)
- **Routing:** [Vue Router](https://router.vuejs.org/)
- **Animations:** [GSAP](https://greensock.com/gsap/) (GreenSock Animation Platform)
- **3D Integration:** [Spline Runtime](https://spline.design/)

## 🛠️ Project Setup

### Prerequisites
Ensure you have [Node.js](https://nodejs.org/) 20 or newer installed.

### Installation
The web app is the `frontend` workspace of the npm project at the repo root, and the lockfile lives there.

```bash
# From the repo root
npm ci
```

The scripts below also work from inside `frontend/`.

### Development
Start the local development server with Hot Module Replacement (HMR):
```bash
npm run dev
```

### Production
Build the project for production:
```bash
npm run build
```

Preview the production build locally:
```bash
npm run preview
```

## ✅ Production Status

The frontend is production-ready and integrated with the backend APIs.

- Authentication and role-based dashboards are connected to backend services.
- Use your real backend-provisioned user accounts for login and testing.
- Legacy mock testing credentials are no longer used.

## 📁 Project Structure

```text
frontend/
├── src/
│   ├── assets/             # Global CSS, Spline models, icons, and static assets
│   ├── layouts/            # Dashboard and public page layout wrappers
│   ├── router/             # Vue Router configuration
│   ├── stores/             # Pinia global state management 
│   ├── utils/              # Helper functions and formatters
│   ├── components/         # Shared and global UI components
│   ├── views/              # Shared generic views 
│   ├── auth-views/         # Login and authentication views
│   └── [Role]-views/ &     # Dedicated views/components for specific roles 
│       [Role]-components/  # (e.g. Ai, IV, LWD, LWDDVI)
```

## 🔌 Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/)
- [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur)
- [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

## 🤝 Contribution

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Commit your changes: `git commit -m 'Add some feature'`
3. Push to the branch: `git push origin feature/your-feature-name`
4. Open a Pull Request.

---
*Developed by QuadCore-Devs(Team-003) @ IIT Madras (2026)*