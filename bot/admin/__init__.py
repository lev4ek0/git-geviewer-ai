from typing import Type, Union

from sqladmin import Admin, BaseView, ModelView


class AdminRouter:
    views: list[Union[Type[ModelView], Type[BaseView]]]

    def __init__(self) -> None:
        self.views = []

    def view(self, view_class: Union[Type[ModelView], Type[BaseView]]):
        self.views.append(view_class)

    def include_routers(self, routers: list["AdminRouter"]):
        for router in routers:
            self.views.extend(router.views)


class MyAdmin(Admin):
    def include_router(self, router: AdminRouter) -> None:
        for view in router.views:
            self.add_view(view)
