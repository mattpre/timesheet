# -*- coding: utf-8 -*-
from timesheet.commands import Command
from timesheet.models import DBSession, Task, Subject
from prettytable import PrettyTable
from datetime import timedelta, datetime
from sqlalchemy import func

__author__ = 'gmc'


class DailySummaryCommand(Command):
    name = 'daily-summary'
    description = 'Print detailed daily summary'

    @classmethod
    def add_arguments(cls):
        cls.parser.add_argument('days', nargs='?', default=30, type=int, help="Days, integer, default: 30")

    def do_job(self):
        """
        SELECT *, coalesce(end_time,now)-start_time
        FROM task t, subject s
        WHERE t.subject_id=s.id AND start_time > GetDate() - @days
        ORDER BY start_time
        :return:
        """
        session = DBSession()
        now = datetime.now()
        time_worked = (func.julianday(func.coalesce(Task.end_time,now)) - func.julianday(Task.start_time)) * 86400

        query = session.query(Task.start_time,
                              func.coalesce(Task.end_time, now),
                              time_worked,
                              Subject.title,
                              Task.title) \
            .filter(Subject.id == Task.subject_id) \
            .filter(func.date(Task.start_time) > func.date('now', '-%s day' % self.args.days)) \
            .order_by(Task.start_time)

        print()

        table = PrettyTable(['Subject', 'Duration'])
        table.align["Title"] = "l"

        total_time = 0
        day_total = 0
        last_date = None

        tasks = []
        time_per_task =[]
        for row in query:
            if row[3] in tasks:
                time_per_task[tasks.index(row[3])] += row[2]
            else:
                tasks.append(row[3])
                time_per_task.append(row[2])

        for k in range(len(tasks)):
            table.add_row([
                tasks[k],
                timedelta(seconds=round(time_per_task[k])),
            ])

        if day_total > 0:
            table.add_row([
                '', timedelta(seconds=round(sum(time_per_task)))
            ])

        print(table)
        print('Total Work time: %s\n' % timedelta(seconds=sum(time_per_task)))
