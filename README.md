# Django WooCommerce Store

A full-featured Django ecommerce frontend powered by the WooCommerce REST API.

## Features
- 🛍️ Product listing with category filters, search, and sorting
- 📦 Product detail pages with image gallery and variation support
- 🛒 Session-based shopping cart (add, update, remove)
- 💳 Checkout → creates live orders via WooCommerce API
- 📋 Order confirmation and history
- 👤 User registration, login, and account dashboard

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure WooCommerce API

**Option A — Environment Variables (recommended)**
```bash
export WC_URL="https://your-store.com"
export WC_KEY="ck_your_consumer_key"
export WC_SECRET="cs_your_consumer_secret"
```

**Option B — Edit settings.py directly**
```python
# django_woo/settings.py
WOOCOMMERCE_URL = 'https://your-store.com'
WOOCOMMERCE_CONSUMER_KEY = 'ck_your_consumer_key'
WOOCOMMERCE_CONSUMER_SECRET = 'cs_your_consumer_secret'
```

**How to get API credentials:**
1. In your WordPress admin, go to **WooCommerce → Settings → Advanced → REST API**
2. Click **Add Key**
3. Set permissions to **Read/Write**
4. Copy the Consumer Key and Consumer Secret

### 3. Run Migrations & Start Server
```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for admin access
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Project Structure
```
django_woo/
├── django_woo/
│   ├── settings.py        # Configuration (WC API keys here)
│   ├── urls.py            # Root URL config
│   └── wsgi.py
├── store/
│   ├── woocommerce.py     # WooCommerce API client (all API calls)
│   ├── views.py           # All view logic
│   ├── models.py          # Local Order model
│   ├── urls.py            # Store URL patterns
│   └── context_processors.py
├── templates/
│   ├── base.html          # Main layout, navigation
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── store/
│       ├── product_list.html
│       ├── product_detail.html
│       ├── cart.html
│       ├── checkout.html
│       ├── order_confirmation.html
│       ├── account.html
│       └── order_detail.html
├── manage.py
└── requirements.txt
```

---

## Customization

### Change Store Name
Edit `templates/base.html`, find `Luxe Store` and replace with your brand name.

### Add More Countries to Checkout
Edit `templates/store/checkout.html` in the `<select name="country">` block.

### Enable Caching (Recommended for Production)
Add to `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
```

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Set a strong `SECRET_KEY` (use environment variable)
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure a real database (PostgreSQL recommended)
- [ ] Set up a payment gateway (Stripe, PayPal) instead of bank transfer
- [ ] Run `python manage.py collectstatic`
- [ ] Use gunicorn + nginx for serving

---

## API Endpoints Used
| Endpoint | Purpose |
|---|---|
| `GET /wc/v3/products` | Product listing |
| `GET /wc/v3/products/{id}` | Product detail |
| `GET /wc/v3/products/{id}/variations` | Product variations |
| `GET /wc/v3/products/categories` | Category list |
| `POST /wc/v3/orders` | Create order |
| `GET /wc/v3/orders/{id}` | Order detail |
