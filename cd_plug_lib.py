''' Lib for Plugin
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.3.02 2017-05-02'
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
REDUCTS = {'lb'     :'label'
        ,  'ln-lb'  :'linklabel'
        ,  'ed'     :'edit'             # ro_mono_brd
        ,  'ed_pw'  :'edit_pwd'
        ,  'sp-ed'  :'spinedit'         # min_max_inc
        ,  'me'     :'memo'             # ro_mono_brd
        ,  'bt'     :'button'           # def_bt
        ,  'rd'     :'radio'
        ,  'ch'     :'check'
        ,  'ch-bt'  :'checkbutton'
        ,  'ch-b'   :'checkbutton'
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
        tp      = REDUCTS.get(tp, tp)
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
            t       = bs_cnt['t'] + fit_top_by_env(tp, REDUCTS.get(bs_tp, bs_tp))
#           t       = bs_cnt['t'] + top_plus_for_os(tp, REDUCTS.get(bs_tp, bs_tp))
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
        tp      = REDUCTS.get(tp, tp)
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
        focus_tp= REDUCTS.get(focus_tp, focus_tp)
        if focus_tp in ('button'):
            focus_cid   = '' if len(chds)!=1 else chds[0]
    return  act_cid \
        ,   an_vals \
        ,   focus_cid \
        ,   chds
   #def dlg_wrapper

_agent_callbacks = {}    # id_dlg:agent_callback
def _dlg_agent_callback(id_dlg, id_ctl_act, id_event='', info=''):
    pass;                      #log('id_dlg, id_ctl_act, id_event, info={}',(id_dlg, id_ctl_act, id_event, info))
    if id_event.startswith('on_close'):
#       agent_form_acts('save', id_dlg=id_dlg)
        return 
    if id_event!='on_change':
        return 
    global _agent_callbacks
    agent_callback  = _agent_callbacks.get(id_dlg)
    if agent_callback:
        agent_callback(id_dlg, id_ctl_act, id_event, info)

RT_BREAK_AG = (None,None,None)
def  dlg_agent(client_data_updater, fm_prs0, ctrls0, settings0={}):
    """ Wrapper for dlg_proc to show MODAL dlg. """

    def agent_ctrls_updater(id_dlg, cnts, in_vals={}, in_fid=''):
        """ Create/update controls.
            - All controls are created once.
            - Order of controls in cnts must be same on create and on update
            Params
                id_dlg  -           dlg_proc id of form
                cnts    - [{}]      Desc for all controls
                in_vals - {cid:v}   Values for ed-controls.
                                    All cid ref to visibled control
                in_fid  - str       cid to next focuced control
        """
        pass;                  #log('id_dlg={}',(id_dlg))

        if 'checks'=='checks':
            cids    = {cnt['cid'] for cnt in cnts if cnt.get('vis', True) and 
                                                     'cid' in cnt}
            no_tids = {cnt['tid'] for cnt in cnts if cnt.get('vis', True) and 
                                                     'tid' in cnt         and 
                                                     cnt['tid'] not in cids}
            if no_tids:
                raise Exception(f('No cid(s) for tid(s): {}', no_tids))
            no_vids = {cid for cid in in_vals if cid not in cids}
            if no_vids:
                raise Exception(f('No cid(s) for vals: {}', no_vids))

        # Add/Upd controls
        cid2i       = odict([(cnt['cid'],i) for i,cnt in enumerate(cnts) if cnt.get('vis', True) and 'cid' in cnt])
        pass;                  #log('cid2i={}',(cid2i))
        create      = 0==app.dlg_proc(id_dlg, app.DLG_CTL_COUNT)
        for idC,cnt in enumerate(cnts):
            vis     = cnt.get('vis', True)
            tp      = cnt['tp']
            tp      = REDUCTS.get(tp, tp)
            
            # Start preprocessor
            if False:pass
            elif tp=='--' and app.app_api_version()<'1.0.161':
                tp              = 'label'
                cnt['cap']      = '—'*300
                cnt['font_color']=str(rgb_to_int(185,185,185))
                cnt['l']        = cnt.get('l', 0)
                cnt['r']        = cnt.get('r', l+cnt.get('w', 0))       # def: to   DlgRight
            elif tp=='--' and app.app_api_version()>='1.0.161':
                tp              = 'colorpanel'
                cnt['l']        = cnt.get('l', 0)
                cnt['r']        = cnt.get('r', l+cnt.get('w', 5000))    # def: to   DlgRight
                cnt['h']        = 1
                cnt['props']    = f('0,{},0,0',rgb_to_int(185,185,185)) # brdW_fillC_fontC_brdC
            
            if 'sto' in cnt:
                cnt['tab_stop'] = cnt.pop('sto')
            
            if 'props' in cnt:
                pass
            elif tp=='label' and cnt['cap'][0]=='>':
                #   cap='>smth' --> cap='smth', props='1' (r-align)
                cnt['cap']  = cnt['cap'][1:]
                cnt['props']= '1'
            elif tp=='label' and    cnt.get('ralign'):
                cnt['props']=       cnt.get('ralign')
            elif tp=='button' and cnt.get('def_bt') in ('1', True):
                cnt['props']= '1'
            elif tp=='spinedit' and cnt.get('min_max_inc'):
                cnt['props']=       cnt.get('min_max_inc')
            elif tp=='linklabel' and    cnt.get('url'):
                cnt['props']=           cnt.get('url')
            elif tp=='listview' and cnt.get('grid'):
                cnt['props']=       cnt.get('grid')
            elif tp=='tabs' and     cnt.get('at_botttom'):
                cnt['props']=       cnt.get('at_botttom')
            elif tp=='colorpanel' and   cnt.get('brdW_fillC_fontC_brdC'):
                cnt['props']=           cnt.get('brdW_fillC_fontC_brdC')
            elif tp in ('edit', 'memo') and cnt.get('ro_mono_brd'):
                cnt['props']=               cnt.get('ro_mono_brd')
            # Finish preprocessor

            # Add/Reuse
            prC_pre     = {}
            if create:
                cr_idC  = app.dlg_proc(id_dlg, app.DLG_CTL_ADD, tp)
                assert cr_idC==idC
            else:
                prC_pre = app.dlg_proc(id_dlg, app.DLG_CTL_PROP_GET, index=idC)

            # Simple props are copying directly 
            prC_new = {k:v for (k,v) in cnt.items() if k in ['cap','hint'
                                                            ,'props'
                                                            ,'color'
                                                            ,'font_name', 'font_size', 'font_color', 'font'
                                                            ,'act'
                                                            ,'en','vis'
                                                           #,'tag'
                                                            ,'tab_stop' ,'tab_order' 
                                                           #,'sp_l','sp_r','sp_t','sp_b','sp_a'
                                                           #,'a_l','a_r','a_t','a_b'
                                                            ]}
            if 'cid' in cnt:
                prC_new['name'] = cnt['cid'] # cid -> name

            # Position:
            #   t[op] or tid, l[eft] required
            #   w[idth]  >>> r[ight ]=l+w
            #   h[eight] >>> b[ottom]=t+h
            #   b dont need for buttons, edit, labels
            l       = cnt['l']
            t       = cnt.get('t', 0)
            if 'tid' in cnt and cnt['tid'] in cid2i:
#           if 'tid' in cnt and vis:
                # cid for horz-align text
                bs_cnt  = cnts[cid2i[cnt['tid']]]
                bs_tp   = bs_cnt['tp']
                t       = bs_cnt['t'] + fit_top_by_env(tp, REDUCTS.get(bs_tp, bs_tp))
            r       = cnt.get('r', l+cnt.get('w', 0)) 
            b       = cnt.get('b', t+cnt.get('h', 0)) 
            prC_new.update(dict(x=l, y=t, w=r-l)) 
            prC_new.update(dict(h=cnt.get('h')))    if 0!=cnt.get('h', 0) else 0 
            pass;              #log('memo prC_new={}',(prC_new)) if tp=='memo' else 0

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
                prC_new.update(dict(items=items)) 
        
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
                prC_new.update(dict(val=str(in_val)))
            

            if tp in ('button') or cnt.get('act') in ('1', True):
                prC_new['callback'] = f('module={};func=_dlg_agent_callback;', __name__)

            pass;              #log('idC,cid,prC_new={}',(idC, cnt.get('cid'), prC_new))
            if create:
                app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop=prC_new)
#               app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop={'tag':json.dumps(prC_new)})
            elif     vis and not prC_pre.get('vis'):
                # Only to show
                app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop=prC_new)
#               app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop={'tag':json.dumps(prC_new)})
            elif not vis and     prC_pre.get('vis'):
                # Only to hide
                app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop={'vis':False})
#           elif prC_new != json.loads(prC_pre.get('tag', '{}')):
            else:
                # Changed
                app.dlg_proc(id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop=prC_new)

            app.dlg_proc(    id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop={'tag':json.dumps(prC_new)}) # Some attrs are not return by DLG_CTL_PROP_GET
           #for cnt
        
        if in_fid in cid2i:
            pass;              #log('in_fid={}',(in_fid))
            app.dlg_proc(    id_dlg, app.DLG_CTL_FOCUS,    index=cid2i[in_fid])
        return
       #def agent_ctrls_updater
    
    def agent_ctrls_anc(id_dlg, cnts, fm_prs):
        """ Translate attr 'a' to 'a_*','sp_*'
            Values for 'a' are str-mask with signs
                'l' 'L'    fixed distanse ctrl-left     to form-left  or form-right
                't' 'T'    fixed distanse ctrl-top      to form-top   or form-bottom
                'r' 'R'    fixed distanse ctrl-right    to form-left  or form-right
                'b' 'B'    fixed distanse ctrl-bottom   to form-top   or form-bottom
        """
        fm_w    = fm_prs['w']
        fm_h    = fm_prs['h']
        for idC,cnt in enumerate(cnts):
            anc     = cnt.get('a', '')
            if not anc: continue
            prOld   = app.dlg_proc(id_dlg, app.DLG_CTL_PROP_GET, index=idC)
            prNew   = {}
            if '-' in anc:
                # Center by horz
                prNew.update(dict( a_l=(None, '-')
                                  ,a_r=(None, '-')))
            if 'LR' in anc:
                # Both left/right to form right
                prNew.update(dict( a_l=None
                                  ,a_r=(None, ']'), sp_r=fm_w-prOld['x']-prOld['w']))
            if 'lR' in anc:
                # Left to form left. Right to form right.
                prNew.update(dict( a_l=(None, '['), sp_l=     prOld['x']
                                  ,a_r=(None, ']'), sp_r=fm_w-prOld['x']-prOld['w']))
            if '|' in anc:
                # Center by vert
                prNew.update(dict( a_t=(None, '-')
                                  ,a_b=(None, '-')))
            if 'TB' in anc:
                # Both top/bottom to form bottom
                prNew.update(dict( a_t=None
                                  ,a_b=(None, ']'), sp_b=fm_h-prOld['y']-prOld['h']))
            if 'tB' in anc:
                # Top to form top. Bottom to form bottom.
                prNew.update(dict( a_t=(None, '['), sp_t=     prOld['y']
                                  ,a_b=(None, ']'), sp_b=fm_h-prOld['y']-prOld['h']))
            if prNew:
                app.dlg_proc(      id_dlg, app.DLG_CTL_PROP_SET, index=idC, prop=prNew)
       #def agent_ctrls_anc
    
    def agent_form_acts(what, fm_prs=None, id_dlg=None):
        """ Save/Restore pos of form """
        pass;                  #log('what, fm_prs, id_dlg={}',(what, fm_prs, id_dlg))
        CFG_JSON= CdSw.get_setting_dir()+os.sep+'forms data.json'
        stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=odict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  odict()
        def get_form_key(prs):
            fm_cap  = prs['cap']
            return fm_cap if ' (' not in fm_cap else fm_cap[:fm_cap.rindex(' (')]
        if False:pass
        if what=='move' and fm_prs:
            fm_key  = get_form_key(fm_prs)
            if fm_key not in stores:    return fm_prs
            return dict_upd(fm_prs, stores[fm_key])
        if what=='save' and id_dlg:
            dlg_pr  = app.dlg_proc(id_dlg, app.DLG_PROP_GET)
            fm_key  = get_form_key(dlg_pr)
            pass;              #log('{}={}', fm_key,{k:v for k,v in dlg_pr.items() if k in ('x','y','w','h')})
            stores[fm_key]  = {k:v for k,v in dlg_pr.items() if k in ('x','y','w','h')}
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
       #def agent_form_acts
       
    settings_t  = settings0
    idDlg       = app.dlg_proc(0, app.DLG_CREATE)
    pass;                      #log('idDlg={}',(idDlg))
    agent_ctrls_updater(idDlg, ctrls0, settings0.get('values'), settings0.get('focused'))
    if fm_prs0.get('resize', False):
        agent_ctrls_anc(idDlg, ctrls0, fm_prs0)
        fm_prs0['w_min']    = fm_prs0.get('w_min', fm_prs0['w'])
        fm_prs0['h_min']    = fm_prs0.get('h_min', fm_prs0['h'])
    fm_prs0     = agent_form_acts('move', fm_prs=fm_prs0)
    app.dlg_proc(       idDlg, app.DLG_PROP_SET, prop=dict_upd(fm_prs0, dict(
                                                               callback = f('module={};func=_dlg_agent_callback;', __name__)
                                                              ,events   = 'on_change'
                                                              ,topmost  = True
                                                              )))
    pass;                       gen_repro_code(idDlg, tempfile.gettempdir()+os.sep+'repro_dlg_proc.py')     if F else None
    
    def agent_scaner(id_dlg, id_ctl_act, in_vals_p=None):
        """ Collect values of controls
        """
        pass;                  #log('id_dlg, id_ctl_act={}',(id_dlg, id_ctl_act))
        pass;                  #log('cnts_p={}',(cnts_p))
        in_vals_p   = in_vals_p if in_vals_p else {}
        pass;                  #log('in_vals_p={}',(in_vals_p))
        
        dlg_pr      = app.dlg_proc(id_dlg, app.DLG_PROP_GET)
        pass;                  #log('dlg_pr={}',(dlg_pr))
        
        focus_idC   = dlg_pr.get('focused', -1)
        focus_prC   = app.dlg_proc(id_dlg, app.DLG_CTL_PROP_GET, index=focus_idC) if -1!=focus_idC else {}
        focus_cid   = focus_prC.get('name', '')
        pass;                  #log('focus_cid={})',(focus_cid))
        act_prC     = app.dlg_proc(id_dlg, app.DLG_CTL_PROP_GET, index=id_ctl_act)
        act_cid     = act_prC['name']

        # Parse output values
        cid2i       = {}
        cid2tp      = {}
        an_vals     = {}
        for idC in range(app.dlg_proc(id_dlg, app.DLG_CTL_COUNT)):
            prC     = app.dlg_proc(id_dlg, app.DLG_CTL_PROP_GET, index=idC)
            cid     = prC['name']
            if not cid or cid not in in_vals_p:
                continue#for idC
            cid2i[cid]  = idC
            cid2tp[cid] = prC['type']
            an_vals[cid]= prC['val']
        pass;                  #log('cid2i={}',(cid2i))
        pass;                  #log('an_vals={}',(an_vals))
    
        for cid in an_vals:
            tp      = cid2tp[cid]
            in_val  = in_vals_p[cid]
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
        chds    = [cid for cid in in_vals_p if in_vals_p[cid]!=an_vals[cid]]

        pass;                  #log('act_cid,focus_cid,chds={})',(act_cid,focus_cid,chds))
        pass;                  #log('an_vals={})',(an_vals))
        pass;                  #return None, None, None, None   # btn_cid, {cid:v}, focus_cid, [cid]
        return  act_cid \
            ,   an_vals \
            ,   focus_cid \
            ,   chds
       #def agent_scaner

    def agent_loop(id_dlg, id_ctl_act, id_event='', info=''):
        nonlocal settings_t
        pass;                  #log('id_dlg, id_ctl_act, id_event={}',(id_dlg, id_ctl_act, id_event))
        pass;                  #log('cnts_t={}',(cnts_t))
        pass;                  #log('settings_t={}',(settings_t))
        
        fm_aid, fm_vals,\
        fm_fid, fm_chds = agent_scaner(id_dlg, id_ctl_act, settings_t.get('values'))
        if not fm_aid:
            pass;               log('Error',)
            app.dlg_proc(   id_dlg, app.DLG_HIDE)
            return

        fm_prs,     \
        ctrls,      \
        settings    = client_data_updater(fm_aid, fm_vals, fm_fid, fm_chds)
        settings_t  = settings
        if fm_prs is None:
            pass;              #log('break agent_loop',)
            app.dlg_proc(   id_dlg, app.DLG_HIDE)
            return
        pass;                  #log('next agent_loop',)
        agent_ctrls_updater(id_dlg, ctrls, settings.get('values'),  settings.get('focused'))
        app.dlg_proc(       id_dlg, app.DLG_PROP_SET, prop=fm_prs)  if fm_prs else None
       #def agent_loop

    global _agent_callbacks
    ed_caller   = ed
    _agent_callbacks[       idDlg] = agent_loop
    app.dlg_proc(           idDlg, app.DLG_SHOW_MODAL)
    # Finish
    _agent_callbacks.pop(   idDlg, None)
    agent_form_acts('save', id_dlg=idDlg)
    app.dlg_proc(           idDlg, app.DLG_FREE)
    ed_caller.focus()
   #def dlg_agent

#pass;                           from cudatext import *
def dlg_valign_consts():
    pass;                      #log('ok')
    UP,DN   = '↑↑','↓↓'
    DLG_W,  \
    DLG_H   = 335, 280
    fits    = dict(
               _sp1=fit_top_by_env('check')
              ,_sp2=fit_top_by_env('edit')
              ,_sp3=fit_top_by_env('button')
              ,_sp4=fit_top_by_env('combo_ro')
              ,_sp5=fit_top_by_env('combo')
              ,_sp6=fit_top_by_env('checkbutton')
              ,_sp7=fit_top_by_env('linklabel')
              ,_sp8=fit_top_by_env('spinedit')
              )
    hints   = dict(
               _sp1=f('{} check', fits['_sp1'])
              ,_sp2=f('{} edit', fits['_sp2'])
              ,_sp3=f('{} button', fits['_sp3'])
              ,_sp4=f('{} combo_ro', fits['_sp4'])
              ,_sp5=f('{} combo', fits['_sp5'])
              ,_sp6=f('{} checkbutton', fits['_sp6'])
              ,_sp7=f('{} linklabel', fits['_sp7'])
              ,_sp8=f('{} spinedit', fits['_sp8'])
              )
    vals    = dict(
               ch1 =False
              ,ed2 ='=======?'
              ,cbo4=0
              ,cb5 ='=======?'
              ,chb6=0
              ,sp8 =4444444
              )
    focused = '-'
    def get_cnts(): return \
            [dict(cid='lb1' ,tp='lb'    ,t= 10              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='ch1' ,tp='ch'    ,t= 10+fits['_sp1'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp1'] )
            ,dict(cid='up1' ,tp='bt'    ,t= 10-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn1' ,tp='bt'    ,t= 10-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb2' ,tp='lb'    ,t= 40              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='ed2' ,tp='ed'    ,t= 40+fits['_sp2'] ,l=115  ,w=100                          ,hint=hints['_sp2'] )
            ,dict(cid='up2' ,tp='bt'    ,t= 40-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn2' ,tp='bt'    ,t= 40-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb3' ,tp='lb'    ,t= 70              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='bt3' ,tp='bt'    ,t= 70+fits['_sp3'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp3'] )
            ,dict(cid='up3' ,tp='bt'    ,t= 70-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn3' ,tp='bt'    ,t= 70-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb4' ,tp='lb'    ,t=100              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='cbo4',tp='cb-ro' ,t=100+fits['_sp4'] ,l=115  ,w=100  ,items=['=======?']     ,hint=hints['_sp4'] )
            ,dict(cid='up4' ,tp='bt'    ,t=100-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn4' ,tp='bt'    ,t=100-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb5' ,tp='lb'    ,t=130              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='cb5' ,tp='cb'    ,t=130+fits['_sp5'] ,l=115  ,w=100  ,items=['=======?']     ,hint=hints['_sp5'] )
            ,dict(cid='up5' ,tp='bt'    ,t=130-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn5' ,tp='bt'    ,t=130-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb6' ,tp='lb'    ,t=160              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='chb6',tp='ch-bt' ,t=160+fits['_sp6'] ,l=115  ,w=100  ,cap='=======?'         ,hint=hints['_sp6'] )
            ,dict(cid='up6' ,tp='bt'    ,t=160-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn6' ,tp='bt'    ,t=160-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb7' ,tp='lb'    ,t=190              ,l=  5  ,w=100  ,cap='==============='                      )
            ,dict(cid='chb7',tp='ln-lb' ,t=190+fits['_sp7'] ,l=115  ,w=100  ,cap='=======?'         ,props=hints['_sp7'])
            ,dict(cid='up7' ,tp='bt'    ,t=190-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn7' ,tp='bt'    ,t=190-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='lb8' ,tp='lb'    ,t=220              ,l=  5  ,w=100  ,cap='4444444444444444'                     )
            ,dict(cid='sp8' ,tp='sp-ed' ,t=220+fits['_sp8'] ,l=115  ,w=100  ,props='0,4444444,1'    ,hint=hints['_sp8'] )
            ,dict(cid='up8' ,tp='bt'    ,t=220-3            ,l=230  ,w=50   ,cap=UP                                     )
            ,dict(cid='dn8' ,tp='bt'    ,t=220-3            ,l=280  ,w=50   ,cap=DN                                     )
                
            ,dict(cid='save',tp='bt'    ,t=DLG_H-30         ,l=115  ,w=100  ,cap=_('&Save')
                                                                                ,hint=_('Apply the fittings to controls of all dialogs.'
                                                                                        '\rCtrl+Click  - Show data to mail report.'))
            ,dict(cid='-'   ,tp='bt'    ,t=DLG_H-30         ,l=230  ,w=100  ,cap=_('Cancel')        )
            ]
       #def get_cnts
    def dlg_loop(aid, vals, fid, chds):
        pass;                  #log('aid={}',(aid))
        
        pass;                  #return None,None,None,None,None#while True
        
#       if aid is None or aid=='-':
        if aid=='-':
            return RT_BREAK_AG#while True
        scam        = app.app_proc(app.PROC_GET_KEYSTATE, '') if app.app_api_version()>='1.0.143' else ''
        aid_m       = scam + '/' + aid if scam and scam!='a' else aid   # smth == a/smth
        focused = chds[0] if 1==len(chds) else fid
        
        if aid[:2]=='up' or aid[:2]=='dn':
            pos = aid[2]
            fits['_sp'+pos] = fits['_sp'+pos] + (-1 if aid[:2]=='up' else 1)
            
        if aid_m=='save':
            ctrls   = ['check'
                      ,'edit'
                      ,'button'   
                      ,'combo_ro' 
                      ,'combo'    
                      ,'checkbutton'
                      ,'linklabel'
                      ,'spinedit'
                      ]
            for ic, nc in enumerate(ctrls):
                fit = fits['_sp'+str(1+ic)]
                if fit==fit_top_by_env(nc): continue#for ic, nc
                apx.set_opt('dlg_wrapper_fit_va_for_'+nc, fit)
               #for ic, nc
            fit_top_by_env__clear()
            return RT_BREAK_AG#break#while
            
        if aid_m=='c/save': # Report
            rpt = 'env:'+get_desktop_environment()
            rpt+= c13+'check:'      +str(fits['_sp1'])
            rpt+= c13+'edit:'       +str(fits['_sp2'])
            rpt+= c13+'button:'     +str(fits['_sp3'])
            rpt+= c13+'combo_ro:'   +str(fits['_sp4'])
            rpt+= c13+'combo:'      +str(fits['_sp5'])
            rpt+= c13+'checkbutton:'+str(fits['_sp6'])
            rpt+= c13+'linklabel:'  +str(fits['_sp7'])
            rpt+= c13+'spinedit:'   +str(fits['_sp8'])
            aid_r, *_t = dlg_wrapper(_('Report'), 230,310,
                 [dict(cid='rprt',tp='me'    ,t=5   ,l=5 ,h=200 ,w=220)
                 ,dict(           tp='lb'    ,t=215 ,l=5        ,w=220  ,cap=_('Send the report to the address'))
                 ,dict(cid='mail',tp='ed'    ,t=235 ,l=5        ,w=220)
                 ,dict(           tp='lb'    ,t=265 ,l=5        ,w=150  ,cap=_('or post it on'))
                 ,dict(cid='gith',tp='ln-lb' ,t=265 ,l=155      ,w=70   ,cap='GitHub',props='https://github.com/kvichans/cuda_fit_v_alignments/issues')
                 ,dict(cid='-'   ,tp='bt'    ,t=280 ,l=205-80   ,w=80   ,cap=_('Close'))
                 ], dict(rprt=rpt
                        ,mail='kvichans@mail.ru'), focus_cid='rprt')
            pass;               log('aid_r={}',(aid_r))
        return dict(fm_cap=_('Adjust vertical alignments'), fm_w=DLG_W, fm_h=DLG_H, fm_ctrls=get_cnts()) \
             , dict(values=vals, focused=focused)
       #def dlg_loop
    dlg_agent( dlg_loop
             , dict(cap=_('Adjust vertical alignments'), w=DLG_W, h=DLG_H) \
             , get_cnts()
             , dict(values=vals, focused=focused))
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

_   = get_translation(__file__) # I18N

def dict_upd(d1, d2):
    d   = d1.copy()
    d.update(d2)
    return d
   #def dict_upd
   
if __name__ == '__main__' :     # Tests
    pass
    def test_ask_number(ask, def_val):
        cnts=[dict(        tp='lb',tid='v',l=3 ,w=70,cap=ask)
             ,dict(cid='v',tp='ed',t=3    ,l=73,w=70)
             ,dict(cid='!',tp='bt',t=45   ,l=3 ,w=70,cap='OK',props='1')
             ,dict(cid='-',tp='bt',t=45   ,l=73,w=70,cap='Cancel')]
        vals={'v':def_val}
        while True:
            btn,vals,fid,chds=dlg_wrapper('Example',146,75,cnts,vals,'v')
            if btn is None or btn=='-': return def_val
            if not re.match(r'\d+$', vals['v']): continue
            return vals['v']
    ask_number('ask_____________', '____smth')
