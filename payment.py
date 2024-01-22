#!/usr/bin/env python3
"""
Baka payment
"""
import sys
sys.path.insert(1, '/home/rusek/skola/lib')
from gybon import Bakalari, Platby, Platba_akce, Eprihlasky_DB
import os
import argparse
from rich import box
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich import print
from rich.align import Align
from rich.live import Live
import datetime

YES_NO = {False:"▪", True:"✔"} 

baka = Bakalari()
pay  = Platby()
c = Console()
db_eprihlasky = Eprihlasky_DB()

MSG_REMINDER = """Dobrý den,

na našem účtu evidujeme dlužnou částku ve výši {} Kč. na školní akci '{}'. Prosíme, uhraďte částku co nejdříve. Informace o platbě (platební symboly) včetně QR kódu jsou přiravené v IS Bakaláři na adrese https://bakalari.gybon.cz/bakaweb

Návod, kde nalézt platební modul v Bakalářích:
https://moodle.gybon.cz/mod/page/view.php?id=31995
https://www.gybon.cz/download/ruzne/ruzne/baka_platba.pdf

Poznámka: platební modul je dostupný pouze ve webové aplikaci, v mobilní aplikaci obsažen není
--
Tento mail byl automaticky vygenerován. Neodpovídejte na něj.
Gymnázium Boženy Němcové
"""
MSG_INFO = """Dobrý den,

v IS Bakaláři na webové adrese https://bakalari.gybon.cz/bakaweb je připravená platba ve výši {} Kč na školní akci '{}'.
Informace o platbě (platební symboly) včetně QR kódu  naleznete v platebním modulu v IS Bakaláři.

Návod, kde nalézt platební modul v Bakalářích:
https://moodle.gybon.cz/mod/page/view.php?id=31995
https://www.gybon.cz/download/ruzne/ruzne/baka_platba.pdf

Poznámka: platební modul je dostupný pouze ve webové aplikaci, v mobilní aplikaci obsažen není
--
Tento mail byl automaticky vygenerován. Neodpovídejte na něj.
Gymnázium Boženy Němcové
"""
MSG_INFO_SUBSCRIBE = """Dobrý den,

v systému elektronických přihlášek studentů na webové adrese https://eprihlasky.gybon.cz je připravena k podpisu přihláška na školní akci:

'{}'

Přihlášku podepisuje zákonný zástupce nezletilého studenta nebo zletilý student. Přihlášení do systému e-přihlášek je shodné s přihlášením do IS Bakaláři.

Přihlášku podepište co nejdříve. Děkujeme.
--
Tento mail byl automaticky vygenerován. Neodpovídejte na něj.
Gymnázium Boženy Němcové
"""
MSG = {'reminder':MSG_REMINDER, 'info':MSG_INFO, 'info_subscribe':MSG_INFO_SUBSCRIBE}

def send_mail(student, akce, typ=''):
    """ send mail """
    subj = {'platba':"Upozornění na platbu v IS Bakaláři",
            'podpis':"Upozornění na podpis e-přihlášky studenta"} 
    if typ == 'platba':
        amount = sum(a.amount for a in  akce)
        msg_type = args.typ if args.typ else 'info'
        msg = MSG[msg_type].format(amount, akce[0].description) 
    if typ == 'podpis':
        baka_id = akce[0].id
        msg = MSG['info_subscribe'].format(db_eprihlasky.get_application(baka_id).name)
    for mail in ['private', 'zz']:
    #for mail in ['test']:
        student.mail(msg, mail_to=mail, mail_subj=subj[typ], send=True)

def mail_reminder(akce, eprihlaska=None, typ='', student=None):
    """ pošli upomínku """
    t = {'platba':' o platbě akce', 'podpis':' o podpisu přihlášky'}
    t = Table(highlight=False, title="Poslat upomínku"+t[typ], title_justify="left")
    t.add_column("Count")
    t.add_column("Student")
    t.add_column("Mail -- student, ZZ")
    if student is not None:
        studenti=[student]
    elif typ == 'platba':
        studenti = list(pay.student(akce[0], scope='dluh'))
    elif typ == 'podpis':
        if eprihlaska == None:
            return
        studenti = student_bez_podpisu(eprihlaska)

    total = len(studenti)
    with Live(t, auto_refresh=False) as live:
        i = 0
        for s in studenti:
            i += 1
            try:
                l_mail = [ email for email in [s.email]+s.zz_email if email != '']
                mail = ", ".join(l_mail)
            except:
                mail = ""
            t.add_row("{}/{}".format(i, total), " ".join([s.prijmeni, s.jmeno]), mail)
            if args.yes:
                send_mail(s, akce, typ=typ)
                live.update(t, refresh=True)

def student_bez_podpisu(eprihlaska):
    """ vybere studenty bez podpisu e-prihlášky """
    
    def clean_list(item):
        if item == None:
            return False
        return True

    if eprihlaska == None:
        return None
    try:
        result = db_eprihlasky.students(eprihlaska)
        return list(filter(clean_list, [baka.student(ikod=row['studentINTERN_KOD']) for row in result]))
    except:
        return None        

def color_alert(line):
    if  YES_NO[False] in line:
        return "[red bold]"+line+"[red bold\]"
    else:
        return line

def count(akce):
    n_all = len(list(pay.student(akce)))
    n_nopay = len(list(pay.student(akce, scope='zaplaceno')))
    icon = YES_NO[n_all == n_nopay]
    return color_alert("{}/{} {}".format(str(n_all), str(n_nopay), icon)) 

def vypis_student(akce, title='', scope='all', eprihlaska=None):
    """ Vypíše studenty platební akce """
    if scope == 'podpis' and eprihlaska is not None:
        studenti = student_bez_podpisu(eprihlaska)
    elif scope == 'podpis' and eprihlaska is None:
        return        
    else:        
        studenti = list(pay.student(akce, scope))
    
    ncol = 4
    t = Table(highlight=False, title=title, title_justify="left")
    for i in range(ncol):
        t.add_column(8*' '+"Student")
    cols = [studenti[i:i+ncol] for i in range(0, len(studenti), ncol)]
    for col in cols:
        line = [color_alert(" ".join([check_platba(akce, student), check_podpis(eprihlaska, student), student.prijmeni, student.jmeno, student.trida])) for student in col]
        
        try:
            t.add_row(*line)
        except:
            continue
    c.print(t)
    celkem = len(list(pay.student(akce)))
    zaplaceno = len(list(pay.student(akce, scope='zaplaceno')))
    dluh = len(list(pay.student(akce, scope='dluh')))
    if eprihlaska:
        nepodepsano = len(student_bez_podpisu(eprihlaska))
        c.print("Celkem studentů: {} -- zaplaceno: {} -- dlužníci: {} -- nepodepsáno: {}".format(celkem, zaplaceno, dluh, nepodepsano))
    else:        
        c.print("Celkem studentů: {} -- zaplaceno: {} -- dlužníci: {}".format(celkem, zaplaceno, dluh))

def check_podpis(eprihlaska, student):
    """ Kontrola podepsání e-přihlášky """
    if eprihlaska == None:
        return ''
    return YES_NO[db_eprihlasky.check_signature(student.i_kod, eprihlaska)]

def check_platba(akce, student):
    """ Kontrola platby akce studentem """
    try:
        return YES_NO[len(list(pay.platby(student=student, akce=akce))) > 0]
    except:
        return YES_NO[False]

def vypis_akce(akce, student=None, title='', id_akce=None):
    """ Vypíše platební akce """
    if id_akce != None:
        # výpis jednotlivé akce
        try:
            _akce = list(akce)[0]
        except IndexError:
            print("*** ERROR-ID akce mimo rozsah")
            exit()
        t = Table.grid()
        t.add_row("Popis platby: ", _akce.title)
        t.add_row("ID: ", str(_akce.id))
        t.add_row("SS: ", str(_akce.ss))
        t.add_row("Částka: ", str(_akce.amount)+' Kč')
        t.add_row("Počet: ", count(_akce))

        panel = Panel(
            Align.left(t),
            box=box.ROUNDED,
            #padding=(1, 1),
            title="[b blue]"+_akce.title,
            border_style="blue",
            width = 50
        )
        print(panel)

    else:
        # tabulka všech akcí
        t= Table(highlight=False, title=title)
        t.add_column("ID", justify='right')
        t.add_column("SS", justify='left')
        t.add_column("Popis platby")
        t.add_column("Předepsaná částka", justify='right')
        t.add_column("Počet", justify='right')
   
        with Live(t, auto_refresh=False) as live:
            for _akce in akce:
                try:
                    if not _akce.active and not args.full:
                        continue
                except:
                        pass
                n = count(_akce) 
                is_platba = check_platba(_akce, student) if student else ''
                t.add_row(str(_akce.id), str(_akce.ss), _akce.title, str(_akce.amount)+' Kč '+is_platba, n)
                live.update(t, refresh=True)

def vypis_platby(pay_lines, title=''):
    """ Vypíše platby """
    title = title if title else "Výpis plateb"
    t = Table(highlight=False, title=title, title_justify="left")
    t.add_column("Datum platby", justify='right')
    t.add_column("VS", justify='center')
    t.add_column("SS", justify='center')
    t.add_column("Student")
    t.add_column("Popis platby")
    t.add_column("Zpráva pro příjemce")
    t.add_column("Částka", justify='right')
    
    for line in  pay_lines:  
        student = baka.student(ikod=line.ikod)
        t.add_row(line.modified.strftime("%d.%m.%Y"), str(line.vs), str(line.ss), "{} {}".format(student.prijmeni, student.jmeno), "({:2}) ".format(line.payment_regulation_id)+line.title, line.bank_title, str(line.amount))
        #print(line.get_items())
    c.print(t)        

def get_eprihlaska(id_baka_akce):
    """ e-prihláška na akci """
    try:
        eprihlaska = db_eprihlasky.get_application(id_baka_akce)
        t = Table.grid()
        t.add_row("Název přihlášky: ", eprihlaska.name)
        t.add_row("Vytvořeno: ", eprihlaska.date_as_str('createdOn'))
        t.add_row("Termín podpisu: ", "{} - {}".format(eprihlaska.date_as_str('openFrom'), eprihlaska.date_as_str('openTo')))     

        message_panel = Panel(
            Align.left(t),
            box=box.ROUNDED,
            title="[b red]E-přihláška",
            border_style="red",
            )
        print(message_panel)
        return eprihlaska
    except:
        return None

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Platby přes Bakaláře")
    parser.add_argument("-n", "--name", help="Příjmení studenta - vypíše akce studenta")
    parser.add_argument("-a", "--akce", help="Vypiš studenty akce - akce zadat pomocí id")
    parser.add_argument("-p", "--pay", help="Vypiš platby", action="store_true")
    parser.add_argument("-s", "--scope", help="Jaký seznam vypsat [dluh | zaplaceno | podpis]  ")
    parser.add_argument("-m", "--mail", help="Poslat upomínku mailem [ platba | podpis | all ]")
    parser.add_argument("-t", "--typ", help="Typ zprávy [ info | reminder ]")
    parser.add_argument("-y", "--yes", help="Skutečně odeslat!", action='store_true')
    parser.add_argument("-f", "--full", help="Všechny akce - včetně neaktivních", action='store_true')
 
    args = parser.parse_args()

    if args.name:
        # student
        if " " in args.name:
            student = baka.student_name(args.name)
        else:            
            student = baka.student(prijmeni=args.name)

        title = "Student: {} {} - {}, {}".format(student.prijmeni, student.jmeno, student.trida, student.ev_cislo)
        # vypsat akce studenta
        vypis_akce(pay.akce_studenta(student), student=student, title=title)
        
        if args.pay: 
            # vypsat platby studenta
            vypis_platby(pay.platby(student=student), title="Výpis plateb - {} {}".format(student.prijmeni, student.jmeno))
        if args.mail and args.akce: 
            # poslat studentovi mail ohledně konkrétní akce
            akce = list(pay.akce(id_akce=args.akce))
            eprihlaska = get_eprihlaska(args.akce)
            mail_reminder(akce, eprihlaska=eprihlaska, typ=args.mail, student=student)

    elif args.akce:
        # zadáné ID platební akce
        vypis_akce(pay.akce(id_akce=args.akce), id_akce=args.akce)  
        akce = list(pay.akce(id_akce=args.akce))
        eprihlaska = get_eprihlaska(args.akce)
        if args.pay:
            # -- výpis plateb pro danou akci --
            vypis_platby(pay.platby(akce=akce[0]))
        elif args.scope:
            # -- výpis části seznamu --
            info_text = {'dluh':'Výpis dlužníků akce',
                        'zaplaceno':'Výpis studentů s uhrazenou platbou',
                        'podpis':'Výpis studentů s nepodepsanou e-přihláškou'
            }
            vypis_student(akce[0], title=info_text[args.scope] , scope=args.scope, eprihlaska=eprihlaska)
        elif args.mail == 'platba' or args.mail == 'podpis':
            # -- poslat upomínku --
            mail_reminder(akce, eprihlaska=eprihlaska, typ=args.mail)
        elif args.mail == 'all':
            # -- poslat upomínku - vše --
            [mail_reminder(akce, eprihlaska, typ=typ) for typ in ['platba', 'podpis']]
        else:            
            vypis_student(akce[0], title="Seznam studentů akce", eprihlaska=eprihlaska)
    else:
        vypis_akce(pay.akce(), title="Výpis všech platebních akcí")