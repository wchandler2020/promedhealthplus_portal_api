from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from sales_rep.models import SalesRep
from .serializers import SalesRepDashboardSerializer  # <-- Import the correct serializer

class SalesRepDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            sales_rep = request.user.salesrep_profile  # ensure this is the SalesRep object
        except SalesRep.DoesNotExist:
            return Response(
                {"error": "You are not associated with a SalesRep profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SalesRepDashboardSerializer(sales_rep)
        return Response(serializer.data, status=status.HTTP_200_OK)
