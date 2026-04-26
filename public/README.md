# Dork Loker - Frontend

Web dashboard untuk manage job search subscriptions.

## Files

- **index.html** - User dashboard (create custom searches)
- **dashboard.html** - Admin dashboard (manage users & global searches)
- **config.js** - Supabase configuration (credentials)

## Setup

1. Copy `config.js` and update with your Supabase credentials:

```javascript
window.SUPABASE_CONFIG = {
  url: 'https://YOUR_PROJECT.supabase.co',
  anonKey: 'YOUR_ANON_KEY_HERE'
};
```

2. Deploy via GitHub Pages or any static hosting

## Usage

### For Users (index.html)

1. Login with your registered email
2. Create custom searches:
   - Set keyword (e.g., "frontend developer")
   - Choose location type (remote/hybrid/on-site)
   - Choose employment type (full-time/part-time/etc.)
   - Set city (optional)
   - Add exclude keywords (optional)
3. Subscribe to global searches created by admin
4. Receive daily email notifications

### For Admins (dashboard.html)

1. Login with admin email
2. Manage users (add/remove)
3. Create global searches for all users
4. View statistics

## Security

- **Anon Key**: Safe to expose in frontend (read-only with RLS)
- **Service Role Key**: NEVER expose in frontend (use in backend only)
- **Row Level Security**: Enabled on all Supabase tables

## Development

No build step required. Just open HTML files in browser.

For local testing with Supabase:
1. Update `config.js` with your credentials
2. Open `index.html` or `dashboard.html` in browser
3. Login and test features
