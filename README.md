# 🛒 SEAPEDIA — Multi-Role E-Commerce Platform

> A full-stack e-commerce platform supporting **Buyer**, **Seller**, **Driver**, and **Admin** roles, built with Flask (Python) + Vanilla JS.

![GitHub Pages](https://img.shields.io/badge/Frontend-GitHub%20Pages-blue?logo=github)
![Backend](https://img.shields.io/badge/Backend-Flask%20Python-green?logo=python)
![Database](https://img.shields.io/badge/Database-SQLite-orange?logo=sqlite)
![License](https://img.shields.io/badge/Phase-6%20Complete-brightgreen)

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| **Frontend** | https://jellyfishcxdding.github.io/sea-compfest/ |
| **Backend API** | https://sea-compfest.onrender.com |
| **Health Check** | https://sea-compfest.onrender.com/health |

> ⚠️ **Note:** The backend runs on Render's free tier. The **first request after inactivity may take up to 60 seconds** to wake up. Subsequent requests are fast.

---

## 🎭 Demo Accounts

All accounts use the password: **`demo1234`**

| Role | Username | Capabilities |
|---|---|---|
| 🛍️ Buyer | `buyer_demo` | Browse, cart, checkout, wallet, vouchers, reviews |
| 🏪 Seller | `seller_demo` | Manage store, products, process orders |
| 🚗 Driver | `driver_demo` | Accept delivery jobs, complete deliveries |
| 👑 Admin | `admin_demo` | View stats, manage all orders, trigger overdue checks |

> Or register a new account at `/login.html` → click **Sign Up**

---

## ⚙️ Running Locally (Any Developer)

### Prerequisites
- **Python 3.8+** — https://python.org/downloads
- **pip** (comes with Python)
- **Git** — https://git-scm.com

### Step 1 — Clone the repository
```bash
git clone https://github.com/jellyfishcxdding/sea-compfest.git
cd sea-compfest
```

### Step 2 — Install Python dependencies
```bash
pip install flask flask-cors PyJWT bcrypt
```

### Step 3 — Seed demo data (first time only)
```bash
python seed_demo.py
```
This creates all 4 demo accounts and 3 voucher codes.

### Step 4 — Start the backend server
```bash
python backend/app.py
```
You should see:
```
SEAPEDIA Backend running on port 5000
* Running on http://127.0.0.1:5000/
```

### Step 5 — Open the frontend

**Option A — Direct file (simplest):**
Just double-click `index.html` in the project folder, OR open it in your browser:
```
file:///path/to/sea-compfest/index.html
```

**Option B — Live Server (recommended for VS Code users):**
1. Install the **Live Server** extension in VS Code
2. Right-click `index.html` → **Open with Live Server**
3. Browser opens at `http://127.0.0.1:5500`

> **Important:** Make sure `js/style.js` has `const API_URL = 'http://127.0.0.1:5000/api';` for local development.

---

## 🗂️ Project Structure

```
sea-compfest/
├── index.html              # Home page
├── login.html              # Login / Register
├── checkout.html           # Checkout flow
├── myOrder.html            # Buyer order history
├── sellerPage.html         # Seller dashboard
├── driverPage.html         # Driver job board
├── admin.html              # Admin dashboard
├── css/
│   ├── style.css           # Global design system
│   ├── motion.css          # Animations
│   └── ...                 # Page-specific styles
├── js/
│   ├── style.js            # API_URL, shared utilities (showToast, etc.)
│   ├── index.js            # Home page logic
│   ├── checkout.js         # Checkout + voucher logic
│   ├── sellerPage.js       # Seller dashboard logic
│   ├── driverPage.js       # Driver job logic
│   ├── admin.js            # Admin dashboard logic
│   └── ...
├── backend/
│   ├── app.py              # Flask API server (1300+ lines)
│   ├── requirements.txt    # Python dependencies
│   ├── init_db.py          # Database schema initializer
│   └── data/               # SQLite databases (auto-created)
│       ├── auth.db         # Users, roles, wallets
│       ├── seller.db       # Stores
│       ├── inventory.db    # Products, reviews, discounts
│       └── transactions.db # Orders, order items, wallet history
├── seed_demo.py            # Creates demo accounts + vouchers
└── render.yaml             # Render.com deployment config
```

---

## 🔌 API Endpoints Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/select-role` | Set active role |

### Products
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products` | List all products (search, filter, sort) |
| GET | `/api/products/<id>` | Product detail |
| POST | `/api/products/<id>/reviews` | Add review (Buyer, must have purchased) |

### Wallet
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/wallet` | Get balance |
| POST | `/api/wallet/topup` | Top up balance |
| GET | `/api/wallet/history` | Transaction history |

### Cart & Checkout
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/cart` | Get cart items |
| POST | `/api/cart` | Add/update item |
| DELETE | `/api/cart/<id>` | Remove item |
| POST | `/api/checkout` | Place order |
| POST | `/api/vouchers/validate` | Validate voucher code |

### Seller
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/stores` | Create store |
| PUT | `/api/stores/<id>` | Update store |
| POST | `/api/seller/products` | Create product |
| PUT/DELETE | `/api/seller/products/<id>` | Update/delete product |
| GET | `/api/seller/orders` | View store orders |
| POST | `/api/orders/<id>/process` | Process order → ship |

### Driver
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs/available` | View available delivery jobs |
| POST | `/api/jobs/<id>/take` | Accept a job |
| POST | `/api/jobs/<id>/complete` | Mark delivery complete |
| GET | `/api/jobs/mine` | My active delivery |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/stats` | System-wide statistics |
| GET | `/api/admin/orders` | All recent orders |
| POST | `/api/admin/trigger-overdue` | Auto-cancel overdue orders + refund |

---

## 🎟️ Voucher Codes (Demo)

| Code | Discount | Min. Purchase |
|---|---|---|
| `SEAPEDIA10` | 10% off | None |
| `HEMAT20` | 20% off | Rp 50,000 |
| `NEWUSER15` | 15% off | None |

---

## 🔐 Security Features (Phase 6)

- ✅ **JWT Authentication** — all protected routes require `Authorization: Bearer <token>`
- ✅ **RBAC** — each role can only access its own endpoints
- ✅ **XSS Protection** — all user inputs are escaped with `html.escape()` + length capped
- ✅ **Parameterized SQL** — zero raw string interpolation in any query
- ✅ **Input Validation** — username (3-50 chars), password (min 6), rating (1-5), price/stock (non-negative)
- ✅ **Tenant Isolation** — Buyer A cannot see Buyer B's orders; Seller can only modify own products
- ✅ **CORS** — configured to accept frontend origins only

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| Backend | Python 3, Flask, flask-cors |
| Auth | JWT (PyJWT), bcrypt password hashing |
| Database | SQLite (4 databases via ATTACH) |
| Hosting (Frontend) | GitHub Pages |
| Hosting (Backend) | Render.com (free tier) |

---

## 💡 Troubleshooting

### "Could not load products" on the live site
The Render backend may be sleeping. Open https://sea-compfest.onrender.com/health in your browser and wait ~60 seconds for it to wake up, then refresh the main site.

### Local backend won't start
Make sure all dependencies are installed:
```bash
pip install flask flask-cors PyJWT bcrypt
```

### "Username already exists" on register
The database already has that username. Try a different one or log in instead.

### Products are empty after cloning
Run the seed script to populate demo data:
```bash
python seed_demo.py
```

---

## 👨‍💻 Authors

Built for **COMPFEST SEA** — Sea-Compfest E-Commerce Challenge
