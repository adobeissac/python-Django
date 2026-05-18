"""
WooCommerce REST API client with caching and error handling.
"""
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class WooCommerceAPI:
    def __init__(self):
        self.base_url = settings.WOOCOMMERCE_URL.rstrip('/')
        self.auth = HTTPBasicAuth(
            settings.WOOCOMMERCE_CONSUMER_KEY,
            settings.WOOCOMMERCE_CONSUMER_SECRET
        )
        self.api_base = f"{self.base_url}/wp-json/wc/v3"

    def _get(self, endpoint, params=None, cache_key=None, timeout=None):
        if cache_key:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, params=params or {}, timeout=15)
            response.raise_for_status()
            data = response.json()
            if cache_key:
                cache.set(cache_key, data, timeout or settings.WC_CACHE_TIMEOUT)
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"WooCommerce API error [{endpoint}]: {e}")
            return None

    def _post(self, endpoint, data):
        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.post(url, auth=self.auth, json=data, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WooCommerce API POST error [{endpoint}]: {e}")
            return None

    # ── Products ──────────────────────────────────────────────
    def get_products(self, page=1, per_page=12, category=None, search=None, order_by='date'):
        params = {'page': page, 'per_page': per_page, 'orderby': order_by, 'status': 'publish'}
        if category:
            params['category'] = category
        if search:
            params['search'] = search
        cache_key = f"wc_products_{page}_{per_page}_{category}_{search}_{order_by}"
        return self._get('products', params=params, cache_key=cache_key) or []

    def get_product(self, product_id):
        return self._get(f'products/{product_id}', cache_key=f"wc_product_{product_id}")

    def get_product_variations(self, product_id):
        return self._get(f'products/{product_id}/variations',
                         cache_key=f"wc_variations_{product_id}") or []

    # ── Categories ────────────────────────────────────────────
    def get_categories(self, per_page=50):
        params = {'per_page': per_page, 'hide_empty': True, 'orderby': 'name'}
        return self._get('products/categories', params=params,
                         cache_key='wc_categories', timeout=600) or []

    # ── Orders ────────────────────────────────────────────────
    def create_order(self, order_data):
        return self._post('orders', order_data)

    def get_order(self, order_id):
        return self._get(f'orders/{order_id}')

    def get_orders_by_email(self, email, page=1, per_page=10):
        params = {'billing_email': email, 'page': page, 'per_page': per_page}
        return self._get('orders', params=params) or []

    # ── Products count for pagination ─────────────────────────
    def get_products_count(self, category=None, search=None):
        params = {'status': 'publish'}
        if category:
            params['category'] = category
        if search:
            params['search'] = search
        url = f"{self.api_base}/products"
        try:
            response = requests.get(url, auth=self.auth, params={**params, 'per_page': 1}, timeout=15)
            return int(response.headers.get('X-WP-Total', 0))
        except Exception:
            return 0


wc_api = WooCommerceAPI()
