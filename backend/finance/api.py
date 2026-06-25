from ninja import NinjaAPI

from .api_accounts import router as accounts_router
from .api_auth import router as auth_router
from .api_categories import router as categories_router
from .api_transactions import router as transactions_router
from .ui_home import router as home_ui_router
from .ui_categories import router as categories_ui_router
from .ui_profile import router as profile_ui_router
from .ui_stats import router as stats_ui_router

api = NinjaAPI()
api.add_router("/auth", auth_router)
api.add_router("/categories", categories_router)
api.add_router("/accounts", accounts_router)
api.add_router("/transactions", transactions_router)
api.add_router("/ui/home", home_ui_router)
api.add_router("/ui/categories", categories_ui_router)
api.add_router("/ui/profile", profile_ui_router)
api.add_router("/ui/stats", stats_ui_router)
