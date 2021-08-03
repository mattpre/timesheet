# -*- coding: utf-8 -*-
from timesheet.commands import Command
from timesheet.models import DBSession, Task, Subject
from prettytable import PrettyTable
from datetime import timedelta, datetime
from sqlalchemy import func

__author__ = 'gmc'


class DailySummaryCommand(Command):
    name = 'daily-summary'
    description = 'Print daily summary'

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

        table = PrettyTable(['Date','Time', 'Subject', 'Title'])
        table.align["Title"] = "l"

        total_time = 0
        day_total = 0
        last_date = None
        task_time = []
        tasks = []
        tasks2 = []

        for row in query:
            if last_date == None:
                last_date = row[0].date()

            if row[0].date() != last_date:
                for kt in range(len(tasks)):
                    table.add_row([
                        tasks2[kt][2].strftime('%Y-%m-%d'),
                        timedelta(seconds=round(task_time[kt])),
                        tasks2[kt][0],
                        tasks2[kt][1],
                    ])
                table.add_row([
                    '',timedelta(seconds=round(day_total)), '', ''
                ])
                last_date = row[0].date()
                day_total = 0
                task_time = []
                tasks = []
                tasks2 = []

            day_total += row[2]
            total_time += row[2]
            
            if row[3]+row[4] in tasks:
                ind = tasks.index(row[3]+row[4])
            else:
                tasks.append(row[3]+row[4])
                tasks2.append((row[3],row[4],row[0]))
                task_time.append(0)
                ind = len(tasks)-1

            task_time[ind] += row[2]

        if day_total > 0:
            for kt in range(len(tasks)):
                table.add_row([
                    tasks2[kt][2].strftime('%Y-%m-%d'),
                    timedelta(seconds=round(task_time[kt])),
                    tasks2[kt][0],
                    tasks2[kt][1],
                ])
            table.add_row([
                '',timedelta(seconds=round(day_total)), '', ''
            ])

        print(table)
        print('Total Work time: %s\n' % timedelta(seconds=round(total_time)))
