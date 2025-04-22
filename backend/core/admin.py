from django.contrib import admin
from .models import *

@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ('headline', 'is_active')

@admin.register(ProductInterest)
class ProductInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'product', 'created_at')
    list_filter = ('product', 'created_at')
    search_fields = ('name', 'email', 'product__name')
    ordering = ('-created_at',)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'position')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'specialty')
        }),
        ('Midia e Links', {
            'fields': ('image', 'linkedin')
        }),
        ('Ordenação', {
            'fields': ('order',)
        })
    )

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('updated_at', 'short_mission')
    fieldsets = (
        ('Conteúdo Principal', {
            'fields': ('mission', 'vision', 'values')
        }),
        ('Seções Adicionais', {
            'fields': ('history', 'team', 'diferentials', 'partners')
        }),
    )

    def short_mission(self, obj):
        return obj.mission[:50] + "..." if len(obj.mission) > 50 else obj.mission
    short_mission.short_description = "Missão Resumida"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {"slug": ("title",)}
    ordering = ('date',)

admin.site.register(FeaturedProduct)
admin.site.register(Testimonial)
admin.site.register(ProductCTA)
admin.site.register(Product)
admin.site.register(ContactPageInfo)
admin.site.register(SocialLink)
admin.site.register(ContactMessage)
admin.site.register(PrivacyPolicy)