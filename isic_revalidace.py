#!/usr/bin/env python3
"""
vytvoří seznam (csv|xlsx) pro objednáná revalidace ISIC
"""
import argparse
import pyodbc as ms
import xlsxwriter

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich import print
from rich.align import Align
from rich.live import Live

isic_csv_line = {'Typ průkazu':'ISIC',
    'Typ požadavku':'EXTENSION',
    'Platnost od':'arg%rok',
    'Platnost do':None,
    'Osobní ID':None,
    'Titul před':None,
    'Titul za':None,
    'Jméno':'baka%JMENO',
    'Příjmení':'baka%PRIJMENI',
    'Kód země':None,
    'Adresa 1':None,
    'Adresa 2':None,
    'Obec':None,
    'Okres':None,
    'PSČ':None,
    'E-mail':'baka%E_MAIL',
    'Telefonní číslo':None,
    'Datum narození':'baka%DATUM_NAR',
    'Rodné číslo':None,
    'Třída':None,
    'Ročník':None,
    'Pojištění':None,
    'Název organizace':None,
    'Číslo průkazu':'baka%ISIC_KARTA',
    'Foto soubor':None
    }

def get_line(r, output='text'):
    """ CSV line """
    line = []
    for k,v in isic_csv_line.items():
        if v==None:
            line += ['']
        elif v.split('%')[0] == 'arg':
            line += ['01.09.'+eval('args.'+v.split('%')[1])]
        elif v.split('%')[0] == 'baka':
            line += [eval('r.'+v.split('%')[1]).strip()]
        else:
            if v == 'ISIC' and args.ucitel:
                v = 'ITIC'
            line += [v]
    if output == 'text':            
        return ",".join(line)            
    else:
        return line
    
def baka_search(trida=None):
    """ search in baka DB """
    fields = ",".join([v.split('%')[1] for k,v in isic_csv_line.items() if v!=None and v.split('%')[0]=='baka'])
    #print([k,v.split('%')[1] for k,v in isic_cvs_line.items() if v.split('%')[0]=='baka'])
    platnost = '09/'+args.rok
    #print(sql)
    if args.ucitel:
        sql = "SELECT {} FROM ucitele WHERE isic_plat<? AND isic_plat<>'' AND isic_karta != '' AND deleted_rc=0 ORDER BY prijmeni, jmeno".format(fields)
        cur.execute(sql,(platnost,))
    else:
        sql = "SELECT {} FROM zaci WHERE isic_plat<? AND deleted_rc=0 AND trida=? ORDER BY prijmeni, jmeno".format(fields) 
        cur.execute(sql,(platnost, trida,))
    return cur

def print_info(order_rows, baka_rows, trida):
    """ print info """
    sum = round(order_rows*int(args.value), 2)
    t.add_row(trida, "{}/{}".format(baka_rows, order_rows), "{} Kč".format(str(sum)))            
    return sum

def print_csv(f, trida=None):
    """ create csv file for import to NCDB """
    f = open(f,'w')
    print(','.join(isic_csv_line.keys()), file=f)
    baka_rows, order_rows  = 0, 0
    for row in baka_search(trida).fetchall():
        baka_rows += 1
        if check_order(row, trida):
            order_rows += 1
            print(get_line(row), file=f)
    return print_info(order_rows, baka_rows, trida)            

def print_xls(f, trida=None):
    """ create xlsx file for import to NCDB """
    workbook = xlsxwriter.Workbook(f) 
    worksheet = workbook.add_worksheet() 
    worksheet.write_row(0, 0, isic_csv_line.keys())
    baka_rows, order_rows  = 0, 0
    for row in baka_search(trida).fetchall():
        baka_rows += 1
        if check_order(row, trida):
            order_rows += 1
            worksheet.write_row(order_rows, 0, get_line(row, output='list'))
    workbook.close()            
    return print_info(order_rows, baka_rows, trida)            

def check_order(r, trida):
    """ check if record in order file """
    value_cz = lambda v: v+',00'
    if not args.objednavka:
        return True
    r_jm = " ".join((r[1].strip(), r[0].strip()))
    if len([True for jm, t, val in orders if jm == r_jm and val == value_cz(args.value) and trida == t]) > 0:
        return True
    else:
        return False

def get_orders(f_orders):
    """ read csv orders """
    orders = []
    f = open(f_orders, encoding='windows-1250')
    i = 0
    for line in f:
        i += 1
        if i<4:
            continue
        if line[0:6] == "Celkem" or line[0:6] == "Zpraco":
            continue
        jmpr, ev_cis, value, rest = line.strip().split(';',3)
        orders += [[jmpr[0:-4], jmpr[-3:], value]]
    return orders

tridy = lambda: cur.execute('select zkratka from tridy order by zkratka')

def write_file(trida):
    if args.type_output == 'csv':
        return print_csv("revalidace_"+trida+".csv", trida)
    elif args.type_output == 'xlsx':
        return print_xls("revalidace_"+trida+".xlsx", trida)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Vytvoří [CSV|XLSX] soubor pro objednání evalidace ISIC")
    parser.add_argument("-r","--rok", help="rok objednání revalidace", required=True )
    parser.add_argument("-t","--trida", help="třída")
    parser.add_argument("-a","--all", action='store_true', help="vytvořit soubory pro všechny třídy")
    parser.add_argument("-u","--ucitel", action='store_true', help="učitelé")
    parser.add_argument("-o","--objednavka", help="CSV soubor plateb z Bakalářů")
    parser.add_argument("-v","--value", help="částka hledaná v objednávce [250]", default='250')
    parser.add_argument("-f","--type_output", help="Formát výstupu [csv|xlsx]", default='csv')

    args = parser.parse_args()
    
    c = Console()
    t = Table(highlight=False, title="Výpis tříd v objednávce", title_justify="left")
    t.add_column("Třída", justify="center")
    t.add_column("Počet", justify="right" )
    t.add_column("Cena", justify="right")

    # --- connect -- SQL Bakalari ---
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
    
    if not args.trida and not args.all and not args.ucitel:
        parser.print_help()
        exit()

    cur = baka.cursor()
    if args.objednavka:
        orders = get_orders(args.objednavka)

    if args.ucitel:
        sum = write_file('učitel')
    
    elif args.trida:
        sum = write_file(args.trida)
    
    elif args.all:
        sum = sum([write_file(r.zkratka.strip()) for r in tridy().fetchall()])

    c.print(t)
    print("Celkem objednávka: {} Kč".format(sum))
            
