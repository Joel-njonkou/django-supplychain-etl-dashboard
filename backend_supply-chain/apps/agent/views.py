from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework import serializers
from .loop import run_agent
from .services import explain_bottlenecks
  
class ChatInput(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    history = serializers.ListField(child=serializers.DictField(), required=False, max_length=20)

class BottleneckExplainView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "agent"
    def post(self, request):
        filters = {k: request.data.get(k) for k in ("date_min", "date_max", "region",
            "transporteur")
                    if request.data.get(k)}
        return Response(explain_bottlenecks(filters, force=request.query_params.get("refresh") ==
            "true"))
        
class ChatView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "agent"
    def post(self, request):
        s = ChatInput(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(run_agent(s.validated_data.get("history", []),
            s.validated_data["question"]))
