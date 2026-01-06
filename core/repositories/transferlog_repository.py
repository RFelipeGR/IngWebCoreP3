from core.models import TransferLog

class TransferLogRepository:
    def crear_log(self, **data):
        return TransferLog.objects.create(**data)
