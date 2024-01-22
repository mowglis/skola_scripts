#!/usr/bin/env python3

from gybon import Bakalari, Mail, Student, Ucitel, from_cz_date, to_cz_date, today, rc, before_today
import argparse
import sys
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.pretty import pprint
from rich.pretty import Pretty
from rich.panel import Panel
from rich import box
from rich import print
import datetime

days = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
week_day = lambda d: days[datetime.date(*list(reversed([int(dd) for dd in d.split('.')]))).weekday()]

def abs_row(hodiny):
    point = lambda x: '/' if x in hodiny else '-'
    max_cols = 10
    t = Table(box=box.ROUNDED)
    for i in range(1, max_cols):
        color = "on green" if i in hodiny else "on white" 
        t.add_column(str(i), style=color, justify="center")
    a = [' ' for i in range(1, max_cols)]   
    t.add_row(*a)
    return t

def abs_table(student, f_date, t_date):
    f_date = f_date if f_date else to_cz_date(before_today(7))
    t_date = t_date if t_date else to_cz_date(today())
    absence = student.absence(from_date=f_date, to_date=t_date, dic=True)
    trida = student.trida if isinstance(student, Student) else 'učitel'
    dny = " -- ".join([f_date, t_date])
    title = "{} {} ({}) - {}".format(student.prijmeni, student.jmeno, rc(student.rc), trida) 
    t = Table(highlight=False, title=title, title_justify="left", box=box.ROUNDED)
    t.add_column("Datum", justify="center", vertical="middle")
    col_tit = "Absence ve dnech: {}".format(dny)
    t.add_column(col_tit, justify="center", vertical="middle")
    for datum, hodiny in absence.items():
        h = t.add_row(week_day(datum)+'\n'+datum, abs_row(hodiny))
    return t

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docházka studenta")
    parser.add_argument("-f", "--from_date", help="Docházka od data")
    parser.add_argument("-t", "--to_date",  help="Docházka do data")
    parser.add_argument("-n", "--name", help="Příjmení studenta", required=True)
    args = parser.parse_args()
    
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(1)
       
    b = Bakalari()
    c = Console()

    c.print(abs_table(b.student_name(args.name), args.from_date, args.to_date))
    del b    
