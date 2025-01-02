from .router_chats import router as chats_router
from .router_users import router as users_router
from .router_webhooks import router as webhooks_router
from .router_strategies import router as strategies_router

all_routers = [chats_router, users_router, webhooks_router, strategies_router]
