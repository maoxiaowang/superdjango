from base.models import OperationLogEntry
from common.mixin import LoginRequiredMixin, PermissionRequiredMixin
from common.views import AdvancedListView


class OptLogList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    操作日志列表
    """
    model = OperationLogEntry
    permission_required = 'base.view_operation_log'
