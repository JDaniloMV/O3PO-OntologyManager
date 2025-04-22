from django.views.generic import TemplateView
from rest_framework import viewsets
from .models import *
from .serializers import *
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from core.serializers import ContactInfoSerializer, SocialLinkSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ContactInfo, SocialLink
from .serializers import ContactInfoSerializer, SocialLinkSerializer, PrivacyPolicySerializer

class HomePageView(TemplateView):
    template_name = 'index.html'

class ProductList(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAdminUser]  # Requer autenticação admin para modificações

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]  # Permite leitura pública
        return super().get_permissions()

class AboutPageView(TemplateView):
    template_name = 'index.html'

class ProductsPageView(TemplateView):
    template_name = 'index.html'

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        return self.queryset.order_by('-created_at')

class StorePageView(TemplateView):
    template_name = 'index.html'

class BlogPageView(TemplateView):
    template_name = 'index.html'

class ContactPageView(TemplateView):
    template_name = 'index.html'

class PolicyPageView(TemplateView):
    template_name = 'index.html'

class HomeBannerViewSet(viewsets.ModelViewSet):
    queryset = HomeBanner.objects.filter(is_active=True)
    serializer_class = HomeBannerSerializer

class FeaturedProductViewSet(viewsets.ModelViewSet):
    queryset = FeaturedProduct.objects.all()
    serializer_class = FeaturedProductSerializer

class AboutSectionViewSet(viewsets.ModelViewSet):
    queryset = AboutSection.objects.all()
    serializer_class = AboutSectionSerializer

class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer

class ProductCTAViewSet(viewsets.ModelViewSet):
    queryset = ProductCTA.objects.all()
    serializer_class = ProductCTASerializer

class TestimonialList(generics.ListAPIView):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer

class ProductInterestCreateView(generics.CreateAPIView):
    queryset = ProductInterest.objects.all()
    serializer_class = ProductInterestSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.order_by('-date')
    serializer_class = PostSerializer

class ContactInfoView(generics.ListAPIView):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer

class SocialLinksView(generics.ListAPIView):
    queryset = SocialLink.objects.all()
    serializer_class = SocialLinkSerializer

class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

class ContatoInfoAPIView(APIView):
    def get(self, request):
        contato = ContactInfo.objects.first()
        serializer = ContactInfoSerializer(contato)
        return Response(serializer.data)

class RedesSociaisListView(APIView):
    def get(self, request):
        redes = SocialLink.objects.all()
        serializer = SocialLinkSerializer(redes, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def get_privacy_policy(request):
    policy = PrivacyPolicy.objects.last()
    if policy:
        serializer = PrivacyPolicySerializer(policy)
        return Response(serializer.data)
    return Response({"detail": "Política não encontrada"}, status=404)

