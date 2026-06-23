from ninja import NinjaAPI

from .api_accounts import router as accounts_router
from .api_auth import router as auth_router
from .api_categories import router as categories_router
from .api_transactions import router as transactions_router
from .ui_categories import router as categories_ui_router
from .ui_accounts import router as accounts_ui_router
from .ui_transactions import router as transactions_ui_router

api = NinjaAPI()
api.add_router("/auth", auth_router)
api.add_router("/categories", categories_router)
api.add_router("/accounts", accounts_router)
api.add_router("/transactions", transactions_router)
api.add_router("/ui/categories", categories_ui_router)
api.add_router("/ui/accounts", accounts_ui_router)
api.add_router("/ui/transactions", transactions_ui_router)
