# """
# Inherit this Task if you define a new Task class
# """
# import traceback
#
# from billiard.exceptions import SoftTimeLimitExceeded
# from celery.task import Task
# from celery_once import QueueOnce
#
# from common.log import default_logger as logger
#
# __all__ = [
#     'CommonTask',
#     'CommonTaskOnce'
# ]
#
# from celery import shared_task
# from django.shortcuts import render
# from django.utils.safestring import mark_safe
#
# from common.utils.mail import send_mail_by_default
#
#
# @shared_task
# def send_task_warning(task_id, trace):
#     # recipient_list = ['1225191678@qq.com', '631722174@qq.com', '1322857202@qq.com', '3091633103@qq.com',
#     #                   '670107317@qq.com', '948114722@qq.com', '1224067934@qq.com', 'easted_bm@163.com',
#     #                   '409092507@qq.com']
#     recipient_list = ['409092507@qq.com']
#     trace = '<div style="width: 100%%; overflow-x: scroll;">%s</div>' % trace
#     message = render(
#         None, 'mail/general_mail.html',
#         {'subject': 'Celery Task',
#          'content': mark_safe(
#              '<h2>%(title)s</h2><pstyle="color:blue">(task_id)</p><p style="color:red">%(content)s</p>' %
#              {'title': '异常任务告警', 'task_id': task_id, 'content': trace}
#          )}
#     ).content.decode('utf-8')
#     send_mail_by_default('新军工版：异常任务告警', message, content_type='html', recipient_list=recipient_list)
#
#
# class CommonTask(Task):
#     silent_exceptions = (SoftTimeLimitExceeded,)
#
#     def run(self, *args, **kwargs):
#         # do something when task runs
#         pass
#
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         # do something when task raise any exception
#         # catch billiard.exceptions.SoftTimeLimitExceeded here
#         if exc.__class__ in self.silent_exceptions:
#             print('{0!r} aborted: {1!r}'.format(task_id, exc))
#         else:
#             print('{0!r} failed: {1!r}'.format(task_id, exc))
#             logger.error('{0!r} failed: {1!r}'.format(task_id, exc))
#             logger.error(traceback.format_exc())
#             # send_task_warning.delay(task_id, traceback.format_exc())
#
#     def on_success(self, retval, task_id, args, kwargs):
#         # do something when task finished successfully
#         # LayerResource.objects.create()
#         print('{0!r} success: {1!r}'.format(task_id, retval))
#         logger.info('{0!r} success: {1!r}'.format(task_id, retval))
#
#
# class CommonTaskOnce(QueueOnce):
#     silent_exceptions = (SoftTimeLimitExceeded,)
#
#     def run(self, *args, **kwargs):
#         # do something when task runs
#         pass
#
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         # do something when task raise any exception
#         # catch billiard.exceptions.SoftTimeLimitExceeded here
#         if exc.__class__ in self.silent_exceptions:
#             print('{0!r} aborted: {1!r}'.format(task_id, exc))
#         else:
#             print('{0!r} failed: {1!r}'.format(task_id, exc))
#             logger.error('{0!r} failed: {1!r}'.format(task_id, exc))
#             logger.error(traceback.format_exc())
#             # send_task_warning.delay(task_id, traceback.format_exc())
#
#     def on_success(self, retval, task_id, args, kwargs):
#         # do something when task finished successfully
#         # LayerResource.objects.create()
#         print('{0!r} success: {1!r}'.format(task_id, retval))
#         logger.info('{0!r} success: {1!r}'.format(task_id, retval))
