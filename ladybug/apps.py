from django.apps import AppConfig


class LadybugConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ladybug'

    def ready(self):
        import ladybug.signals  # 👈 This ensures signals get registered