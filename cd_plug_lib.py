''' Lib for Plugin
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '2.1.10 2017-06-10'
Content
    log                 Logger with timing
    get_translation     i18n
    dlg_wrapper         Wrapper for dlg_custom: pack/unpack values, h-align controls
ToDo: (see end of file)
'''

import  sys, os, gettext, logging, inspect, time, collections, json
from    time        import perf_counter

try:
    import  cudatext            as app
    from    cudatext        import ed
    import  cudax_lib           as apx
except:
    import  sw                  as app
    from    sw              import ed
    from . import cudax_lib     as apx

pass;                           # Logging
pass;                           from pprint import pformat
pass;                           import tempfile

odict       = collections.OrderedDict
T,F,N       = True, False, None
GAP         = 5
c13,c10,c9  = chr(13),chr(10),chr(9)
REDUCTIONS  = {'lb'     :'label'
            ,  'ln-lb'  :'linklabel'
            ,  'llb'    :'linklabel'
            ,  'ed'     :'edit'             # ro_mono_brd
            ,  'ed_pw'  :'edit_pwd'
            ,  'sp-ed'  :'spinedit'         # min_max_inc
            ,  'me'     :'memo'             # ro_mono_brd
            ,  'bt'     :'button'           # def_bt
            ,  'rd'     :'radio'
            ,  'ch'     :'check'
            ,  'ch-bt'  :'checkbutton'
            ,  'ch-b'   :'checkbutton'
            ,  'chb'    :'checkbutton'
            ,  'ch-gp'  :'checkgroup'
            ,  'rd-gp'  :'radiogroup'
            ,  'cb'     :'combo'
            ,  'cb-ro'  :'combo_ro'
            ,  'cb-r'   :'combo_ro'
            ,  'lbx'    :'listbox'
            ,  'ch-lbx' :'checklistbox'
            ,  'lvw'    :'listview'
            ,  'ch-lvw' :'checklistview'
            ,  'tabs'   :'tabs'
            ,  'clr'    :'colorpanel'
            ,  'im'     :'image'
            ,  'f-lb'   :'filter_listbox'
            ,  'f-lvw'  :'filter_listview'
            ,  'fr'     :'bevel'
            ,  'pn'     :'panel'
            ,  'gr'     :'group'
            
#           ,  'fid'    :'focused'
            }

def f(s, *args, **kwargs):return s.format(*args, **kwargs)

def log(msg='', *args, **kwargs):
    if args or kwargs:
        msg = msg.format(*args, **kwargs)
    if Tr.tr is None:
        Tr.tr=Tr()
    return Tr.tr.log(msg)
    
class Tr :
    tr=None
    """ Трассировщик.
        Основной (единственный) метод: log(строка) - выводит указанную строку в лог.
        Управляется через команды в строках для вывода.
        Команды:
            >>  Увеличить сдвиг при выводе будущих строк (пока жив возвращенный объект) 
            (:) Начать замер нового вложенного периода, закончить когда умрет возвращенный объект 
            (== Начать замер нового вложенного периода 
            ==> Вывести длительность последнего периода 
            ==) Вывести длительность последнего периода и закончить его замер
            =}} Отменить все замеры
        Вызов log с командой >> (увеличить сдвиг) возвращает объект, 
            который при уничтожении уменьшит сдвиг 
        """
    sec_digs        = 2                     # Точность отображения секунд, кол-во дробных знаков
    se_fmt          = ''
    mise_fmt        = ''
    homise_fmt      = ''
    def __init__(self, log_to_file=None) :
        # Поля объекта
        self.gap    = ''                # Отступ
        self.tm     = perf_counter()    # Отметка времени о запуске
        self.stms   = []                # Отметки времени о начале замера спец.периода

        if log_to_file:
            logging.basicConfig( filename=log_to_file
                                ,filemode='w'
                                ,level=logging.DEBUG
                                ,format='%(message)s'
                                ,datefmt='%H:%M:%S'
                                ,style='%')
        else: # to stdout
            logging.basicConfig( stream=sys.stdout
                                ,level=logging.DEBUG
                                ,format='%(message)s'
                                ,datefmt='%H:%M:%S'
                                ,style='%')
        # Tr()
    def __del__(self):
        logging.shutdown()

    class TrLiver :
        cnt = 0
        """ Автоматически сокращает gap при уничножении 
            Показывает время своей жизни"""
        def __init__(self, tr, ops) :
            # Поля объекта
            self.tr = tr
            self.ops= ops
            self.tm = 0
            self.nm = Tr.TrLiver.cnt
            if '(:)' in self.ops :
                # Начать замер нового интервала
                self.tm = perf_counter()
        def log(self, msg='') :
            if '(:)' in self.ops :
                msg = '{}(:)=[{}]{}'.format( self.nm, Tr.format_tm( perf_counter() - self.tm ), msg ) 
                logging.debug( self.tr.format_msg(msg, ops='') )
        def __del__(self) :
            #pass;                  logging.debug('in del')
            if '(:)' in self.ops :
                msg = '{}(:)=[{}]'.format( self.nm, Tr.format_tm( perf_counter() - self.tm ) ) 
                logging.debug( self.tr.format_msg(msg, ops='') )
            if '>>' in self.ops :
                self.tr.gap = self.tr.gap[:-1]
                
    def log(self, msg='') :
        if '(:)' in msg :
            Tr.TrLiver.cnt += 1
            msg     = msg.replace( '(:)', '{}(:)'.format(Tr.TrLiver.cnt) )  
        logging.debug( self.format_msg(msg) )
        if '>>' in msg :
            self.gap = self.gap + c9
            # Создаем объект, который при разрушении сократит gap
        if '>>' in msg or '(:)' in msg:
            return Tr.TrLiver(self,('>>' if '>>' in msg else '')+('(:)' if '(:)' in msg else ''))
            # return Tr.TrLiver(self,iif('>>' in msg,'>>','')+iif('(:)' in msg,'(:)',''))
        else :
            return self 
        # Tr.log
            
#   def format_msg(self, msg, dpth=2, ops='+fun:ln +wait==') :
    def format_msg(self, msg, dpth=3, ops='+fun:ln +wait==') :
        if '(==' in msg :
            # Начать замер нового интервала
            self.stms   = self.stms + [perf_counter()]
            msg = msg.replace( '(==', '(==[' + Tr.format_tm(0) + ']' )

        if '+fun:ln' in ops :
            frCaller= inspect.stack()[dpth] # 0-format_msg, 1-Tr.log|Tr.TrLiver, 2-log, 3-need func
            try:
                cls = frCaller[0].f_locals['self'].__class__.__name__ + '.'
            except:
                cls = ''
            fun     = (cls + frCaller[3]).replace('.__init__','()')
            ln      = frCaller[2]
            msg     = '[{}]{}{}:{} '.format( Tr.format_tm( perf_counter() - self.tm ), self.gap, fun, ln ) + msg
        else : 
            msg     = '[{}]{}'.format( Tr.format_tm( perf_counter() - self.tm ), self.gap ) + msg

        if '+wait==' in ops :
            if ( '==)' in msg or '==>' in msg ) and len(self.stms)>0 :
                # Закончить/продолжить замер последнего интервала и вывести его длительность
                sign    = '==)' if '==)' in msg else '==>'
                # sign    = icase( '==)' in msg, '==)', '==>' )
                stm = '[{}]'.format( Tr.format_tm( perf_counter() - self.stms[-1] ) )
                msg = msg.replace( sign, sign+stm )
                if '==)' in msg :
                    del self.stms[-1] 

            if '=}}' in msg :
                # Отменить все замеры
                self.stms   = []
                
        return msg.replace('¬',c9).replace('¶',c10)
        # Tr.format

    @staticmethod
    def format_tm(secs) :
        """ Конвертация количества секунд в 12h34'56.78" """
        if 0==len(Tr.se_fmt) :
            Tr.se_fmt       = '{:'+str(3+Tr.sec_digs)+'.'+str(Tr.sec_digs)+'f}"'
            Tr.mise_fmt     = "{:2d}'"+Tr.se_fmt
            Tr.homise_fmt   = "{:2d}h"+Tr.mise_fmt
        h = int( secs / 3600 )
        secs = secs % 3600
        m = int( secs / 60 )
        s = secs % 60
        return Tr.se_fmt.format(s) \
                if 0==h+m else \
               Tr.mise_fmt.format(m,s) \
                if 0==h else \
               Tr.homise_fmt.format(h,m,s)
        # return icase( 0==h+m,   Tr.se_fmt.format(s)
        #             , 0==h,     Tr.mise_fmt.format(m,s)
        #             ,           Tr.homise_fmt.format(h,m,s) )
        # Tr.format_tm
    # Tr

def get_desktop_environment():
    #From http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=1139057
    if sys.platform in ["win32", "cygwin"]:
        return "win"
    elif sys.platform == "darwin":
        return "mac"
    else: #Most likely either a POSIX system or something not much common
        desktop_session = os.environ.get("DESKTOP_SESSION")
        if desktop_session is not None: #easier to match if we doesn't have  to deal with caracter cases
            desktop_session = desktop_session.lower()
            if desktop_session in ["gnome","unity", "cinnamon", "mate", "xfce4", "lxde", "fluxbox", 
                                   "blackbox", "openbox", "icewm", "jwm", "afterstep","trinity", "kde"]:
                return desktop_session
            ## Special cases ##
            # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
            # There is no guarantee that they will not do the same with the other desktop environments.
            elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
                return "xfce4"
            elif desktop_session.startswith("ubuntu"):
                return "unity"       
            elif desktop_session.startswith("lubuntu"):
                return "lxde" 
            elif desktop_session.startswith("kubuntu"): 
                return "kde" 
            elif desktop_session.startswith("razor"): # e.g. razorkwin
                return "razor-qt"
            elif desktop_session.startswith("wmaker"): # e.g. wmaker-common
                return "windowmaker"
        if os.environ.get('KDE_FULL_SESSION') == 'true':
            return "kde"
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            if not "deprecated" in os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                return "gnome2"
        #From http://ubuntuforums.org/showthread.php?t=652320
        elif is_running("xfce-mcs-manage"):
            return "xfce4"
        elif is_running("ksmserver"):
            return "kde"
    return "unknown"
def is_running(process):
    #From http://www.bloggerpolis.com/2011/05/how-to-check-if-a-process-is-running-using-python/
    # and http://richarddingwall.name/2009/06/18/windows-equivalents-of-ps-and-kill-commands/
    try: #Linux/Unix
        s = subprocess.Popen(["ps", "axw"],stdout=subprocess.PIPE)
    except: #Windows
        s = subprocess.Popen(["tasklist", "/v"],stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return True
    return False

ENV2FITS= {'win':
            {'check'      :-2
            ,'edit'       :-3
            ,'button'     :-4
            ,'combo_ro'   :-4
            ,'combo'      :-3
            ,'checkbutton':-4
            ,'linklabel'  : 0
            ,'spinedit'   :-3
            }
          ,'unity':
            {'check'      :-3
            ,'edit'       :-5
            ,'button'     :-4
            ,'combo_ro'   :-5
            ,'combo'      :-6
            ,'checkbutton':-4
            ,'linklabel'  : 0
            ,'spinedit'   :-6
            }
          ,'mac':
            {'check'      :-1
            ,'edit'       :-3
            ,'button'     :-3
            ,'combo_ro'   :-2
            ,'combo'      :-3
            ,'checkbutton':-2
            ,'linklabel'  : 0
            ,'spinedit'   : 0   ##??
            }
          }
fit_top_by_env__cash    = {}
def fit_top_by_env__clear():
    global fit_top_by_env__cash
    fit_top_by_env__cash    = {}
def fit_top_by_env(what_tp, base_tp='label'):
    """ Get "fitting" to add to top of first control to vertical align inside text with text into second control.
        The fittings rely to platform: win, unix(kde,gnome,...), mac
    """
    if what_tp==base_tp:
        return 0
    if (what_tp, base_tp) in fit_top_by_env__cash:
        pass;                  #log('cashed what_tp, base_tp={}',(what_tp, base_tp))
        return fit_top_by_env__cash[(what_tp, base_tp)]
    env     = get_desktop_environment()
    pass;                      #env = 'mac'
    fit4lb  = ENV2FITS.get(env, ENV2FITS.get('win'))
    fit     = 0
    if base_tp=='label':
        fit = apx.get_opt('dlg_wrapper_fit_va_for_'+what_tp, fit4lb.get(what_tp, 0))
    else:
        fit = fit_top_by_env(what_tp) - fit_top_by_env(base_tp)
    pass;                      #log('what_tp, base_tp, fit={}',(what_tp, base_tp, fit))
    return fit_top_by_env__cash.setdefault((what_tp, base_tp), fit)
   #def fit_top_by_env

def rgb_to_int(r,g,b):
    return r | (g<<8) | (b<<16)
def dlg_wrapper(title, w, h, cnts, in_vals={}, focus_cid=None):
    """ Wrapper for dlg_custom. 
        Params
            title, w, h     Title, Width, Height 
            cnts            List of static control properties
                                [{cid:'*', tp:'*', t:1,l:1,w:1,r:1,b;1,h:1,tid:'cid', cap:'*', hint:'*', en:'0', props:'*', items:[*], act='0'}]
                                cid         (opt)(str) C(ontrol)id. Need only for buttons and conrols with value (and for tid)
                                tp               (str) Control types from wiki or short names
                                t           (opt)(int) Top
                                tid         (opt)(str) Ref to other control cid for horz-align text in both controls
                                l                (int) Left
                                r,b,w,h     (opt)(int) Position. w>>>r=l+w, h>>>b=t+h, b can be omitted
                                cap              (str) Caption for labels and buttons
                                hint        (opt)(str) Tooltip
                                en          (opt)('0'|'1'|True|False) Enabled-state
                                props       (opt)(str) See wiki
                                act         (opt)('0'|'1'|True|False) Will close dlg when changed
                                items            (str|list) String as in wiki. List structure by types:
                                                            [v1,v2,]     For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox
                                                            (head, body) For listview, checklistview 
                                                                head    [(cap,width),(cap,width),]
                                                                body    [[r0c0,r0c1,],[r1c0,r1c1,],[r2c0,r2c1,],]
            in_vals         Dict of start values for some controls 
                                {'cid':val}
            focus_cid       (opt) Control cid for start focus
        Return
            btn_cid         Clicked/changed control cid
            {'cid':val}     Dict of new values for the same (as in_vals) controls
                                Format of values is same too.
            focus_cid       Focused control cid
            [cid]           List of controls with changed values
        Short names for types
            lb      label
            ln-lb   linklabel
            ed      edit
            sp-ed   spinedit
            me      memo
            bt      button
            rd      radio
            ch      check
            ch-bt   checkbutton
            ch-gp   checkgroup
            rd-gp   radiogroup
            cb      combo
            cb-ro   combo_ro
            lbx     listbox
            ch-lbx  checklistbox
            lvw     listview
            ch-lvw  checklistview
        Example.
            def ask_number(ask, def_val):
                cnts=[dict(        tp='lb',tid='v',l=3 ,w=70,cap=ask)
                     ,dict(cid='v',tp='ed',t=3    ,l=73,w=70)
                     ,dict(cid='!',tp='bt',t=45   ,l=3 ,w=70,cap='OK',props='1')
                     ,dict(cid='-',tp='bt',t=45   ,l=73,w=70,cap='Cancel')]
                vals={'v':def_val}
                while True:
                    aid,vals,fid,chds=dlg_wrapper('Example',146,75,cnts,vals,'v')
                    if aid is None or btn=='-': return def_val
                    if not re.match(r'\d+$', vals['v']): continue
                    return vals['v']
    """
    pass;                      #log('in_vals={}',pformat(in_vals, width=120))
    cnts        = [cnt for cnt in cnts if cnt.get('vis', True) in (True, '1')]
    cid2i       = {cnt['cid']:i for i,cnt in enumerate(cnts) if 'cid' in cnt}
    if True:
        # Checks
        no_tids = {cnt['tid']   for   cnt in    cnts    if 'tid' in cnt and  cnt['tid'] not in cid2i}
        if no_tids:
            raise Exception(f('No cid(s) for tid(s): {}', no_tids))
        no_vids = {cid          for   cid in    in_vals if                          cid not in cid2i}
        if no_vids:
            raise Exception(f('No cid(s) for vals: {}', no_vids))
    
    simpp   = ['cap','hint'
              ,'props'
              ,'color'
              ,'font_name', 'font_size', 'font_color', 'font'
              ,'act'
              ,'en','vis'
             #,'tag'
              ]
    ctrls_l = []
    for cnt in cnts:
        tp      = cnt['tp']
        tp      = REDUCTIONS.get(tp, tp)
        if tp=='--':
            # Horz-line
            t   = cnt.get('t')
            l   = cnt.get('l', 0)                   # def: from DlgLeft
            r   = cnt.get('r', l+cnt.get('w', w))   # def: to   DlgRight
            lst = ['type=label']
            lst+= ['cap='+'—'*1000]
            lst+= ['font_color='+str(rgb_to_int(185,185,185))]
            lst+= ['pos={l},{t},{r},0'.format(l=l,t=t,r=r)]
            ctrls_l+= [chr(1).join(lst)]
            continue#for cnt
            
        lst     = ['type='+tp]

        # Preprocessor
        if 'props' in cnt:
            pass
        elif tp=='label' and cnt['cap'][0]=='>':
            #   cap='>smth' --> cap='smth', props='1' (r-align)
            cnt['cap']  = cnt['cap'][1:]
            cnt['props']= '1'
        elif tp=='label' and cnt.get('ralign'):
            cnt['props']=    cnt.get('ralign')
        elif tp=='button' and cnt.get('def_bt') in ('1', True):
            cnt['props']= '1'
        elif tp=='spinedit' and cnt.get('min_max_inc'):
            cnt['props']=       cnt.get('min_max_inc')
        elif tp=='linklabel' and cnt.get('url'):
            cnt['props']=        cnt.get('url')
        elif tp=='listview' and cnt.get('grid'):
            cnt['props']=       cnt.get('grid')
        elif tp=='tabs' and cnt.get('at_botttom'):
            cnt['props']=   cnt.get('at_botttom')
        elif tp=='colorpanel' and cnt.get('brdW_fillC_fontC_brdC'):
            cnt['props']=         cnt.get('brdW_fillC_fontC_brdC')
        elif tp in ('edit', 'memo') and cnt.get('ro_mono_brd'):
            cnt['props']=               cnt.get('ro_mono_brd')

#       # Simple props
#       for k in ['cap', 'hint', 'props', 'font_name', 'font_size', 'font_color', 'font', 'name']:
#               lst += [k+'='+str(cnt[k])]

        # Position:
        #   t[op] or tid, l[eft] required
        #   w[idth]  >>> r[ight ]=l+w
        #   h[eight] >>> b[ottom]=t+h
        #   b dont need for buttons, edit, labels
        l       = cnt['l']
        t       = cnt.get('t', 0)
        if 'tid' in cnt:
            # cid for horz-align text
            bs_cnt  = cnts[cid2i[cnt['tid']]]
            bs_tp   = bs_cnt['tp']
            t       = bs_cnt['t'] + fit_top_by_env(tp, REDUCTIONS.get(bs_tp, bs_tp))
        r       = cnt.get('r', l+cnt.get('w', 0)) 
        b       = cnt.get('b', t+cnt.get('h', 0)) 
        lst    += ['pos={l},{t},{r},{b}'.format(l=l,t=t,r=r,b=b)]
#       if 'en' in cnt:
#           val     = cnt['en']
#           lst    += ['en='+('1' if val in [True, '1'] else '0')]

        if 'items' in cnt:
            items   = cnt['items']
            if isinstance(items, str):
                pass
            elif tp in ['listview', 'checklistview']:
                # For listview, checklistview: "\t"-separated items.
                #   first item is column headers: title1+"="+size1 + "\r" + title2+"="+size2 + "\r" +...
                #   other items are data: cell1+"\r"+cell2+"\r"+...
                # ([(hd,wd)], [[cells],[cells],])
                items   = '\t'.join(['\r'.join(['='.join((hd,sz)) for hd,sz in items[0]])]
                                   +['\r'.join(row) for row in items[1]]
                                   )
            else:
                # For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox: "\t"-separated lines
                items   = '\t'.join(items)
            lst+= ['items='+items]
        
        # Prepare val
        if cnt.get('cid') in in_vals:
            in_val = in_vals[cnt['cid']]
            if False:pass
            elif tp in ['check', 'radio', 'checkbutton'] and isinstance(in_val, bool):
                # For check, radio, checkbutton: value "0"/"1" 
                in_val  = '1' if in_val else '0'
            elif tp=='memo':
                # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
                if isinstance(in_val, list):
                    in_val = '\t'.join([v.replace('\t', chr(2)) for v in in_val])
                else:
                    in_val = in_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
            elif tp=='checkgroup' and isinstance(in_val, list):
                # For checkgroup: ","-separated checks (values "0"/"1") 
                in_val = ','.join(in_val)
            elif tp in ['checklistbox', 'checklistview'] and isinstance(in_val, tuple):
                # For checklistbox, checklistview: index+";"+checks 
                in_val = ';'.join( (str(in_val[0]), ','.join( in_val[1]) ) )
            lst+= ['val='+str(in_val)]

#       if 'act' in cnt:    # must be last in lst
#           val     = cnt['act']
#           lst    += ['act='+('1' if val in [True, '1'] else '0')]
 
        # Simple props
        for k in simpp:
            if k in cnt:
                v   = cnt[k]
                v   = ('1' if v else '0') if isinstance(v, bool) else str(v)
                lst += [k+'='+v]
        pass;                  #log('lst={}',lst)
        ctrls_l+= [chr(1).join(lst)]
       #for cnt
    pass;                      #log('ok ctrls_l={}',pformat(ctrls_l, width=120))

    pass;                      #ctrls_fn=tempfile.gettempdir()+os.sep+'dlg_custom_ctrls.txt'
    pass;                      #open(ctrls_fn, 'w', encoding='UTF-8').write('\n'.join(ctrls_l).replace('\r',''))
    pass;                      #log(f(r'app.dlg_custom("{t}",{w},{h},open(r"{fn}",encoding="UTF-8").read(), {f})',t=title, w=w, h=h, fn=ctrls_fn, f=cid2i.get(focus_cid, -1)))
    ans     = app.dlg_custom(title, w, h, '\n'.join(ctrls_l), cid2i.get(focus_cid, -1))
    if ans is None: return None, None, None, None   # btn_cid, {cid:v}, focus_cid, [cid]
    pass;                      #log('ans={})',ans)

    btn_i,  \
    vals_ls = ans[0], ans[1].splitlines()
    pass;                      #log('btn_i,vals_ls={})',(btn_i,vals_ls))

    focus_cid   = ''
    if vals_ls[-1].startswith('focused='):
        # From API 1.0.156 dlg_custom also returns index of active control
        focus_n_s   = vals_ls.pop()
        focus_i     = int(focus_n_s.split('=')[1])
        focus_cid   = cnts[focus_i].get('cid', '')
        pass;                  #log('btn_i,vals_ls,focus_cid={})',(btn_i,vals_ls,focus_cid))

    act_cid     = cnts[btn_i]['cid']
    # Parse output values
    an_vals = {cid:vals_ls[cid2i[cid]] for cid in in_vals}
    for cid in an_vals:
        cnt     = cnts[cid2i[cid]]
        tp      = cnt['tp']
        tp      = REDUCTIONS.get(tp, tp)
        in_val  = in_vals[cid]
        an_val  = an_vals[cid]
        pass;                  #log('tp,in_val,an_val={})',(tp,in_val,an_val))
        if False:pass
        elif tp=='memo':
            # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
            if isinstance(in_val, list):
                an_val = [v.replace(chr(2), '\t') for v in an_val.split('\t')]
               #in_val = '\t'.join([v.replace('\t', chr(2)) for v in in_val])
            else:
                an_val = an_val.replace('\t','\n').replace(chr(2), '\t')
               #in_val = in_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
        elif tp=='checkgroup' and isinstance(in_val, list):
            # For checkgroup: ","-separated checks (values "0"/"1") 
            an_val = an_val.split(',')
           #in_val = ','.join(in_val)
        elif tp in ['checklistbox', 'checklistview'] and isinstance(in_val, tuple):
            an_val = an_val.split(';')
            an_val = (an_val[0], an_val[1].split(','))
           #in_val = ';'.join(in_val[0], ','.join(in_val[1]))
        elif isinstance(in_val, bool): 
            an_val = an_val=='1'
        elif tp=='listview':
            an_val = -1 if an_val=='' else int(an_val)
        else: 
            an_val = type(in_val)(an_val)
            pass;              #log('type(in_val),an_val={})',(type(in_val),an_val))
        an_vals[cid]    = an_val
       #for cid
    chds    = [cid for cid in in_vals if in_vals[cid]!=an_vals[cid]]
    if focus_cid:
        # If out focus points to button then will point to a unique changed control
        focus_tp= cnts[cid2i[focus_cid]]['tp']
        focus_tp= REDUCTIONS.get(focus_tp, focus_tp)
        if focus_tp in ('button'):
            focus_cid   = '' if len(chds)!=1 else chds[0]
    return  act_cid \
        ,   an_vals \
        ,   focus_cid \
        ,   chds
   #def dlg_wrapper

LMBD_HIDE   = lambda cid,ag:None
class BaseDlgAgent:
    """ 
    Simple helper to use dlg_proc(). See wiki.freepascal.org/CudaText_API#dlg_proc

    Main features:
    - All controls are created once then some of them can be changed via callbacks (attribute 'call').
    - The helper stores config version of form's and control's attributes.
      So the helper can return two versions of attributes: configured and actual (live).
    - Helper marshals complex data ('items' for type=list/combo/..., 'val' for type=memo)
    - Helper can to save/restore form position and sizes to/from file "settings/forms data.json".
      Key for saving is form's 'cap' (default) or a value in call BaseDlgAgent(..., option={'form data key':'smth'})
      If value of 'form data key' is empty then helper doesnt save/restore.

    Format of constructor 
        BaseDlgAgent(ctrls, form=None, focused=None)
            ctrls             [(name,{...})]        To create controls with the names
                                                    All attributes from 
                                                        wiki.freepascal.org/CudaText_API#Control_properties
                                                        excluded: name, callback
            form              {...}                 To configure form
                                                    All attributes from
                                                        wiki.freepascal.org/CudaText_API#Form_properties
            focused           name_to_focus         To set focus
    
    Format of callback for a control
        def callname(name_of_event_control, agent):
            # Reactions
            return None                         #   To hide form
            return {}                           #   To keep controls and form state
            return {'ctrls':  [(name,{...})]    #   To change controls with the names
                   ,'form':   {...}             #   To change form
                   ,'focused':name_to_focus     #   To set focus
                   }                            #   Any key ('ctrls','form','focused') can be ommited.
    Callback cannot add new controls or change type values.
    
    Useful methods of agent
    - agent.cattr(name, '??', live=T)               To get a control actual/configured attribute
    - agent.cattrs(name, ['??'], live=T)            To get dict of a control listed actual/configured attributes
    - agent.fattr('??', live=T)                     To get actual/configured form attribute
    - agent.fattrs(live=T, ['??']=None)             To get actual/configured all/listed form attributes
    
    Tricks
    Automatically set some values for attributes
        - 'act':True    If 'call'   set in a control (not 'button')
        - 'w_min':w     If 'resize' set in the form
        - 'h_min':h     If 'resize' set in the form

    Example. Dialog with two buttons.
    BaseDlgAgent(
        ctrls=[('b1', dict(type='button',             cap='Click', x=0, y= 0, w=100, 
                call=lambda name,ag:{'ctrls':[('b1',{'cap':'OK',             'w':70})]}
               ))
              ,('b2', dict(type='button', cap='Close', x=0, y=30, w=100,
                call=lambda name,ag:None)
               )]
    ,   form=dict(cap='Two buttons', x=0, y=0, w=100, h=60)
    ,   focused='b1'
    ).show()
    """
 
    def activate(self):
        """ Set focus to the form """
        app.dlg_proc(self.id_dlg, app.DLG_FOCUS)
       #def activate
    
    def show(self, callbk_on_exit=None):
        """ Show the form """
        ed_caller   = ed
        
        app.dlg_proc(self.id_dlg, app.DLG_SHOW_MODAL)
        
        BaseDlgAgent._form_acts('save', id_dlg=self.id_dlg, key4store=self.opts.get('form data key'))
        if callbk_on_exit:  callbk_on_exit(self)
        app.dlg_proc(self.id_dlg, app.DLG_FREE)
        ed_caller.focus()
       #def show
        
    def fattr(self, attr, live=True, defv=None):
        """ Return one form property """
        pr  = app.dlg_proc(self.id_dlg
                        , app.DLG_PROP_GET)     if live else    self.form
        pass;                  #log('pr={}',(pr))
        rsp = pr.get(attr, defv)
        if live and attr=='focused':
            rsp = app.dlg_proc(self.id_dlg, app.DLG_CTL_PROP_GET, index=rsp)['name']
        return rsp
       #def fattr

    def fattrs(self, live=True, attrs=None):
        """ Return form properties """
        pr  = app.dlg_proc(self.id_dlg
                        , app.DLG_PROP_GET)     if live else    self.form
        return pr   if not attrs else   {attr:pr.get(attr) for attr in attrs}
       #def fattrs

    def cattr(self, name, attr, live=True, defv=None):
        """ Return one the control property """
        live= False if attr in ('type',) else live          # Unchangable
        pr  = app.dlg_proc(self.id_dlg
                        , app.DLG_CTL_PROP_GET
                        , name=name)            if live else    self.ctrls[name]
        if attr not in pr:  return defv
        rsp = pr[attr]
        return self._take_val(name, rsp, defv)   if attr=='val' and live else    rsp
       #def cattr

    def cattrs(self, name, attrs=None, live=True):
        """ Return the control properties """
        pr  = app.dlg_proc(self.id_dlg
                        , app.DLG_CTL_PROP_GET
                        , name=name)            if live else    self.ctrls[name]
        attrs   = attrs if attrs else list(pr.keys())
        pass;                  #log('pr={}',(pr))
        rsp     = {attr:pr.get(attr) for attr in attrs if attr not in ('val','on_change','callback')}
        if 'val' in attrs:
            rsp['val'] = self._take_val(name, pr.get('val')) if live else pr.get('val')
        return rsp
       #def cattrs
       
    def bind_do(self, names=None, gui2data=True):
        names   = names if names else self.binds.keys()
        assert self.bindof
        for name in names:
            if name not in self.binds: continue
            attr    = 'val'
            if gui2data:
                self.bindof.__setattr__(self.binds[name], self.cattr(name, attr))
            else:
                val = self.bindof.__getattr(self.binds[name])
                self._update({'ctrls':[(name, {attr:val})]})
       #def bind_do

    def __init__(self, ctrls, form=None, focused=None, options=None):
        # Fields
        self.opts   = options if options else {}
        
        self.id_dlg = app.dlg_proc(0, app.DLG_CREATE)
        self.ctrls  = None                      # Conf-attrs of all controls by name (may be with 'val')
        self.form   = None                      # Conf-attrs of form
#       self.callof = self.opts.get('callof')   # Object for callbacks
        self.bindof = self.opts.get('bindof')   # Object for bind control's values to object's fields
        self.binds  = {}                        # {name:'other obj field name'}
        
        self._setup_base(ctrls, form, focused)

        rtf     = self.opts.get('gen_repro_to_file', False)
        rtf_fn  = rtf if isinstance(rtf, str) else 'repro_dlg_proc.py'
        if rtf:   self._gen_repro_code(tempfile.gettempdir()+os.sep+rtf_fn)
       #def __init__
        
    def _setup_base(self, ctrls, form, focused=None):
        """ Arrange and fill all: controls attrs, form attrs, focus.
            Params
                ctrls   [(id, {})]
                form    {}
                focused id
        """
        #NOTE: DlgAg init
        self.ctrls  = odict(ctrls)
        self.form   = form.copy()     if form   else {}
        
#       if 'checks'=='checks':
#           if focused and focused not in self.ctrls:
#               raise Exception(f('Unknown focused: {}', focused))
        
        # Create controls
        for name, cfg_ctrl in ctrls:
            assert 'type' in cfg_ctrl
            # Create control
            cfg_ctrl.pop('callback', None)
            cfg_ctrl.pop('on_change', None)
            ind_c   = app.dlg_proc(self.id_dlg
                        , app.DLG_CTL_ADD
                        , cfg_ctrl['type'])
            pass;              #log('ind_c,cfg_ctrl[type]={}',(ind_c,cfg_ctrl['type']))
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_PROP_SET
                        , index=ind_c
                        , prop=self._prepare_c_pr(name, cfg_ctrl))
           #for cnt
        
        if self.form:
            fpr     = self.form
            if fpr.get('resize', False):
                fpr['w_min']    = fpr.get('w_min', fpr['w'])
                fpr['h_min']    = fpr.get('h_min', fpr['h'])
            fpr     = BaseDlgAgent._form_acts('move', form=fpr, key4store=self.opts.get('form data key'))
            fpr['topmost']      = True
            app.dlg_proc(       self.id_dlg
                            , app.DLG_PROP_SET
                            , prop=fpr)
        
        if focused in self.ctrls:
            self.form['focused']   = focused
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_FOCUS
                        , name=focused)
       #def _setup_base
       
    def _take_val(self, name, liv_val, defv=None):
        tp      = self.ctrls[name]['type']
        old_val = self.ctrls[name].get('val', defv)
        new_val = liv_val
        if False:pass
        elif tp=='memo':
            # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
            if isinstance(old_val, list):
                new_val = [v.replace(chr(2), '\t') for v in liv_val.split('\t')]
               #liv_val = '\t'.join([v.replace('\t', chr(2)) for v in old_val])
            else:
                new_val = liv_val.replace('\t','\n').replace(chr(2), '\t')
               #liv_val = old_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
        elif tp=='checkgroup' and isinstance(old_val, list):
            # For checkgroup: ","-separated checks (values "0"/"1") 
            new_val = liv_val.split(',')
           #in_val = ','.join(in_val)
        elif tp in ['checklistbox', 'checklistview'] and isinstance(old_val, tuple):
            new_val = liv_val.split(';')
            new_val = (new_val[0], new_val[1].split(','))
           #liv_val = ';'.join(old_val[0], ','.join(old_val[1]))
        elif isinstance(old_val, bool): 
            new_val = liv_val=='1'
        elif tp=='listview':
            new_val = -1 if liv_val=='' else int(liv_val)
        elif old_val is not None: 
            new_val = type(old_val)(liv_val)
        return new_val
       #def _take_val

    def _prepare_c_pr(self, name, cfg_ctrl, opts={}):
        pass;                  #log('name, cfg_ctrl={}',(name, cfg_ctrl))
        c_pr    = {k:v for (k,v) in cfg_ctrl.items() if k not in ['call', 'bind', 'items', 'val']}
        c_pr['name'] = name
        tp      = cfg_ctrl['type']

        if 'val' in cfg_ctrl        and opts.get('prepare val', True):
            in_val  = cfg_ctrl['val']
            if False:pass
            elif tp=='memo':
                # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
                if isinstance(in_val, list):
                    in_val = '\t'.join([v.replace('\t', chr(2)) for v in in_val])
                else:
                    in_val = in_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
            elif tp=='checkgroup' and isinstance(in_val, list):
                # For checkgroup: ","-separated checks (values "0"/"1") 
                in_val = ','.join(in_val)
            elif tp in ['checklistbox', 'checklistview'] and isinstance(in_val, tuple):
                # For checklistbox, checklistview: index+";"+checks 
                in_val = ';'.join( (str(in_val[0]), ','.join( in_val[1]) ) )
            c_pr['val']     = in_val

        if 'items' in cfg_ctrl        and opts.get('prepare items', True):
            items   = cfg_ctrl['items']
            if isinstance(items, str):
                pass
            elif tp in ['listview', 'checklistview']:
                # For listview, checklistview: "\t"-separated items.
                #   first item is column headers: title1+"="+size1 + "\r" + title2+"="+size2 + "\r" +...
                #   other items are data: cell1+"\r"+cell2+"\r"+...
                # ([(hd,wd)], [[cells],[cells],])
                items   = '\t'.join(['\r'.join(['='.join((hd,sz)) for hd,sz in items[0]])]
                                   +['\r'.join(row) for row in items[1]]
                                   )
            else:
                # For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox: "\t"-separated lines
                items   = '\t'.join(items)
            c_pr['items']   = items

        if cfg_ctrl.get('bind'):
            self.binds[name]    = cfg_ctrl['bind']
        
        if callable(cfg_ctrl.get('call'))        and opts.get('prepare call', True):
            if tp!='button':
                c_pr['act'] = True
            user_callbk = cfg_ctrl['call']
            
            def bda_c_callbk(idd, idc, data):
                pass;              #log('idc,name={}',(idc,name))
                upds = user_callbk(name, self)
                if upds is None:                                        # To hide/close
                    app.dlg_proc(self.id_dlg, app.DLG_HIDE)
                    return
                elif not upds:                                          # No changes
                    return
                self._update(ctrls  =upds.get('ctrls',  [])
                            ,form   =upds.get('form',   {})
                            ,focused=upds.get('focused',None))
               #def agent_cbk
            c_pr['on_change']= bda_c_callbk
        
        return c_pr
       #def _prepare_c_pr

    def _update(self, ctrls={}, form={}, focused=None):
        """ Change some attrs of form/controls """
        pass;                  #log('',())
        pass;                  #log('ctrls={}',(ctrls))
        pass;                  #log('form={}',(form))
        pass;                  #log('focused={}',(focused))
        for name, new_ctrl in ctrls.items():
            pass;              #log('name, new_ctrl={}',(name, new_ctrl))
                
            cfg_ctrl= self.ctrls[name]
            cfg_ctrl.update(new_ctrl)
            new_ctrl['type']    = cfg_ctrl['type']
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_PROP_SET
                        , name=name
                        , prop=self._prepare_c_pr(name, new_ctrl, {'ctrls':ctrls}))
        
        if form:
            self.form.update(form)
            pass;              #log('form={}',(self.fattrs(live=F)))
            pass;              #log('form={}',(self.fattrs()))
            pass;              #log('form={}',(form))
            app.dlg_proc(   self.id_dlg
                        , app.DLG_PROP_SET
                        , prop=form)

        if focused in self.ctrls:
            self.form['focused']    = focused
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_FOCUS
                        , name=focused)
       #def _update
    
    def _gen_repro_code(self, rerpo_fn):
        # Repro-code
        l       = '\n'
        srp     =    ''
        srp    +=    'idd=dlg_proc(0, DLG_CREATE)'
        for idC in range(app.dlg_proc(self.id_dlg, app.DLG_CTL_COUNT)):
            prC = app.dlg_proc(self.id_dlg, app.DLG_CTL_PROP_GET, index=idC)
            name = prC['name']
            prC.update({k:v for k,v in self.ctrls[name].items() if k not in ('callback','call')})
            srp+=l+f('idc=dlg_proc(idd, DLG_CTL_ADD,"{}")', prC['type'])
            srp+=l+f('dlg_proc(idd, DLG_CTL_PROP_SET, index=idc, prop={})', repr(prC))
        prD     = app.dlg_proc(self.id_dlg, app.DLG_PROP_GET)
        prD.update(self.form)
        srp    +=l+f('dlg_proc(idd, DLG_PROP_SET, prop={})', repr(prD))
        srp    +=l+f('dlg_proc(idd, DLG_CTL_FOCUS, index={})', prD['focused'])
        srp    +=l+  'dlg_proc(idd, DLG_SHOW_MODAL)'
        srp    +=l+  'dlg_proc(idd, DLG_FREE)'
        open(rerpo_fn, 'w', encoding='UTF-8').write(srp)
        pass;                   log(r'exec(open(r"{}", encoding="UTF-8").read())', rerpo_fn)
       #def _gen_repro_code
    
    @staticmethod
    def _form_acts(act, form=None, id_dlg=None, key4store=None):
        """ Save/Restore pos of form """
        pass;                  #log('act, form, id_dlg={}',(act, form, id_dlg))
        CFG_JSON= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'forms data.json'
        stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=odict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  odict()
        
        def get_form_key(prs):
            fm_cap  = prs['cap']
            return fm_cap if ' (' not in fm_cap else fm_cap[:fm_cap.rindex(' (')]
        
        if False:pass
        
        if act=='move' and form:
            fm_key  = key4store if key4store else get_form_key(form)
            pass;              #log('fm_key={}',(fm_key))
            if fm_key not in stores:    return form
            form.update(stores[fm_key])
            pass;              #log('!upd form={}',(form))
            return form
        
        if act=='save' and id_dlg:
            dlg_pr  = app.dlg_proc(id_dlg, app.DLG_PROP_GET)
            fm_key  = key4store if key4store else get_form_key(dlg_pr)
            pass;              #log('{}={}', fm_key,{k:v for k,v in dlg_pr.items() if k in ('x','y','w','h')})
            stores[fm_key]  = {k:v for k,v in dlg_pr.items() if k in ('x','y','w','h')}
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
       #def _form_acts
    
   #class BaseDlgAgent

class DlgAgent(BaseDlgAgent):
    """ 
    Helper to use dlg_proc(). See wiki.freepascal.org/CudaText_API#dlg_proc

    Main base features :
    - All controls are created once then some of them can be changed via callbacks (attribute 'call').
    - The helper stores config version of form's and control's attributes.
      So the helper can return two versions of attributes: configured and actual (live).
    - Helper marshals complex data ('items' for type=list/combo/..., 'val' for type=memo)
    - Helper can to save/restore form position and sizes to/from file "settings/forms data.json".

    Main extra features:
    - Helper handles attributes names of controls
        Helper adds short synonyms: 
            cid is name
            tp  is type
            fid is focused
        Helper adds new attributes to simplify config: 
            l,r,t,b,tid,a,aid 
        are translated to live 
            x,y,w,h,a_*,sp*
    - Helper allows to aligns texts from linear controls (by tid attribute)

    Terms
        conf-attr - configured attribute (key and value passed to agent from plugin)
        live-attr - actual attribute     (key and value taked from dlg_proc)
    
    Rules
    1. All conrols have conf-attr 'cid'|'name'. It must be unique.
    2. All conrols have conf-attr 'tp'|'type'. 
        Value of 'tp'|'type' can be any API values or shortened variants from REDUCTIONS.
    3. Conrol position can be set 
        - directly by x,y,w,h
        - computed by enough subset of l,r,w,t,b,h (x=l, y=t, l+w=r, t+h=b)
        - computed by tid (refer to cid|name of control, from which to get t and add a bit to align texts)
    4. Controls values (attribute 'val') can be passed to agent as separate collection:
        - parameter 'vals' to call constructor
        - key 'vals' in dict to return from callback
    5. Need focused control cid can be passed to agent
        - parameter 'fid' to call constructor
        - key 'fid' in dict to return from callback
        - key 'fid' into parameter 'form'
       Live focused control cid can be asked as agent.fattr('fid')
    6. Anchors 'aid' and 'a' are used to plan control's position on form resize. 
        Note: agent's anchors cannot set initial control position (except to center control).
        'aid' points to a tagret: form (empty value, default) or cid.
        'a' has string value which can include character:
            - |     to center           the control by horz/vert with the target
            t T     to anchor top    of the control to top/bottom of the target
            b B     to anchor bottom of the control to top/bottom of the target
            l L     to anchor left   of the control to left/right of the target
            r R     to anchor right  of the control to left/right of the target
        Padding with target (live-attrs 'sp_*') are auto-calculated by initial positions of both elements.
        Examples
            a='|lR'     
    7. Format of callback for a control
        def callname(name_of_event_control, agent):
            'smth'
            return None                         #   To hide form
            return {}                           #   To keep controls and form state
            return {'ctrls':[(nm,{...})]        #   To change controls with pointed names
                   ,'vals':{nm:...}             #   To change controls 'val' with pointed names
                   ,'form':{...}                #   To change form attributes
                   ,'focused':name_to_focus     #   To change focus
                   ,'fid':cid_to_focus          #   To change focus
                   }                            #   Any key ('ctrls','vals','form','fid','focused') can be ommited.
        Callback cannot add/del controls or change cid,type,a,aid
        Callback have to conside the form as it has initial size - agent will recalculate to actual state.
        Useful methods of agent
        - agent.cattr(cid, '??', live=T)        To get a control actual/configured attribute
        - agent.cattrs(cid, ['??'], live=T)     To get dict of a control listed actual/configured attributes
        - agent.cval(cid, live=T)               To get actual/configured 'val' attribute (short of agent.cattr(cid, 'val'))
        - agent.cvals([cid], live=T)            To get dict of actual/configured 'val' the listed attributes
        - agent.fattr('??', live=T)             To get actual/configured form attribute
        - agent.fattrs(live=T, ['??']=None)     To get actual/configured all/listed form attributes
    8. Match of different conf-attr and live-attr keys: 
        cid     name
        tp      type
        l       x 
        r       x+w
        t       y
        b       y+h
        tid     y
        aid     a_*[0]
        a       a_*[1], sp*
        fid     focused
        call    callback
    9. List of same conf-attr and live-attr keys
        w h 
        cap hint 
        props 
        color 
        font_name font_size font_color font
        val
        act
        en vis 
        tag 
        tab_stop tab_order
    10. Tricks
        - 'tid' vertical aligns not a pair of controls themself but text in its. 
          For this it uses platform specific data. The data can be configured by call dlg_valign_consts()
        - If cap of a label starts with '>' then the character is cut and 'prop' set to '1' to right alignment
        - Attributes
            def_bt spinedit url grid at_botttom brdW_fillC_fontC_brdC ro_mono_brd
          are used as temporary and readable version of 'prop'. 
          They can be use to configure as others but key to ask is 'prop'.
        - Attribute 
            sto     tab_stop
          is used as temporary version of 'tab_stop'. 
    
    Example. Horz-resized modal dialog with two buttons. First button is stretched, second is pinned to right.
    DlgAgent(
        ctrls=[('b1', dict(type='button',             cap='Click', x=0, y= 0, w=100, a='lR'
                call=lambda name,ag:{'ctrls':[('b1',{'cap':'OK',             'w':70})]}
               ))
              ,('b2', dict(type='button', cap='Close', x=0, y=30, w=100,             a='LR'
                call=lambda name,ag:None)
               )]
    ,   form=dict(cap='Two buttons', x=0, y=0, w=100, h=60)
    ,   focused='b1'
    ).show()
    """

    def __init__(self, ctrls, vals=None, form=None, fid=None, focused=None, options=None):
        options = options or {}
        super().__init__([], options={k:v for k,v in options.items() if k not in ['gen_repro_to_file']})
        # Inherited Fields
#       self.opts
#       self.id_dlg
#       self.ctrls
#       self.form
        self._setup(ctrls, vals, form, focused or fid)

        rtf     = options.get('gen_repro_to_file', False)
        rtf_fn  = rtf if isinstance(rtf, str) else 'repro_dlg_proc.py'
        if rtf:   self._gen_repro_code(tempfile.gettempdir()+os.sep+rtf_fn)
       #def __init__
        
    def cval(self, cid, live=True, defv=None):
        """ Return the control val property """
        return self.cattr(cid, 'val', live=live, defv=defv)
    def cvals(self, cids, live=True):
        """ Return the controls val property """
        return {cid:self.cattr(cid, 'val', live=live) for cid in cids}
    
    def _setup(self, ctrls, vals=None, form=None, fid=None):
        """ Arrange and fill all: controls static/dinamic attrs, form attrs, focus.
            Params
                ctrls   [{}]
                vals    {cid:v}
                form    {}
                fid     str
        """
        #NOTE: DlgAg init
        self.ctrls  = odict(ctrls)
        self.form   = form.copy()       if form     else {}

        if 'checks'=='checks':
            no_tids = {cnt['tid'] for cnt in ctrls if 'tid' in cnt and cnt['tid'] not in self.ctrls}
            if no_tids:
                raise Exception(f('No cid for tid: {}', no_tids))
            no_vids = {cid for cid in vals if cid not in self.ctrls} if vals else None
            if no_vids:
                raise Exception(f('No cid for val: {}', no_vids))
#           if fid and fid not in self.ctrls:
#               raise Exception(f('No fid: {}', fid))
        
        if vals:
            for cid, val in vals.items():
                self.ctrls[cid]['val']  = val
        
        # Create controls
        for cid,cfg_ctrl in ctrls:
            cfg_ctrl.pop('callback', None)
            cfg_ctrl.pop('on_change', None)
#           cid     = cfg_ctrl.get('cid', cfg_ctrl.get('name'))
#           cfg_ctrl['cid']     = cid
#           cfg_ctrl['name']    = cid
            assert 'type' in cfg_ctrl or 'tp'  in cfg_ctrl
            tp      = cfg_ctrl.get('tp',  cfg_ctrl.get('type'))
            cfg_ctrl['tp']      = tp
            cfg_ctrl['type']    = REDUCTIONS.get(tp, tp)
            ind_c   = app.dlg_proc(self.id_dlg
                        , app.DLG_CTL_ADD
                        , cfg_ctrl['type'])
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_PROP_SET
                        , index=ind_c
                        , prop=self._prepare_c_pr(cid, cfg_ctrl))    # Upd live-attrs
           #for cnt

        fpr     = self.form
        if fpr.get('resize', False):
            self._prepare_anchors()                                         # a,aid -> a_*,sp_*
            fpr['w_min']    = fpr.get('w_min', fpr['w'])
            fpr['h_min']    = fpr.get('h_min', fpr['h'])
        fpr     = DlgAgent._form_acts('move', form=fpr)
        fpr['topmost']      = True
        app.dlg_proc(           self.id_dlg
                            , app.DLG_PROP_SET
                            , prop=fpr)                         # Upd live-attrs
        
        fid     = fid   if fid in self.ctrls else     self.form.get('fid')
        if fid in self.ctrls:
            self.form['fid']    = fid                           # Upd conf-attrs
            self.form['focused']= fid
            app.dlg_proc(   self.id_dlg
                        , app.DLG_CTL_FOCUS
                        , name=fid)                             # Upd live-attrs

        pass;                   self._gen_repro_code(tempfile.gettempdir()+os.sep+'repro_dlg_proc.py')     if F else None
       #def _setup

    EXTRA_C_ATTRS   = ['tp','l','t','r','b','tid','a','aid']
    def _prepare_c_pr(self, cid, cfg_ctrl, opts={}):
        pass;                  #log('cid, cfg_ctrl={}',(cid, cfg_ctrl))
#       cid     = cfg_ctrl['cid']
        tp      = cfg_ctrl['type']  # reduced
        DlgAgent._preprocessor(cfg_ctrl, tp)                                # sto -> tab_stop, ... -> props
        c_pr    = super()._prepare_c_pr(cid
                    , {k:v for k,v in cfg_ctrl.items() if k not in DlgAgent.EXTRA_C_ATTRS}
                    , {'prepare call':False})                               # items -> items, val -> val
        c_pr.update(self._prep_pos_attrs(cfg_ctrl, cid, opts.get('ctrls')))                    # l,r,t,b,tid -> x,y,w,h
        pass;                  #log('c_pr={}',(c_pr))

        if callable(cfg_ctrl.get('call')):
            if tp!='button':
                c_pr['act'] = True
            user_callbk = cfg_ctrl['call']
            
            def da_c_callbk(idd, idc, data):
                pass;          #log('idc,cid={}',(idc,cid))
                upds    = user_callbk(cid, self)
                if upds is None:                                        # To hide/close
                    app.dlg_proc(self.id_dlg, app.DLG_HIDE)
                    return
                elif not upds:                                          # No changes
                    return
                pass;          #log('upds={}',(upds))
                if isinstance(upds, tuple) or isinstance(upds, list) :
                    upds    = deep_upd(*upds)
                    pass;      #log('upds={}',(upds))
                ctrls_u = odict(upds.get('ctrls',  []))
                pass;          #log('ctrls_u={}',(ctrls_u))
                vals    = upds.get('vals',   {})
                form    = upds.get('form',   {})
                fid     = upds.get('fid'  , upds.get('focused', form.get('fid', form.get('focused'))))
                if False:pass
                elif vals and not ctrls_u:
                    ctrls_u     = { cid_    :  {'val':val} for cid_, val in vals.items()}
                elif vals and     ctrls_u:
                    for cid_, val in vals.items():
                        if cid_ not in ctrls_u:
                            ctrls_u[cid_]   =  {'val':val}
                        else:
                            ctrls_u[cid_]['val']    = val
                for cid_, c in ctrls_u.items():
                    pass;      #log('cid_, c={}',(cid_, c))
                    c.pop('callback', None)
                    c.pop('on_change', None)
                    c.pop('call', None)
                    c['type']   = self.ctrls[cid_]['type']
                super(DlgAgent,self)._update(ctrls  =ctrls_u
                                            ,form   =form
                                            ,focused=fid)
                if fid in self.ctrls:
                    self.form['fid']    = fid
               #def agent_cbk
            
            c_pr['on_change']= da_c_callbk
           #if callable
        
        return c_pr
       #def _prepare_c_pr
       
    def _prepare_anchors(self):
        """ Translate attrs 'a' 'aid' to 'a_*','sp_*'
            Values for 'a' are str-mask with signs
                'l' 'L'    fixed distanse ctrl-left     to trg-left  or trg-right
                't' 'T'    fixed distanse ctrl-top      to trg-top   or trg-bottom
                'r' 'R'    fixed distanse ctrl-right    to trg-left  or trg-right
                'b' 'B'    fixed distanse ctrl-bottom   to trg-top   or trg-bottom
        """
        fm_w    = self.form['w']
        fm_h    = self.form['h']
        for cid,cnt in self.ctrls.items():
            anc     = cnt.get('a'  , '')
            aid     = cnt.get('aid', None)
            trg_w,  \
            trg_h   = fm_w, fm_h
            if aid in self.ctrls:
                prTrg   = app.dlg_proc(self.id_dlg, app.DLG_CTL_PROP_GET, name=aid)
                trg_w,  \
                trg_h   = prTrg['w'], prTrg['h']
            if not anc: continue
            prOld   = app.dlg_proc(self.id_dlg, app.DLG_CTL_PROP_GET, name=cid)
            prAnc   = {}
            if '-' in anc:
                # Center by horz
                prAnc.update(dict( a_l=(aid, '-')
                                  ,a_r=(aid, '-')))
            if 'L' in anc and 'R' in anc:
                # Both left/right to form right
                prAnc.update(dict( a_l=None
                                  ,a_r=(aid, ']'), sp_r=trg_w-prOld['x']-prOld['w']))
            if 'l' in anc and 'R' in anc:
                # Left to form left. Right to form right.
                prAnc.update(dict( a_l=(aid, '['), sp_l=      prOld['x']
                                  ,a_r=(aid, ']'), sp_r=trg_w-prOld['x']-prOld['w']))
            if '|' in anc:
                # Center by vert
                prAnc.update(dict( a_t=(aid, '-')
                                  ,a_b=(aid, '-')))
            if 'T' in anc and 'B' in anc:
                # Both top/bottom to form bottom
                prAnc.update(dict( a_t=None
                                  ,a_b=(aid, ']'), sp_b=trg_h-prOld['y']-prOld['h']))
            if 't' in anc and 'B' in anc:
                # Top to form top. Bottom to form bottom.
                prAnc.update(dict( a_t=(aid, '['), sp_t=      prOld['y']
                                  ,a_b=(aid, ']'), sp_b=trg_h-prOld['y']-prOld['h']))
            if prAnc:
                app.dlg_proc(self.id_dlg, app.DLG_CTL_PROP_SET, name=cid, prop=prAnc)
       #def _prepare_anchors

    def _prep_pos_attrs(self, cnt, cid, ctrls4t=None):
        # Position:
        #   t[op] or tid, l[eft] required
        #   w[idth]  >>> r[ight ]=l+w
        #   h[eight] >>> b[ottom]=t+h
        #   b dont need for buttons, edit, labels
#       if not [k for k in cnt.keys() if k in ('l','t','r','b','tid')]:
#           return {k:v for (k,v) in cnt.items() if k in ('x','y','w','h')}

        pass;                  #log('cid, cnt={}',(cid, cnt))
        prP     =  {}

        if 'l' in cnt:
            prP['x']    = cnt['l']
        if 'r' in cnt and 'x' in prP:
            prP['w']    = cnt['r'] - prP['x']
        if 'w' in cnt:
            prP['w']    = cnt['w']

        if 't' in cnt:
            prP['y']    = cnt['t']
#       t       = cnt.get('t', 0)   if 't' in cnt else  self.cattr(cid, 't', live=False)
        elif 'tid' in cnt:
            ctrls4t = ctrls4t if ctrls4t else self.ctrls
            assert cnt['tid'] in ctrls4t
            # cid for horz-align text
            bs_cnt4t= ctrls4t[   cnt['tid']]
            bs_cnt  = self.ctrls[cnt['tid']]
            bs_tp   = bs_cnt['tp']
            bs_tp   = REDUCTIONS.get(bs_tp, bs_tp)
            tp      = self.ctrls[cid]['tp']
            tp      = REDUCTIONS.get(tp, tp)
            pass;              #log('tp, bs_tp, fit, bs_cnt={}',(tp, bs_tp, fit_top_by_env(tp, bs_tp), bs_cnt))
            t       = bs_cnt4t['t'] + fit_top_by_env(tp, bs_tp)
            prP['y']    = t
        if 'b' in cnt and 'y' in prP:
            prP['h']    = cnt['b'] - prP['y']
        if 'h' in cnt:
            prP['h']    = cnt['h']
            
#       b       = cnt.get('b', t+cnt.get('h', 0)) 

#       l       = cnt['l']          if 'l' in cnt else  self.cattr(cid, 'l', live=False)
#       r       = cnt.get('r', l+cnt.get('w', 0)) 
#       prP     =  dict(x=l, y=t, w=r-l)
#       prP.update(dict(h=cnt.get('h')))    if 0!=cnt.get('h', 0) else 0 
        pass;                  #log('prP={}',(prP))
        return prP
       #def _prep_pos_attrs

    @staticmethod
    def _preprocessor(cnt, tp):
        if 'sto' in cnt:
            cnt['tab_stop'] = cnt.pop('sto')
            
        if 'props' in cnt:
            pass
        elif tp=='label' and 'cap' in cnt and cnt['cap'][0]=='>':
            #   cap='>smth' --> cap='smth', props='1' (r-align)
            cnt['cap']  = cnt['cap'][1:]
            cnt['props']= '1'
        elif tp=='label' and    cnt.get('ralign'):
            cnt['props']=       cnt.pop('ralign')
        elif tp=='button' and cnt.get('def_bt') in ('1', True):
            cnt['props']= '1'
        elif tp=='spinedit' and cnt.get('min_max_inc'):
            cnt['props']=       cnt.pop('min_max_inc')
        elif tp=='linklabel' and    cnt.get('url'):
            cnt['props']=           cnt.pop('url')
        elif tp=='listview' and cnt.get('grid'):
            cnt['props']=       cnt.pop('grid')
        elif tp=='tabs' and     cnt.get('at_botttom'):
            cnt['props']=       cnt.pop('at_botttom')
        elif tp=='colorpanel' and   cnt.get('brdW_fillC_fontC_brdC'):
            cnt['props']=           cnt.pop('brdW_fillC_fontC_brdC')
        elif tp in ('edit', 'memo') and cnt.get('ro_mono_brd'):
            cnt['props']=               cnt.pop('ro_mono_brd')
       #def _preprocessor

#class DlgAgent


########################################################################
########################################################################
########################################################################
#pass;                           from cudatext import *
def dlg_valign_consts():
    pass;                      #log('ok')
    UP,DN   = '↑↑','↓↓'
    DLG_W,  \
    DLG_H   = 335, 280
    ctrls   = ['check'
              ,'edit'
              ,'button'   
              ,'combo_ro' 
              ,'combo'    
              ,'checkbutton'
              ,'linklabel'
              ,'spinedit'
              ]
    ctrls_sp= [('_sp'+str(1+ic),nc) for ic, nc in enumerate(ctrls)]
    fits    = {sp:fit_top_by_env(nc) for sp, nc in ctrls_sp}
    hints   = {sp:nc+': '+str(fits[sp]) for sp, nc in ctrls_sp}

    def save():
        scam        = app.app_proc(app.PROC_GET_KEYSTATE, '') if app.app_api_version()>='1.0.143' else ''
        if not scam:#aid_m=='save':
            for sp, nc in ctrls_sp:
                fit = fits[sp]
                if fit==fit_top_by_env(nc): continue#for ic, nc
                apx.set_opt('dlg_wrapper_fit_va_for_'+nc, fit)
               #for ic, nc
            fit_top_by_env__clear()
            return None#break#while
            
        if scam=='c':#aid_m=='c/save': # Report
            rpt = 'env:'+get_desktop_environment()
            rpt+= c13 + c13.join(hints.values())
            aid_r, *_t = dlg_wrapper(_('Report'), 230,310,
                 [dict(cid='rprt',tp='me'    ,t=5   ,l=5 ,h=200 ,w=220)
                 ,dict(           tp='lb'    ,t=215 ,l=5        ,w=220  ,cap=_('Send the report to the address'))
                 ,dict(cid='mail',tp='ed'    ,t=235 ,l=5        ,w=220)
                 ,dict(           tp='lb'    ,t=265 ,l=5        ,w=150  ,cap=_('or post it on'))
                 ,dict(cid='gith',tp='ln-lb' ,t=265 ,l=155      ,w=70   ,cap='GitHub',props='https://github.com/kvichans/cuda_fit_v_alignments/issues')
                 ,dict(cid='-'   ,tp='bt'    ,t=280 ,l=205-80   ,w=80   ,cap=_('Close'))
                 ], dict(rprt=rpt
                        ,mail='kvichans@mail.ru')
                 ,  focus_cid='rprt')
        return {}
       #def save

    def up_dn(ag, cid, sht):
        pass;                  #log('cid,sht={}',(cid,sht))
        sign    = cid[-1]
        sp      = '_sp'+sign
        fits[sp]= fits[sp] + sht
        nonlocal hints
        hints   = {sp:nc+': '+str(fits[sp]) for sp, nc in ctrls_sp}
        return {'ctrls':[(cid ,dict(y=ag.cattr(cid, 'y')+sht ,x=ag.cattr(cid, 'x') ,hint=hints[sp] ))]}
#       return {'ctrls':[dict(cid=cid ,t=ag.cattr(cid, 't')+sht ,l=ag.cattr(cid, 'l') ,w=ag.cattr(cid, 'w') ,hint=hints[sp] )]}
       #def up_dn

    cnts    = \
            [('lb1' ,dict(tp='lb'    ,t= 10              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('ch1' ,dict(tp='ch'    ,t= 10+fits['_sp1'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp1']     ,val=F))
            ,('up1' ,dict(tp='bt'    ,t= 10-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'ch1',-1) ))
            ,('dn1' ,dict(tp='bt'    ,t= 10-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'ch1', 1) ))
                
            ,('lb2' ,dict(tp='lb'    ,t= 40              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('ed2' ,dict(tp='ed'    ,t= 40+fits['_sp2'] ,l=115  ,w=100                          ,hint=hints['_sp2']     ,val='=======?'))
            ,('up2' ,dict(tp='bt'    ,t= 40-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'ed2',-1) ))
            ,('dn2' ,dict(tp='bt'    ,t= 40-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'ed2', 1) ))
                
            ,('lb3' ,dict(tp='lb'    ,t= 70              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('bt3' ,dict(tp='bt'    ,t= 70+fits['_sp3'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp3']     ))
            ,('up3' ,dict(tp='bt'    ,t= 70-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'bt3',-1) ))
            ,('dn3' ,dict(tp='bt'    ,t= 70-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'bt3', 1) ))
                
            ,('lb4' ,dict(tp='lb'    ,t=100              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('cbo4',dict(tp='cb-ro' ,t=100+fits['_sp4'] ,l=115  ,w=100  ,items=['=======?']     ,hint=hints['_sp4']     ,val=0))
            ,('up4' ,dict(tp='bt'    ,t=100-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'cbo4',-1)))
            ,('dn4' ,dict(tp='bt'    ,t=100-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'cbo4', 1)))
                
            ,('lb5' ,dict(tp='lb'    ,t=130              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('cb5' ,dict(tp='cb'    ,t=130+fits['_sp5'] ,l=115  ,w=100  ,items=['=======?']     ,hint=hints['_sp5']     ,val='=======?'))
            ,('up5' ,dict(tp='bt'    ,t=130-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'cb5',-1) ))
            ,('dn5' ,dict(tp='bt'    ,t=130-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'cb5', 1) ))
                
            ,('lb6' ,dict(tp='lb'    ,t=160              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('chb6',dict(tp='ch-bt' ,t=160+fits['_sp6'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp6']     ,val=0))
            ,('up6' ,dict(tp='bt'    ,t=160-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'chb6',-1)))
            ,('dn6' ,dict(tp='bt'    ,t=160-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'chb6', 1)))
                
            ,('lb7', dict(tp='lb'    ,t=190              ,l=  5  ,w=100  ,cap='==============='                          ))
            ,('lnb7',dict(tp='ln-lb' ,t=190+fits['_sp7'] ,l=115  ,w=100  ,cap='=======?'         ,props=hints['_sp7']    ))
            ,('up7' ,dict(tp='bt'    ,t=190-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'lnb7',-1)))
            ,('dn7' ,dict(tp='bt'    ,t=190-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'lnb7', 1)))
                
            ,('lb8' ,dict(tp='lb'    ,t=220              ,l=  5  ,w=100  ,cap='4444444444444444'                         ))
            ,('sp8' ,dict(tp='sp-ed' ,t=220+fits['_sp8'] ,l=115  ,w=100  ,props='0,4444444,1'    ,hint=hints['_sp8']     ,val=4444444))
            ,('up8' ,dict(tp='bt'    ,t=220-3            ,l=230  ,w=50   ,cap=UP ,call=lambda cid,ag: up_dn(ag,'sp8',-1) ))
            ,('dn8' ,dict(tp='bt'    ,t=220-3            ,l=280  ,w=50   ,cap=DN ,call=lambda cid,ag: up_dn(ag,'sp8', 1) ))
                
            ,('save',dict(tp='bt'    ,t=DLG_H-30         ,l=115  ,w=100  ,cap=_('&Save')     ,call=lambda cid,ag: save()
                                                                                ,hint=_('Apply the fittings to controls of all dialogs.'
                                                                                        '\rCtrl+Click  - Show data to mail report.')))
            ,('-'   ,dict(tp='bt'    ,t=DLG_H-30         ,l=230  ,w=100  ,cap=_('Cancel')    ,call=(lambda cid,ag: None) ))
            ]
    agent   = DlgAgent( form=dict(cap=_('Adjust vertical alignments'), w=DLG_W, h=DLG_H)
                       ,ctrls=cnts ,fid = '-'
                               #,options={'gen_repro_to_file':'repro_dlg_valign_consts.py'}
            ).show()    #NOTE: dlg_valign
   #def dlg_valign_consts


def get_hotkeys_desc(cmd_id, ext_id=None, keys_js=None, def_ans=''):
    """ Read one or two hotkeys for command 
            cmd_id [+ext_id]
        from 
            settings\keys.json
        Return 
            def_ans                     If no  hotkeys for the command
            'Ctrl+Q'            
            'Ctrl+Q * Ctrl+W'           If one hotkey  for the command
            'Ctrl+Q/Ctrl+T'            
            'Ctrl+Q * Ctrl+W/Ctrl+T'    If two hotkeys for the command
    """
    if keys_js is None:
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        keys_js     = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}

    cmd_id  = f('{},{}', cmd_id, ext_id) if ext_id else cmd_id
    if cmd_id not in keys_js:
        return def_ans
    cmd_keys= keys_js[cmd_id]
    desc    = '/'.join([' * '.join(cmd_keys.get('s1', []))
                       ,' * '.join(cmd_keys.get('s2', []))
                       ]).strip('/')
    return desc
   #def get_hotkeys_desc

class CdSw:
    """ Proxy to use plugins both in CudaText and SynWrite"""
    
    ENC_UTF8    = str(app.EDENC_UTF8_NOBOM) if 'sw'==app.__name__ else 'UTF-8'

    @staticmethod
    def ed_group(grp):
        if 'sw'==app.__name__:
            return ed                   ##!!
        else:
            return app.ed_group(grp)

    @staticmethod
    def app_idle():
        if 'sw'==app.__name__:
            pass
        else:
            return app.app_idle()

    @staticmethod
    def file_open(filename, group=-1):
        if 'sw'==app.__name__:
            return app.file_open(filename, group=group)
        else:
            return app.file_open(filename, group)

    @staticmethod
    def get_groups_count():
        if 'sw'==app.__name__:
            dct = {
                app.GROUPING_ONE     : 1,
                app.GROUPING_2VERT   : 2,
                app.GROUPING_2HORZ   : 2,
                app.GROUPING_3VERT   : 3,
                app.GROUPING_3HORZ   : 3,
                app.GROUPING_1P2VERT : 3,
                app.GROUPING_1P2HORZ : 3,
                app.GROUPING_4VERT   : 4,
                app.GROUPING_4HORZ   : 4,
                app.GROUPING_4GRID   : 4,
                app.GROUPING_6GRID   : 6
            }
            gr_mode = app.get_app_prop(app.PROP_GROUP_MODE)
            return dct.get(gr_mode, 1)
        else:
            dct = {
                app.GROUPS_ONE      : 1,
                app.GROUPS_2VERT    : 2,
                app.GROUPS_2HORZ    : 2,
                app.GROUPS_3VERT    : 3,
                app.GROUPS_3HORZ    : 3,
                app.GROUPS_3PLUS    : 3,
                app.GROUPS_1P2VERT  : 3,
                app.GROUPS_1P2HORZ  : 3,
                app.GROUPS_4VERT    : 4,
                app.GROUPS_4HORZ    : 4,
                app.GROUPS_4GRID    : 4,
                app.GROUPS_6GRID    : 6
            }
            gr_mode = app.app_proc(app.PROC_GET_GROUPING, '')
            return dct.get(gr_mode, 1)

    @staticmethod
    def get_carets(_ed):
        if 'sw'==app.__name__:
            x,y = _ed.get_caret_xy()
            return [(x,y,-1,-1)]        ##!!
        else:
            return _ed.get_carets()

    MARKERS_ADD             = 1 if 'sw'==app.__name__ else app.MARKERS_ADD
    MARKERS_DELETE_ALL      = 2 if 'sw'==app.__name__ else app.MARKERS_DELETE_ALL
    @staticmethod
    def attr(_ed, id, **kwargs):
        if 'sw'==app.__name__:
            if id==CdSw.MARKERS_DELETE_ALL:
                return _ed.set_attr(app.ATTRIB_CLEAR_ALL, 0)
            x   = kwargs['x']
            y   = kwargs['y']+1 ##!!
            ln  = kwargs['len']
            _ed.set_sel(ed.xy_pos(x, y), ln)
            _ed.set_attr(app.ATTRIB_SET_UNDERLINE, 0)
            _ed.set_sel(ed.xy_pos(x, y), 0)
            return  ##!!
        else:
            return _ed.attr(id, **kwargs)             

    PROC_GET_FIND_OPTIONS   = 22 if 'sw'==app.__name__ else app.PROC_GET_FIND_OPTIONS
    PROC_GET_LANG           = 40 if 'sw'==app.__name__ else app.PROC_GET_LANG
    @staticmethod
    def app_proc(pid, defv):
        if 'sw'!=app.__name__:
            return app.app_proc(pid, defv)
        if False:pass
        elif pid==CdSw.PROC_GET_FIND_OPTIONS:
            return ''
        elif pid==CdSw.PROC_GET_LANG:
            return 'en'
        return ''

    @staticmethod
    def set_caret(_ed, posx, posy, endx=-1, endy=-1):
        if 'sw'==app.__name__:
           #_ed.set_caret_xy(x, y)
            if endx==-1:    # no sel
                return _ed.set_caret_xy(posx, posy)
            else:           # with sel
                pos = _ed.xy_pos(posx, posy)
                end = _ed.xy_pos(endx, endy)
                return _ed.set_sel(pos, end-pos)
#               return _ed.set_caret_xy(posx, posy) ##!!
        else:
           #set_caret(posx, posy, endx=-1, endy=-1)
            return _ed.set_caret(posx, posy, endx, endy)

    @staticmethod
    def dlg_dir(init_dir):
        if 'sw'==app.__name__:
            return app.dlg_folder('', init_dir)
        else:
            return app.dlg_dir(init_dir)
    
    MENU_LIST     = 0 if 'sw'==app.__name__ else app.MENU_LIST
    MENU_LIST_ALT = 1 if 'sw'==app.__name__ else app.MENU_LIST_ALT
    @staticmethod
    def dlg_menu(mid, text):
        if 'sw'==app.__name__:
            return app.dlg_menu(app.MENU_SIMPLE if mid==CdSw.MENU_LIST else app.MENU_DOUBLE, '', text)
        else:
            return app.dlg_menu(mid, text)
    
    @staticmethod
    def msg_status(msg, process_messages=False):
        if 'sw'==app.__name__:
            return app.msg_status(msg)
        else:
            return app.msg_status(msg, process_messages)
    
    @staticmethod
    def msg_status_alt(msg, secs):
        if 'sw'==app.__name__:
            return app.msg_status(msg)
        else:
            return app.msg_status_alt(msg, secs)
    
    @staticmethod
    def get_setting_dir():
        return  app.app_ini_dir()       if 'sw'==app.__name__ else \
                app.app_path(app.APP_DIR_SETTINGS)
   #class CudSyn

def gen_repro_code(idDlg, rerpo_fn):
    # Repro-code
    l       = chr(13)
    srp     =    ''
    srp    +=    'idd=dlg_proc(0, DLG_CREATE)'
    for idC in range(app.dlg_proc(idDlg, app.DLG_CTL_COUNT)):
        prC = app.dlg_proc(idDlg, app.DLG_CTL_PROP_GET, index=idC)
        prTg= json.loads(prC.pop('tag','{}'))
        prC.update(prTg)
#       prC['props'] = prTg.get('props','')
#       prC['props'] = json.loads(prC['tag']).get('props','')
        srp+=l+f('idc=dlg_proc(idd, DLG_CTL_ADD,"{}")', prC.pop('type',None))
        srp+=l+f('dlg_proc(idd, DLG_CTL_PROP_SET, index=idc, prop={})', repr(prC))
    prD     = app.dlg_proc(idDlg, app.DLG_PROP_GET)
    srp    +=l+f('dlg_proc(idd, DLG_PROP_SET, prop={})', repr({'cap':prD['cap'], 'w':prD['w'], 'h':prD['h']}))
    srp    +=l+f('dlg_proc(idd, DLG_CTL_FOCUS, index={})', prD['focused'])
    srp    +=l+  'dlg_proc(idd, DLG_SHOW_MODAL)'
    srp    +=l+  'dlg_proc(idd, DLG_FREE)'
    open(rerpo_fn, 'w', encoding='UTF-8').write(srp)
    pass;                       log(r'exec(open(r"{}", encoding="UTF-8").read())', rerpo_fn)
   #def gen_repro_code

def get_translation(plug_file):
    ''' Part of i18n.
        Full i18n-cycle:
        1. All GUI-string in code are used in form 
            _('')
        2. These string are extracted from code to 
            lang/messages.pot
           with run
            python.exe <pypython-root>\Tools\i18n\pygettext.py -p lang <plugin>.py
        3. Poedit (or same program) create 
            <module>\lang\ru_RU\LC_MESSAGES\<module>.po
           from (cmd "Update from POT") 
            lang/messages.pot
           It allows to translate all "strings"
           It creates (cmd "Save")
            <module>\lang\ru_RU\LC_MESSAGES\<module>.mo
        4. get_translation uses the file to realize
            _('')
    '''
    plug_dir= os.path.dirname(plug_file)
    plug_mod= os.path.basename(plug_dir)
    lng     = CdSw.app_proc(CdSw.PROC_GET_LANG, '')
#   lng     = app.app_proc(app.PROC_GET_LANG, '')
    lng_mo  = plug_dir+'/lang/{}/LC_MESSAGES/{}.mo'.format(lng, plug_mod)
    if os.path.isfile(lng_mo):
        t   = gettext.translation(plug_mod, plug_dir+'/lang', languages=[lng])
        _   = t.gettext
        t.install()
    else:
        _   =  lambda x: x
    return _
   #def get_translation

def upd_dict(d1, d2):
    rsp = d1.copy()
    rsp.update(d2)
    return rsp
   #def upd_dict

def deep_upd(dct1, *dcts):
    pass;                      #log('dct1, dcts={}',(dct1, dcts))
    rsp   = dct1.copy()
    for dct in dcts:
        for k,v in dct.items():
            if False:pass
            elif k not in rsp:
                rsp[k]  = v
            elif isinstance(rsp[k], dict) and isinstance(v, dict):
                rsp[k].update(v)
            else:
                rsp[k]  = v
    pass;                      #log('rsp={}',(rsp))
    return rsp
   #def deep_upd

def isint(what):    return isinstance(what, int)
   
_   = get_translation(__file__) # I18N

if __name__ == '__main__' :     # Tests
    class C:
        def m1(self, p):
            print('m1',p)
        def m2(self, p):
            print('m2',p)

    c = C()
#   print('c.m1',dir(c.m1))
#   print('c',dir(c))
#   print('c.m1.__self__',dir(c.m1.__self__))
    
    c.m1('0')
    rm = c.m1
    rm('0')
    rm(c, '0')

#   DlgAgent(
#       ctrls=[('b1', dict(type='button',             cap='Click', x=0, y= 0, w=100, a='lR',
#               call=lambda name,ag:{'ctrls':[('b1',{'cap':'OK',             'w':70})]}         ##!! new w <> a
#              ))
#             ,('b2', dict(type='button', cap='Close', x=0, y=30, w=100,             a='LR',
#               call=lambda name,ag:None)
#              )]
#   ,   form=dict(cap='Two buttons', x=0, y=0, w=100, h=60, h_max=60, resize=True)
#   ,   focused='b1'
#   ).show()

#   BaseDlgAgent(
#       ctrls=[('b1', dict(type='button', cap='Click', x=0, y= 0, w=100, 
#                          call=lambda name,ag:{'ctrls':[('b1',{'cap':'OK', 'w':70})]}))
#             ,('b2', dict(type='button', cap='Close', x=0, y=30, w=100,
#                          call=lambda name,ag:None))]
#   ,   form=dict(cap='Two buttons', x=0, y=0, w=100, h=60)
#   ,   focused='b1'
#   ).show()

#   pass
#   def test_ask_number(ask, def_val):
#       cnts=[dict(        tp='lb',tid='v',l=3 ,w=70,cap=ask)
#            ,dict(cid='v',tp='ed',t=3    ,l=73,w=70)
#            ,dict(cid='!',tp='bt',t=45   ,l=3 ,w=70,cap='OK',props='1')
#            ,dict(cid='-',tp='bt',t=45   ,l=73,w=70,cap='Cancel')]
#       vals={'v':def_val}
#       while True:
#           btn,vals,fid,chds=dlg_wrapper('Example',146,75,cnts,vals,'v')
#           if btn is None or btn=='-': return def_val
#           if not re.match(r'\d+$', vals['v']): continue
#           return vals['v']
#   ask_number('ask_____________', '____smth')
