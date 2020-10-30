# # encoding: utf-8
# """
# @author: lxc
# @file: periodic_task.py
# @time: 2019/6/11/011 15:50
# """
# import json
#
# from django_celery_beat.models import IntervalSchedule, PeriodicTask, CrontabSchedule
#
#
# def create_interval_schedule(every, period=IntervalSchedule.SECONDS):
#     schedule, _ = IntervalSchedule.objects.get_or_create(every=every,
#                                                          period=period)
#     return schedule
#
#
# def create_crontab_schedule(minute='*', hour='*', day_of_week='*', day_of_month='*', month_of_year='*', timezone='Asia/Shanghai'):
#     schedule, _ = CrontabSchedule.objects.get_or_create(minute=minute, hour=hour,
#                                                         day_of_week=day_of_week,
#                                                         day_of_month=day_of_month,
#                                                         month_of_year=month_of_year,
#                                                         timezone=timezone)
#     return schedule
#
#
# def delete_crontab_schedule(minute, hour, day_of_week, day_of_month, month_of_year):
#     if CrontabSchedule.objects.filter(minute=minute, hour=hour,
#                                       day_of_week=day_of_week,
#                                       day_of_month=day_of_month,
#                                       month_of_year=month_of_year).exists():
#         CrontabSchedule.objects.filter(minute=minute, hour=hour,
#                                        day_of_week=day_of_week,
#                                        day_of_month=day_of_month,
#                                        month_of_year=month_of_year).delete()