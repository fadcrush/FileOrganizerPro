# FileOrganizer Pro - Web Dashboard

Modern, futuristic web interface for FileOrganizer Pro built with React, TypeScript, and Tailwind CSS.

## 🎨 Features

- **Glassmorphism Design**: Modern UI with frosted glass effects
- **Cyberpunk Aesthetics**: Neon colors (cyan, magenta, green) with glow effects
- **Real-time Updates**: WebSocket integration for live job progress
- **Responsive Layout**: Works seamlessly on desktop, tablet, and mobile
- **Dark Theme**: Eye-friendly dark space theme
- **Smooth Animations**: Framer Motion for buttery-smooth transitions

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on `http://localhost:8000` (optional for demo)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The app will be available at `http://localhost:3000`

## 🏗️ Project Structure

```
src/
├── components/
│   └── layout/
│       ├── MainLayout.tsx       # Main app layout
│       ├── Sidebar.tsx          # Navigation sidebar
│       └── TopBar.tsx           # Top navigation bar
├── pages/
│   ├── Dashboard.tsx            # Main dashboard
│   ├── FilesView.tsx            # File management
│   ├── OrganizeView.tsx         # Organization jobs
│   ├── DuplicatesView.tsx       # Duplicate detection
│   ├── AnalyticsView.tsx        # Analytics & insights
│   ├── SettingsView.tsx         # User settings
│   └── LoginPage.tsx            # Authentication
├── store/
│   └── authStore.ts             # Zustand auth state
├── App.tsx                      # App root with routing
├── main.tsx                     # Entry point
└── index.css                    # Global styles & Tailwind

## 🎯 Demo Mode

The dashboard includes a **demo mode** for testing:

1. Go to the login page
2. Enter **any email and password**
3. Click "Sign In"
4. Explore the dashboard with demo data

No backend required for demo!

## 🎨 Color Scheme

### Cyberpunk Dark Theme

- **Background**: `#0a0e27` (Deep space)
- **Surface**: `#1a1f3a` (Dark navy)
- **Accent Cyan**: `#00f7ff` (Neon cyan)
- **Accent Magenta**: `#ff00ff` (Neon magenta)
- **Accent Green**: `#00ff41` (Matrix green)

### Glassmorphism Effects

```css
.glass-card {
  background: rgba(26, 31, 58, 0.5);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

## 🔌 API Integration

The dashboard connects to the FastAPI backend:

```typescript
// Configure API base URL in axios
const API_URL = 'http://localhost:8000/api/v1'

// Example API call
axios.get(`${API_URL}/files`, {
  headers: {
    Authorization: `Bearer ${token}`
  }
})
```

## 📦 Key Dependencies

- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Animations
- **Zustand**: State management
- **React Query**: Data fetching
- **Socket.io**: Real-time updates
- **Recharts**: Data visualization
- **Lucide React**: Icon library

## 🎭 Components

### Layout Components

- **MainLayout**: Sidebar + TopBar + content area
- **Sidebar**: Navigation with neon highlights
- **TopBar**: Search, notifications, user menu

### Page Components

- **Dashboard**: Overview with stats and quick actions
- **FilesView**: File grid with upload zone
- **OrganizeView**: Job configuration and progress
- **DuplicatesView**: Duplicate groups management
- **AnalyticsView**: Charts and insights
- **SettingsView**: User preferences

## 🚧 Roadmap

### Phase 1 (Current)
- [x] Basic layout and navigation
- [x] Dashboard with demo data
- [x] Login page
- [ ] File upload zone
- [ ] Real-time job progress

### Phase 2
- [ ] Complete FilesView with grid/list toggle
- [ ] OrganizeView with job configuration
- [ ] DuplicatesView with side-by-side comparison
- [ ] Analytics charts (storage, categories, activity)

### Phase 3
- [ ] Settings page (profile, subscription, security)
- [ ] Real API integration
- [ ] WebSocket for live updates
- [ ] Mobile responsiveness improvements

### Phase 4
- [ ] Advanced features (tagging, search, filters)
- [ ] Team collaboration UI
- [ ] Dark/Light theme toggle
- [ ] Keyboard shortcuts

## 🎨 Customization

### Change Theme Colors

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      'neon': {
        cyan: '#00f7ff',    // Change this
        magenta: '#ff00ff', // Change this
        green: '#00ff41',   // Change this
      }
    }
  }
}
```

### Add New Page

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add nav item in `src/components/layout/Sidebar.tsx`

## 📱 Responsive Design

The dashboard is optimized for:

- **Desktop**: 1920x1080 and above
- **Laptop**: 1366x768 and above
- **Tablet**: 768px and above
- **Mobile**: 375px and above

## 🔒 Security

- JWT token stored in Zustand with persistence
- HTTPS enforced in production
- CORS configured for API access
- XSS protection via React

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

Proprietary - JSMS Academy

---

**Built with ❤️ by David @ JSMS Academy**
