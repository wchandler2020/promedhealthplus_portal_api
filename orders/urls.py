from django.urls import path
import orders.views as api_views

urlpatterns = [
    path('provider/orders/', api_views.CreateOrderView.as_view(), name='create-order')
]
