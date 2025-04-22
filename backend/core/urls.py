from django.urls import path, include
from core import views
from rest_framework import routers
from .views import (
    HomePageView,
    TeamMemberViewSet,
    AboutPageView,
    ProductsPageView,
    StorePageView,
    BlogPageView,
    ContactPageView,
    PolicyPageView,
    HomeBannerViewSet,
    FeaturedProductViewSet,
    AboutSectionViewSet,
    TestimonialViewSet,
    ProductCTAViewSet,
    ProductViewSet,
    ProductInterestCreateView,
    PostViewSet, 
    ContactInfoView, 
    SocialLinksView, 
    ContactMessageCreateView,
    ContatoInfoAPIView, 
    RedesSociaisListView
)

# Configuração única do Router para todas as APIs
router = routers.DefaultRouter()
router.register('home-banner', HomeBannerViewSet, basename='homebanner')
router.register('featured-product', FeaturedProductViewSet, basename='featuredproduct')
router.register('about-section', AboutSectionViewSet, basename='aboutsection')
router.register('testimonials', TestimonialViewSet, basename='testimonial')
router.register('product-ctas', ProductCTAViewSet, basename='productcta')
router.register('products', ProductViewSet, basename='product') 
router.register(r'team-members', TeamMemberViewSet, basename='teammember')
router.register(r'blog', PostViewSet)

urlpatterns = [
    # Rotas das páginas HTML
    path('', HomePageView.as_view(), name='home'),
    path('sobre/', AboutPageView.as_view(), name='about'),
    path('produtos/', ProductsPageView.as_view(), name='products'),
    path('loja/', StorePageView.as_view(), name='store'),
    path('blog/', BlogPageView.as_view(), name='blog'),
    path('contato/', ContactPageView.as_view(), name='contact'),
    path('politica/', PolicyPageView.as_view(), name='policy'),
    path('api/interesse/', ProductInterestCreateView.as_view(), name='product-interest-create'),
    path('contato/info/', ContactInfoView.as_view(), name='contact-info'),
    path('contato/redes/', SocialLinksView.as_view(), name='social-links'),
    path('contato/mensagem/', ContactMessageCreateView.as_view(), name='contact-message'),
    path('api/contato/info/', ContatoInfoAPIView.as_view(), name='contato-info'),
    path('api/contato/redes/', RedesSociaisListView.as_view(), name='contato-redes'),
    path('contato/formulario/', views.ContactMessageCreateView.as_view(), name='contato-formulario'),
    path('api/politica/', views.get_privacy_policy),
    
    # Rotas da API
    path('api/', include(router.urls)),
]
