# Barakat Custom App — ERPNext Customizations

## What is This?

The `barakat` app is a **Frappe/ERPNext custom app** that extends ERPNext with Barakat-specific functionality. It's installed on every client site (not the master site) to provide:

- Custom fields on standard doctypes
- Custom doctypes for Barakat-specific features
- Fixtures (pre-configured data)
- Hooks and overrides

---

## Installation

### On a Frappe Bench

```bash
# Get the app
bench get-app barakat https://github.com/Iztech-team/barakat.git --branch main

# Install on a site
bench --site <site-name> install-app barakat

# Run migrations
bench --site <site-name> migrate
```

### Required Configuration

After installing, set the `front_door_domain` in the site config:

```bash
bench --site <site-name> set-config front_door_domain "master.yourdomain.com"
```

This tells the site where the SSO master is located.

---

## Development Setup

### Clone for Local Development

```bash
cd /path/to/frappe-bench/apps
git clone https://github.com/Iztech-team/barakat.git
cd barakat
```

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Make Changes

1. Edit files in `barakat/`
2. Run migrations: `bench --site <site> migrate`
3. Test your changes
4. Commit with pre-commit checks

---

## App Structure

```
barakat/
├── barakat/
│   ├── barakat/
│   │   ├── doctype/          # Custom doctypes
│   │   └── ...
│   ├── fixtures/             # Pre-configured data
│   ├── hooks.py              # Frappe hooks
│   ├── patches/              # Database patches
│   │   └── patches.txt       # Patch registry
│   └── ...
├── pyproject.toml            # Python project config
├── license.txt               # MIT License
└── README.md
```

---

## Key Files

| File | Purpose |
|------|---------|
| `hooks.py` | Defines app hooks (fixtures, doc_events, etc.) |
| `patches/patches.txt` | Lists database patches to run on migrate |
| `fixtures/` | JSON files with pre-configured data |

---

## Deploying Updates

### On Production/Development EC2

```bash
# SSH into the server
ssh -i <key.pem> ubuntu@<ip>
sudo su - frappe
cd /home/frappe/erp_project

# Pull latest changes
cd apps/barakat
git pull origin main
cd /home/frappe/erp_project

# Run migrations on all sites
bench --site all migrate

# Rebuild assets (if frontend changes)
bench build --app barakat

# Restart workers
bench restart
```

---

## Related Apps

| App | Purpose | Install On |
|-----|---------|------------|
| `barakat` | Client site customizations | Client sites |
| `iztechvalley_gateway` | SSO authentication | All sites |

---

## Repository Migration

The app was migrated from:
- **Old:** `https://github.com/Osama-Tbaileh/barakat`
- **New:** `https://github.com/Iztech-team/barakat`

Update your local clone:

```bash
cd apps/barakat
git remote set-url origin https://github.com/Iztech-team/barakat.git
git fetch origin
git pull origin main
```

---

## Support

For issues or questions, contact the development team.
