''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.1.1 2016-02-25'
ToDo: (see end of file)
'''

import  re, os, sys, glob, json, collections
import  cudatext        as app
from    cudatext    import ed
import  cudatext_cmd    as cmds
import  cudax_lib       as apx
from    cudax_lib   import log

OrdDict = collections.OrderedDict
#FROM_API_VERSION= '1.0.119'

pass;                           LOG = (-2==-2)  # Do or dont logging.

def F(s, *args, **kwargs):return s.format(*args, **kwargs)
C1      = chr(1)
C2      = chr(2)
POS_FMT = 'pos={l},{t},{r},{b}'.format
POS_LTR = 'pos={l},{t},{r},0'.format
def POS_TLW(t=0,l=0,w=0):   return POS_LTR(l=l, t=t, r=l+w)
def cust_it(tp, **kw):
    tp      = {'check-bt':'checkbutton'}.get(tp, tp)
    lst     = ['type='+tp]
    lst    += [POS_TLW(t=kw['t'],l=kw['l'],w=kw['w'])
                if 'w'     in kw else
               POS_LTR(l=kw['l'],t=kw['t'],r=kw['r'])
                if 'b' not in kw else
               POS_FMT(l=kw['l'],t=kw['t'],r=kw['r'],b=kw['b'])
              ]
    for k in ['cap', 'hint', 'props', 'en']:
        if k in kw:
            lst += [k+'='+str(kw[k])]
    if 'items' in kw:
        lst+= ['items='+'\t'.join(kw['items'])]
    if 'val' in kw:
        val = kw['val']
        val = '\t'.join(val) if isinstance(val, list) else val
        lst+= ['val='+str(val)]
    pass;                      #LOG and log('lst={}',lst)
    return C1.join(lst)
   #def cust_it
GAP     = 5
def top_plus_for_os(what_control, base_control='edit'):
    ''' Addition for what_top to align text with base.
        Params
            what_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
            base_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
    '''
    if what_control==base_control:
        return 0
    env = sys.platform
    if base_control=='edit': 
        if env=='win32':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    3
                            ,what_control=='button',  -1
                            ,what_control=='combo_ro',-1
                            ,what_control=='combo',    0
                            ,True,                     0)
        if env=='linux':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    5
                            ,what_control=='button',   1
                            ,what_control=='combo_ro', 0
                            ,what_control=='combo',   -1
                            ,True,                     0)
        if env=='darwin':
            return apx.icase(what_control=='check',    2
                            ,what_control=='label',    3
                            ,what_control=='button',   0
                            ,what_control=='combo_ro', 1
                            ,what_control=='combo',    0
                            ,True,                     0)
        return 0
       #if base_control=='edit'
    return top_plus_for_os(what_control, 'edit') - top_plus_for_os(base_control, 'edit')
   #def top_plus_for_os

class Command:
    def show_dlg(self):
        self.show_dlg_( what='smth', opts={
            'repl':'other',
            'incl':'d1?3.* d3?1.*',
            'excl':'c*.*',
            'fold':'root',
            'dept':'2',
#           'case':'1',
#           'word':'1',
#           'reex':'1',
        })
    def show_dlg_(self, what='', opts={}):
        max_hist= apx.get_opt('ui_max_history_edits', 20)
        cfg_json= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_find_in_files.json'
        stores  = apx._json_loads(open(cfg_json).read(), object_pairs_hook=OrdDict)    if os.path.exists(cfg_json) else    OrdDict()
        mask_h  = 'Space separated masks.\rQuote as "m a s k" if space is need.\rUse ? for any character and * for any fragment'
        incl_h  = mask_h+'\rEmpty equal *.*'
        reex_h  = 'Reg.ex'
        case_h  = 'Case sensitive'
        word_h  = 'Whole words'
        brow_h  = 'Select folder'
        curr_h  = 'Use folder of current file'
        more_h  = 'Show/Hide advance options'
        adju_h  = 'Change dialog layout'
        coun_h  = 'Only count matches in files.\rAs Find with Collect:"Match counts".'
        pset_h  = 'Save options for future.\rRestore saved options'
        dept_l  = ['All', 'In folder only', '1 level', '2 level', '3 level', '4 level', '5 level']
        join_c  = 'Appen&d to results'
        toed_c  = 'Show results in &editor'
        cllc_l  = ['All matches', 'Match counts', 'Filenames']
        skip_l  = [' ', 'Hidden', 'Binary', 'Hidden, Binary']
        sort_l  = [' ', 'By date, from newest', 'By date, from oldest']
    
        it0     = cust_it(tp='label',t=0,l=0,w=0,cap='')
        DLG_W0, \
        DLG_H0  = (700, 315)
        TXT_W   = 380
        t_lb4cm = top_plus_for_os('label', 'combo')
        t_ch4cm = top_plus_for_os('check', 'combo')
        t_bt4cm = top_plus_for_os('button', 'combo')
        t_lb4ed = top_plus_for_os('label', 'edit')
        t_lb4bt = top_plus_for_os('label', 'button')
        
        focused = 10
        what_s  = what
        repl_s  = opts.get('repl', '')
        reex01  = opts.get('reex', stores.get('reex', '0'))
        case01  = opts.get('case', stores.get('case', '0'))
        word01  = opts.get('word', stores.get('word', '0'))
        incl_s  = opts.get('incl', stores.get('incl',  ''))
        excl_s  = opts.get('excl', stores.get('excl',  ''))
        fold_s  = opts.get('fold', stores.get('fold',  ''))
        dept_s  = opts.get('dept', stores.get('dept', '0'))
        cllc_s  = opts.get('cllc', stores.get('cllc', '0'))
        join_s  = opts.get('join', stores.get('join', '0'))
        toed_s  = opts.get('toed', stores.get('toed', '0'))
        skip_s  = opts.get('skip', stores.get('skip', '0'))
        sort_s  = opts.get('sort', stores.get('sort', '0'))
        frst_s  = opts.get('frst', stores.get('frst', '0'))
        while True:
            what_l  = stores.get('what', [])
            incl_l  = stores.get('incl', [])
            excl_l  = stores.get('excl', [])
            fold_l  = stores.get('fold', [])
            repl_l  = stores.get('repl', [])
        
            wo_excl = stores.get('wo_excl', True)
            wo_repl = stores.get('wo_repl', True)
            wo_adva = stores.get('wo_adva', True)
            c_more  = 'Show "Ad&v"' if wo_adva else 'Hide "Ad&v"'
            gap1    = (GAP- 25 if wo_excl else GAP)
            gap2    = (GAP- 25 if wo_repl else GAP)+gap1
            gap3    = (GAP-115 if wo_adva else GAP)+gap2
            DLG_W,\
            DLG_H   = (DLG_W0, DLG_H0+gap3)
            lbl_l   = GAP+35*3+GAP
            cmb_l   = lbl_l+100
            tl2_l   = lbl_l+200
            tbn_l   = cmb_l+TXT_W+GAP
            ans = app.dlg_custom('Find in Files', DLG_W, DLG_H, '\n'.join([]
+[cust_it(tp='button'   ,t=GAP+t_bt4cm      ,l=tbn_l    ,r=DLG_W-GAP    ,cap='Find' ,props='1'                      )] #  0 find #default
+[cust_it(tp='button'   ,t=GAP+25+t_bt4cm   ,l=tbn_l    ,r=DLG_W-GAP    ,cap='Coun&t'       ,hint=coun_h            )] #  1 count   &t
+[cust_it(tp='button'   ,t=DLG_H-GAP-23     ,l=GAP      ,w=35*3         ,cap=c_more         ,hint=more_h            )] #  2 more    &v
+[cust_it(tp='button'   ,t=DLG_H-GAP-23     ,l=GAP*2+35*3,w=35*3        ,cap='Ad&just...'   ,hint=adju_h            )] #  3 custom  &j
+[cust_it(tp='button'   ,t=DLG_H-GAP-23-25  ,l=tbn_l    ,r=DLG_W-GAP    ,cap='Pre&sets...'  ,hint=pset_h            )] #  4 preset  &s
+[cust_it(tp='button'   ,t=DLG_H-GAP-23     ,l=tbn_l    ,r=DLG_W-GAP    ,cap='Close'                                )] #  5 cancel

+[cust_it(tp='check-bt' ,t=GAP+t_bt4cm      ,l=GAP+35*0 ,w=35           ,cap='&.*'          ,hint=reex_h,val=reex01 )] #  6         &.
+[cust_it(tp='check-bt' ,t=GAP+t_bt4cm      ,l=GAP+35*1 ,w=35           ,cap='&aA'          ,hint=case_h,val=case01 )] #  7         &a
+[cust_it(tp='check-bt' ,t=GAP+t_bt4cm      ,l=GAP+35*2 ,w=35           ,cap='"&w"'         ,hint=word_h,val=word01 )] #  8         &w
+[cust_it(tp='label'    ,t=GAP+t_lb4cm      ,l=lbl_l    ,r=cmb_l        ,cap='&Find:'                               )] #  9         &f
+[cust_it(tp='combo'    ,t=GAP              ,l=cmb_l    ,w=TXT_W        ,items=what_l                   ,val=what_s )] # 10
                                                                                                                    
+[cust_it(tp='label'    ,t=GAP+25+t_lb4cm   ,l=lbl_l    ,r=cmb_l        ,cap='&In files:'   ,hint=incl_h            )] # 11         &i
+[cust_it(tp='combo'    ,t=GAP+25           ,l=cmb_l    ,w=TXT_W        ,items=incl_l                   ,val=incl_s )] # 12
            +([it0]*2 if wo_excl else []                                                                                 
+[cust_it(tp='label'    ,t=GAP+50+t_lb4cm   ,l=lbl_l    ,r=cmb_l        ,cap='Not in files:',hint=mask_h            )] # 13
+[cust_it(tp='combo'    ,t=GAP+50           ,l=cmb_l    ,w=TXT_W        ,items=excl_l                   ,val=excl_s )] # 14
            )                                                                                                       
+[cust_it(tp='button'   ,t=gap1+75+t_bt4cm  ,l=GAP      ,w=35*3         ,cap='&Current folder',hint=curr_h          )] # 15 curr    &c
+[cust_it(tp='label'    ,t=gap1+75+t_lb4cm  ,l=lbl_l    ,r=cmb_l        ,cap='I&n folder:'                          )] # 16         &n
+[cust_it(tp='combo'    ,t=gap1+75          ,l=cmb_l    ,w=TXT_W        ,items=fold_l                   ,val=fold_s )] # 17 
+[cust_it(tp='button'   ,t=gap1+75+t_bt4cm  ,l=tbn_l    ,r=DLG_W-GAP    ,cap='&Browse...'   ,hint=brow_h            )] # 18 brow    &b
+[cust_it(tp='label'    ,t=gap1+100+t_lb4cm ,l=cmb_l    ,w=100          ,cap='In s&ubfolders:'                      )] # 19         &u
+[cust_it(tp='combo_ro' ,t=gap1+100         ,l=tl2_l    ,w=120          ,items=dept_l                   ,val=dept_s )] # 20 
            +([it0]*3 if wo_repl else []                                                                                 
+[cust_it(tp='label'    ,t=gap1+125+t_lb4cm ,l=lbl_l    ,r=cmb_l        ,cap='&Replace with:'                       )] # 21         &r
+[cust_it(tp='combo'    ,t=gap1+125         ,l=cmb_l    ,w=TXT_W        ,items=repl_l                   ,val=repl_s )] # 22
+[cust_it(tp='button'   ,t=gap1+125+t_bt4cm ,l=tbn_l    ,r=DLG_W-GAP    ,cap='Re&place'                             )] # 23 replace &p
            )                                                                                                       
            +([it0]*12 if wo_adva else  []                                                                                 
+[cust_it(tp='label'    ,t=gap2+160         ,l=GAP      ,w=150          ,cap='== Adv. report options =='            )] # 24
+[cust_it(tp='label'    ,t=gap2+180+t_lb4cm ,l=GAP      ,w=100          ,cap='Co&llect:'                            )] # 25         &l
+[cust_it(tp='combo_ro' ,t=gap2+180         ,l=GAP+100  ,r=cmb_l        ,items=cllc_l                   ,val=cllc_s )] # 26 
+[cust_it(tp='check'    ,t=gap2+205         ,l=GAP      ,w=150          ,cap=join_c                     ,val=join_s )] # 27         &d
+[cust_it(tp='check'    ,t=gap2+230         ,l=GAP      ,w=150          ,cap=toed_c                     ,val=toed_s )] # 28         &e

+[cust_it(tp='label'    ,t=gap2+160         ,l=tl2_l    ,w=150          ,cap='== Adv. find options =='              )] # 29
+[cust_it(tp='label'    ,t=gap2+180+t_lb4cm ,l=tl2_l    ,w=100          ,cap='S&kip files:'                         )] # 30         &k
+[cust_it(tp='combo_ro' ,t=gap2+180         ,l=tl2_l+100,w=150          ,items=skip_l                   ,val=skip_s )] # 31 
+[cust_it(tp='label'    ,t=gap2+205+t_lb4cm ,l=tl2_l    ,w=100          ,cap='S&ort file list:'                     )] # 32         &o
+[cust_it(tp='combo_ro' ,t=gap2+205         ,l=tl2_l+100,w=150          ,items=sort_l                   ,val=sort_s )] # 33 
+[cust_it(tp='label'    ,t=gap2+230+t_lb4ed ,l=tl2_l    ,w=100          ,cap='Firsts (&0=all):'                     )] # 34         &0
+[cust_it(tp='edit'     ,t=gap2+230         ,l=tl2_l+100,w=150                                          ,val=frst_s )] # 35 
            )                                                                                                       
+[cust_it(tp='button'   ,t=DLG_H-GAP-23-50  ,l=tbn_l    ,r=DLG_W-GAP    ,cap='&Help...'                             )] # 36 help    &h
              ), focused)    # start focus - what_s
            if ans is None: return
            act_i,vals= ans
            vals    = vals.splitlines()
            act_s   = apx.icase(False,''
                       ,act_i==  0  ,'find'
                       ,act_i==  1  ,'count'
                       ,act_i==  2  ,'more'
                       ,act_i==  3  ,'custom'
                       ,act_i==  4  ,'preset'
                       ,act_i==  5  ,'cancel'
                       ,act_i== 15  ,'curr-fold'
                       ,act_i== 18  ,'brow-fold'
                       ,act_i== 23  ,'replace'
                       ,act_i== 36  ,'help'
                       ,True                , '???')
            pass;               LOG and log('act_i,act_s={}',(act_i,act_s))
            if act_s=='cancel':return
            focused     = 10
            reex01      = vals[  6]
            case01      = vals[  7]
            word01      = vals[  8]
            what_s      = vals[ 10]
            incl_s      = vals[ 12]
            if not wo_excl:     
                excl_s  = vals[ 14]
            fold_s      = vals[ 17]
            dept_s      = vals[ 20]
            if not wo_repl:     
                repl_s  = vals[ 22]
            if not wo_adva:     
                cllc_s  = vals[ 26]
                join_s  = vals[ 27]
                toed_s  = vals[ 28]
                skip_s  = vals[ 31]
                sort_s  = vals[ 33]
                frst_s  = vals[ 35]
            pass;              #LOG and log('what_s,incl_s,fold_s={}',(what_s,incl_s,fold_s))
            
            stores['reex']  = reex01
            stores['case']  = case01
            stores['word']  = word01
            stores['what']  = add_to_history(what_s, stores.get('what', []), max_hist)
            stores['incl']  = add_to_history(incl_s, stores.get('incl', []), max_hist)
            stores['excl']  = add_to_history(excl_s, stores.get('excl', []), max_hist)
            stores['fold']  = add_to_history(fold_s, stores.get('fold', []), max_hist)
            stores['dept']  = dept_s
            stores['repl']  = add_to_history(repl_s, stores.get('repl', []), max_hist)
            stores['cllc']  = cllc_s
            stores['join']  = join_s
            stores['toed']  = toed_s
            stores['skip']  = skip_s
            stores['sort']  = sort_s
            stores['frst']  = frst_s
            open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            
            if act_s=='help':
                show_help()
                continue#while
            if act_s=='preset':
                pset_l  = stores.setdefault('pset', [])
                dlg_list= [F('Restore: {nm}\t[{il}]In files, [{fo}]In folder, [{aa}].*aAw, [{fn}]Adv. find, [{rp}]Adv. report'
                            ,nm=ps['name']
                            ,il=ps.get('_il_',' ')
                            ,fo=ps.get('_fo_',' ')
                            ,aa=ps.get('_aa_',' ')
                            ,fn=ps.get('_fn_',' ')
                            ,rp=ps.get('_rp_',' ')
                            ) 
                            for ps in pset_l] \
                        + ['Save preset...']
                ps_ind  = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(dlg_list))
                if ps_ind is None:  continue#while
                if ps_ind<len(pset_l):
                    # Restore
                    ps  = pset_l[ps_ind]
                    incl_s = ps.get('incl', incl_s)
                    excl_s = ps.get('excl', excl_s)
                    fold_s = ps.get('fold', fold_s)
                    dept_s = ps.get('dept', dept_s)
                    reex01 = ps.get('reex', reex01)
                    case01 = ps.get('case', case01)
                    word01 = ps.get('word', word01)
                    cllc_s = ps.get('cllc', cllc_s)
                    join_s = ps.get('join', join_s)
                    toed_s = ps.get('toed', toed_s)
                    skip_s = ps.get('skip', skip_s)
                    sort_s = ps.get('sort', sort_s)
                    frst_s = ps.get('frst', frst_s)
                    app.msg_status('Restore preset: '+ps['name'])
                else:
                    custs   = app.dlg_input_ex(6, 'Save preset'
                        , 'Preset name'                                             , F('Preset #{}', 1+len(pset_l))
                        , 'Save "In files"/"Not in files" (0/1)'                    , '1'   # 1
                        , 'Save "In folder"/"Subfolders" (0/1)'                     , '1'   # 2
                        , 'Save ".*"/"aA"/"w" (0/1)'                                , '1'   # 3
                        , 'Save (Adv. find) "Skip"/"Sort"/"Firsts" (0/1)'           , '1'   # 4
                        , 'Save (Adv. report) "Collect"/"Append"/"In editor" (0/1)' , '1'   # 5
                        )
                    if not custs or not custs[0] :   continue#while
                    ps      = OrdDict([('name',custs[0])])
                    if custs[1]=='1':
                        ps['_il_']  = 'x'
                        ps['incl']  = incl_s
                        ps['excl']  = excl_s
                    if custs[2]=='1':
                        ps['_fo_']  = 'x'
                        ps['fold']  = fold_s
                        ps['dept']  = dept_s
                    if custs[3]=='1':
                        ps['_aa_']  = 'x'
                        ps['reex']  = reex01
                        ps['case']  = case01
                        ps['word']  = word01
                    if custs[4]=='1':
                        ps['_fn_']  = 'x'
                        ps['skip']  = skip_s
                        ps['sort']  = sort_s
                        ps['frst']  = frst_s
                    if custs[5]=='1':
                        ps['_rp_']  = 'x'
                        ps['cllc']  = cllc_s
                        ps['join']  = join_s
                        ps['toed']  = toed_s
                        pass
                    pset_l += [ps]
                    open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                    app.msg_status('Save new preset')
                
            if act_s=='more':
                stores['wo_adva']       = not stores.get('wo_adva', True)
                open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                continue#while
            if act_s=='custom':
                custs   = app.dlg_input_ex(2, 'Adjust dialog'
                    , 'Show Replace (0/1)'                  , str(0 if stores.get('wo_repl', True) else 1)
                    , 'Show Exclude masks (0/1)'            , str(0 if stores.get('wo_excl', True) else 1)
                    )
                if custs is not None:
                    stores['wo_repl']   = (custs[0]=='0')
                    stores['wo_excl']   = (custs[1]=='0')
                    open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                continue#while

            open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            if False:pass
            elif act_s=='brow-fold':
                path    = app.dlg_dir(fold_s)
                fold_s  = path if path else fold_s
            elif act_s=='curr-fold':
                path    = ed.get_filename()
                fold_s  = os.path.dirname(path) if path else fold_s

            elif act_s=='replace':
                pass
            elif act_s in ('count', 'find'):
                if not what_s:
                    app.msg_box('Fill "Find"', app.MB_OK) 
                    continue#while
                if not fold_s or not os.path.isdir(fold_s):
                    app.msg_box('Correct "In folder"', app.MB_OK) 
                    focused     = 17
                    continue#while
                find_in_files(what_s, fold_s 
                    ,what_saves =apx.icase(act_s=='count'   ,'-f-c-' 
                                          ,cllc_s=='0'      ,'-f-r-p-t-' 
                                          ,cllc_s=='1'      ,'-f-c-' 
                                          ,cllc_s=='2'      ,'-f-')       # ['All matches', 'Match counts', 'Filenames']
                    ,as_re      =reex01=='1'
                    ,case       =case01=='1'
                    ,word       =word01=='1'
                    ,file_mask  =incl_s
                    ,file_exmask=excl_s
                    ,depth      =int(dept_s)-1          # ['All', 'In folder only', '1 level', ...]
                    ,skips_hidn =skip_s in ('1', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                    ,skips_binr =skip_s in ('2', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                    ,sort_type  =apx.icase(sort_s=='0','' 
                                          ,sort_s=='1','date,desc' 
                                          ,sort_s=='2','date,asc' ,'') # [' ', 'By date, from newest', 'By date, from oldest']
                    ,only_frst  =int(frst_s)
                    )
           #while
#       return (res, data)

#       open(cfg_json, 'w').write(json.dumps(stores, indent=4))
       #def show_dlg
   #class Commandc

def show_help():
    l           = '\n'
    RE_DOC_REF  = 'https://docs.python.org/3/library/re.html'
    text        =   'RegExp tips:' \
                +l+r'- Format for found groups in Replace: \1'

    text        = text.replace('\t', chr(2)).replace('\n', '\t')
    DW, DH      = 600, 400
    t_lb4bt     = top_plus_for_os('label', 'button')
    app.dlg_custom('Help for "Find in files"', GAP+DW+GAP,GAP+DH+GAP, '\n'.join([]
+[cust_it(tp='memo'     ,t=GAP              ,l=GAP      ,r=GAP+DW,b=GAP+DH-28,val=text                  ,props='1,1,1'   )]  #  0  # ro,mono,border
+[cust_it(tp='linklabel',t=GAP+DH-23+t_lb4bt,l=GAP      ,w=180               ,cap='RegExp on python.org',props=RE_DOC_REF)]  #  1
+[cust_it(tp='button'   ,t=GAP+DH-23        ,l=GAP+DW-80,w=80                ,cap='Close'                                )]  #  2 cancel
      ), 2)    # start focus - what_s
   #def show_help

def add_to_history(val, lst, max_len, uncase=True):
    """ Add/Move val to list head.
    """
    if not val:
        return lst
    pass;                      #LOG and log('val, lst={}',(val, lst))
    lst_u = [ s.upper() for s in lst] if uncase else lst
    val_u = val.upper()               if uncase else val
    if val_u in lst_u:
        if 0 == lst_u.index(val_u):   return lst
        del lst[lst_u.index(val_u)]
    lst.insert(0, val)
    pass;                      #LOG and log('lst={}',lst)
    if len(lst)>max_len:
        del lst[max_len:]
    pass;                      #LOG and log('lst={}',lst)
    return lst
   #def add_to_history

def find_in_files(what_s, fold_s 
        ,what_saves ='-f-r-p-t-' # f=file, r=line, p=col, t=fragment
        ,as_re=False
        ,case=False
        ,word=False
        ,file_mask  ='*.*'
        ,file_exmask=''
        ,depth      =-1          # -1=all, 0=only root
        ,skips_hidn =True
        ,skips_binr =True
        ,sort_type  =''         # 'date,desc' 'date,asc'
        ,only_frst=0):
    pass

if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[ ][kv-kv][25feb16] 'Sort files' with opts No/By date desc/By date asc 
[ ][kv-kv][25feb16] 'First N files'
[ ][kv-kv][25feb16] 'Append to results'
[ ][kv-kv][25feb16] 'Show results in' with opts Panel/Tab/CB
[ ][kv-kv][25feb16] 'Only count in each files'
[ ][kv-kv][25feb16] 'Show files to select'
[ ][kv-kv][25feb16] 'include/exclude masks'
[ ][kv-kv][25feb16] 'depth' for recursion
[+][kv-kv][25feb16] 'preset'
'''
