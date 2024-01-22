#!/usr/bin/env python3
"""
eprihlasky.gybon.cz
"""
import sys
sys.path.insert(1, '/home/rusek/skola/lib')
from gybon import Bakalari, Platby, Platba_akce, Eprihlasky_DB
import os
import argparse
from rich.console import Console
from rich.table import Table
from rich import print
from rich.live import Live
from gybon import Eprihlasky_DB
from payment import vypis_akce, get_eprihlaska

def get_ikod_platby(akce):
    return [s.i_kod  for s in pay.student(akce)]        

def update_db(eprihlaska, l_ikod, action):
    """ update db """
    actions = ['add', 'delete']
    if action not in actions:
        return
   
    if action == 'delete':
            db_eprihlasky.delete_ikod(eprihlaska, l_ikod)  
    elif action == 'add':
            students = [baka.student(ikod=ikod) for ikod in l_ikod]
            db_eprihlasky.add_students(eprihlaska, students)

def missing_in_eprihlaska(s_payment, s_eprihlaska):
    """ studenti chybějící v e-přihlášce """
    return [ikod for ikod in s_payment if ikod not in s_eprihlaska]

def extra_in_eprihlaska(s_payment, s_eprihlaska):
    """" studenti navíc v e-přihláškách """ 
    return [ikod for ikod in s_eprihlaska if ikod not in s_payment]

def print_table(list_ikod, title=''):
    """ tabulky studentů """
    if len(list_ikod) == 0:
        c.print(title,"- seznam je prázdný", style="red")
        return
    t = Table(highlight=False, title=title, title_justify="left")
    t.add_column("Student")
    for ik in list_ikod:
        try:
            t.add_row(baka.student(ikod=ik).fullname)
        except:
            t.add_row("{} - interní kód nenalezen v DB Bakaláři".format(ik))            
    c.print(t)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="E-přihlášky - kontrola studentů podle platební akce Bakalářů")
    parser.add_argument("-a", "--akce", help="Vypiš info o konkrétní akci ID")
    parser.add_argument("-u", "--update", help="Update záznamů v db E-přihlášek", action='store_true')
 
    args = parser.parse_args()

    db_eprihlasky = Eprihlasky_DB()
    baka = Bakalari()
    pay = Platby()
    c = Console()

    if args.akce:
        vypis_akce(pay.akce(id_akce=args.akce), id_akce=args.akce)
        eprihlaska = get_eprihlaska(args.akce)
        if eprihlaska == None:
            c.print("Akce nemá založené e-přihlášky", style='red')
            exit()
        akce = list(pay.akce(id_akce=args.akce))[0]
        s_payment = get_ikod_platby(akce)
        s_eprihlaska = db_eprihlasky.get_ikod(eprihlaska)
        
        # chybějící studneti v E-P 
        missing = missing_in_eprihlaska(s_payment, s_eprihlaska)
        if args.update and len(missing) > 0:
            update_db(eprihlaska, missing, action='add')
        print_table(missing_in_eprihlaska(s_payment, s_eprihlaska), title="Studenti chybějící v e-přihláškách")
        
        # nadbyteční studenti v E-P
        extra = extra_in_eprihlaska(s_payment, s_eprihlaska)
        if args.update and len(extra) > 0:
            update_db(eprihlaska, extra, action='delete')
        print_table(extra_in_eprihlaska(s_payment, s_eprihlaska), title="Studenti v e-přihlášekách nadbytečně")

    else:
        vypis_akce(pay.akce(), title="Výpis všech platebních akcí")

