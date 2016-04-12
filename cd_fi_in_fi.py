''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.1.1 2016-04-08'
ToDo: (see end of file)
'''

import  re, os, sys, glob, json, collections
from    fnmatch         import fnmatch
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
#from    cudax_lib       import log
#from    .cd_plug_lib    import f, get_translation, dlg_wrapper
from    .cd_plug_lib    import *

OrdDict = collections.OrderedDict
#FROM_API_VERSION= '1.0.119'

pass;                           LOG = (-2==-2)  # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)

# I18N
_       = get_translation(__file__)

class ProgressAndBreak:
    """ Helper for 
        - Show progress of working
        - Allow user to break long procces
    """
    def __init__(self):
        app.app_proc(app.PROC_SET_ESCAPE, '0')

    def set_progress(self, msg):
        app.msg_status(msg)

    def need_break(self, with_request=False, process_hint=''):
        was_esc = app.app_proc(app.PROC_GET_ESCAPE, '')
        if was_esc and with_request:
            if app.ID_YES == app.msg_box(_('Break process?'), app.MB_YESNO):
                return True
            app.app_proc(app.PROC_SET_ESCAPE, '0')
            was_esc = False
        return was_esc
   #class ProgressAndBreak

GAP     = 5

class Command:
#   def show_dlg(self):
#       self.show_dlg_( what='step', opts={
#           'repl':'other',
#           'incl':'*.*',
#           'excl':'',
#           'fold':r'c:\temp\try-ff',
#           'dept':-1,
#           'case':'1',
#           'word':'1',
#           'reex':'1',
#       })
    def show_dlg(self, what='', opts={}):
        max_hist= apx.get_opt('ui_max_history_edits', 20)
        cfg_json= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_find_in_files.json'
        stores  = apx._json_loads(open(cfg_json).read(), object_pairs_hook=OrdDict)    if os.path.exists(cfg_json) else    OrdDict()
        mask_h  = _('Space separated masks.\rQuote as "m a s k" if space is need.\rUse ? for any character and * for any fragment')
#       incl_h  = mask_h+_('\rEmpty equal *.*')
        reex_h  = _('Reg.ex')
        case_h  = _('Case sensitive')
        word_h  = _('Whole words')
        brow_h  = _('Select folder')
        curr_h  = _('Use folder of current file')
        more_h  = _('Show/Hide advance options')
        adju_h  = _('Change dialog layout')
        frst_h  = _('Use only N first files for searching')
        coun_h  = _('Only count matches in files.\rAs Find with Collect:"Match counts".')
        pset_h  = _('Save options for future.\rRestore saved options')
        dept_l  = [_('All'), _('In folder only'), _('1 level'), _('2 level'), _('3 level'), _('4 level'), _('5 level')]
        join_c  = _('Appen&d to results')
        toed_c  = _('Show in editor')
        reed_c  = _('Reuse tab')
        cllc_l  = [_('All matches'), _('Match counts'), _('Filenames')]
        skip_l  = [' ', _('Hidden'), _('Binary'), _('Hidden, Binary')]
        sort_l  = [_("Don't sort"), _('By date, from newest'), _('By date, from oldest')]
    
        DLG_W0, \
        DLG_H0  = (700, 325)
        TXT_W   = 380

        what_s  = what
        repl_s  = opts.get('repl', '')
        reex01  = opts.get('reex', stores.get('reex', '0'))
        case01  = opts.get('case', stores.get('case', '0'))
        word01  = opts.get('word', stores.get('word', '0'))
        incl_s  = opts.get('incl', stores.get('incl',  [''])[0])
        excl_s  = opts.get('excl', stores.get('excl',  [''])[0])
        fold_s  = opts.get('fold', stores.get('fold',  [''])[0])
        dept_n  = opts.get('dept', stores.get('dept',  0)-1)+1
        cllc_s  = opts.get('cllc', stores.get('cllc', '0'))
        join_s  = opts.get('join', stores.get('join', '0'))
        toed_s  = opts.get('toed', stores.get('toed', '0'))
        reed_s  = opts.get('reed', stores.get('reed', '0'))
        skip_s  = opts.get('skip', stores.get('skip', '0'))
        sort_s  = opts.get('sort', stores.get('sort', '0'))
        frst_s  = opts.get('frst', stores.get('frst', '0'))
        focused = 'what'
        while True:
            what_l  = [s for s in stores.get('what', []) if s ]
            incl_l  = [s for s in stores.get('incl', []) if s ]
            excl_l  = [s for s in stores.get('excl', []) if s ]
            fold_l  = [s for s in stores.get('fold', []) if s ]
            repl_l  = [s for s in stores.get('repl', []) if s ]
        
            wo_excl = stores.get('wo_excl', True)
            wo_repl = True #stores.get('wo_repl', True)
            wo_adva = stores.get('wo_adva', True)
           #c_more  = 'Show "Ad&v"' if wo_adva else 'Hide "Ad&v"'
            c_more  = _('Mor&e >>') if wo_adva else _('L&ess <<')
            gap1    = (GAP- 25 if wo_excl else GAP)
            gap2    = (GAP- 25 if wo_repl else GAP)+gap1
            gap3    = (GAP-115 if wo_adva else GAP)+gap2
            DLG_W,\
            DLG_H   = (DLG_W0, DLG_H0+gap3)
            lbl_l   = GAP+35*3+GAP
            cmb_l   = lbl_l+100
            tl2_l   = lbl_l+200
            tbn_l   = cmb_l+TXT_W+GAP

            cnts    = ([]                                                                                                              # gmqvxyz
                     +[dict(cid='reex',tp='ch-bt'   ,tid='what'     ,l=GAP+35*0 ,w=35       ,cap='&.*'                  ,hint=reex_h)] # &.
                     +[dict(cid='case',tp='ch-bt'   ,tid='what'     ,l=GAP+35*1 ,w=35       ,cap='&aA'                  ,hint=case_h)] # &a
                     +[dict(cid='word',tp='ch-bt'   ,tid='what'     ,l=GAP+35*2 ,w=35       ,cap='"&w"'                 ,hint=word_h)] # &w
                     +[dict(           tp='lb'      ,tid='what'     ,l=lbl_l    ,r=cmb_l    ,cap=_('&Find:')                        )] # &f
                     +[dict(cid='what',tp='cb'      ,t=GAP          ,l=cmb_l    ,w=TXT_W    ,items=what_l                           )] # 
                                                
                     +[dict(           tp='lb'      ,tid='incl'     ,l=lbl_l    ,r=cmb_l    ,cap=_('&In files:')        ,hint=mask_h)] # &i
                     +[dict(cid='incl',tp='cb'      ,t=GAP+28       ,l=cmb_l    ,w=TXT_W    ,items=incl_l                           )] # 
                    +([] if wo_excl else []                         
                     +[dict(           tp='lb'      ,tid='excl'     ,l=lbl_l    ,r=cmb_l    ,cap=_('Not in files:')     ,hint=mask_h)] # 
                     +[dict(cid='excl',tp='cb'      ,t=GAP+56       ,l=cmb_l    ,w=TXT_W    ,items=excl_l                           )] # 
                    )                                               
                     +[dict(cid='cfld',tp='bt'      ,tid='fold'     ,l=GAP      ,w=35*3     ,cap=_('&Current folder')   ,hint=curr_h)] # &c
                     +[dict(           tp='lb'      ,tid='fold'     ,l=lbl_l    ,r=cmb_l    ,cap=_('I&n folder:')                   )] # &n
                     +[dict(cid='fold',tp='cb'      ,t=gap1+84      ,l=cmb_l    ,w=TXT_W    ,items=fold_l                           )] # 
                     +[dict(cid='brow',tp='bt'      ,tid='fold'     ,l=tbn_l    ,r=DLG_W-GAP,cap=_('&Browse...')        ,hint=brow_h)] # &b
                     +[dict(           tp='lb'      ,tid='dept'     ,l=cmb_l    ,w=100      ,cap=_('In s&ubfolders:')               )] # &u
                     +[dict(cid='dept',tp='cb-ro'   ,t=gap1+112     ,l=tl2_l    ,w=120      ,items=dept_l                           )] # 
                    +([] if wo_repl else []                         
                     +[dict(           tp='lb'      ,tid='repl'     ,l=lbl_l    ,r=cmb_l    ,cap=_('&Replace with:')                )] # &r
                     +[dict(cid='repl',tp='cb'      ,t=gap1+135     ,l=cmb_l    ,w=TXT_W    ,items=repl_l                           )] # 
                     +[dict(cid='!rep',tp='bt'      ,tid='repl'     ,l=tbn_l    ,r=DLG_W-GAP,cap=_('Re&place')                      )] # &p
                    )                                               
                    +([] if wo_adva else  []                        
                     +[dict(           tp='lb'      ,t=gap2+170     ,l=GAP      ,w=150      ,cap=_('== Adv. report options ==')     )] # 
                     +[dict(           tp='lb'      ,tid='cllc'     ,l=GAP      ,w=100      ,cap=_('Co&llect:')                     )] # &l
                     +[dict(cid='cllc',tp='cb-ro'   ,t=gap2+190     ,l=GAP+100  ,r=cmb_l    ,items=cllc_l                           )] # 
                     +[dict(cid='join',tp='ch'      ,t=gap2+217     ,l=GAP      ,w=150      ,cap=join_c                             )] # &d
                     +[dict(cid='toed',tp='ch'      ,t=gap2+244     ,l=GAP      ,w=150      ,cap=toed_c                             )] # 
                     +[dict(cid='reed',tp='ch'      ,t=gap2+244     ,l=GAP+150  ,w=150      ,cap=reed_c                             )] # 
                                                
                     +[dict(           tp='lb'      ,t=gap2+170     ,l=tl2_l    ,w=150      ,cap=_('== Adv. find options ==')       )] # 
                     +[dict(           tp='lb'      ,tid='skip'     ,l=tl2_l    ,w=100      ,cap=_('S&kip files:')                  )] # &k
                     +[dict(cid='skip',tp='cb-ro'   ,t=gap2+190     ,l=tl2_l+100,w=150      ,items=skip_l                           )] # 
                     +[dict(           tp='lb'      ,tid='sort'     ,l=tl2_l    ,w=100      ,cap=_('S&ort file list:')              )] # &o
                     +[dict(cid='sort',tp='cb-ro'   ,t=gap2+217     ,l=tl2_l+100,w=150      ,items=sort_l                           )] # 
                     +[dict(           tp='lb'      ,tid='frst'     ,l=tl2_l    ,w=100      ,cap=_('Firsts (&0=all):')  ,hint=frst_h)] # &0
                     +[dict(cid='frst',tp='ed'      ,t=gap2+244     ,l=tl2_l+100,w=150                                              )] # 
                    )                                                                                                               
                     +[dict(cid='help',tp='bt'      ,t=DLG_H-GAP-50 ,l=tbn_l    ,r=DLG_W-GAP,cap=_('&Help...')                      )] # &h
                     +[dict(cid='!fnd',tp='bt'      ,tid='what'     ,l=tbn_l    ,r=DLG_W-GAP,cap=_('Find'),props='1'                )] #    default
                     +[dict(cid='!cnt',tp='bt'      ,tid='incl'     ,l=tbn_l    ,r=DLG_W-GAP,cap=_('Coun&t')            ,hint=coun_h)] # &t
                     +[dict(cid='more',tp='bt'      ,t=DLG_H-GAP-25 ,l=GAP      ,w=35*3     ,cap=c_more                 ,hint=more_h)] # &e
                     +[dict(cid='cust',tp='bt'      ,t=DLG_H-GAP-25 ,l=GAP*2+35*3,w=35*3    ,cap=_('Ad&just...')        ,hint=adju_h)] # &j
                     +[dict(cid='pres',tp='bt'      ,t=DLG_H-GAP-25 ,l=tbn_l-95 ,w=90       ,cap=_('Pre&sets...')       ,hint=pset_h)] # &s
                     +[dict(cid='-'   ,tp='bt'      ,t=DLG_H-GAP-25 ,l=tbn_l    ,r=DLG_W-GAP,cap=_('Close')                         )] # 
                    )
            vals    =       dict( reex=reex01
                                 ,case=case01
                                 ,word=word01
                                 ,what=what_s
                                 ,incl=incl_s
                                 ,fold=fold_s
                                 ,dept=dept_n
                                )
            if not wo_excl:
                vals.update(dict( excl=excl_s))
            if not wo_repl:
                vals.update(dict( repl=repl_s))
            if not wo_adva:
                vals.update(dict( cllc=cllc_s
                                 ,join=join_s
                                 ,toed=toed_s
                                 ,reed=reed_s
                                 ,skip=skip_s
                                 ,sort=sort_s
                                 ,frst=frst_s))
            pass;              #LOG and log('vals={}',pf(vals))
            btn,vals    = dlg_wrapper(_('Find in Files'), DLG_W, DLG_H, cnts, vals, focus_cid=focused)
            if btn is None or btn=='-': return None
            pass;              #LOG and log('vals={}',pf(vals))
            reex01      = vals['reex']
            case01      = vals['case']
            word01      = vals['word']
            what_s      = vals['what']
            incl_s      = vals['incl']
            if not wo_excl:     
                excl_s  = vals['excl']
            fold_s      = vals['fold']
            dept_n      = vals['dept']
            if not wo_repl:     
                repl_s  = vals['repl']
            if not wo_adva:     
                cllc_s  = vals['cllc']
                join_s  = vals['join']
                toed_s  = vals['toed']
                reed_s  = vals['reed']
                skip_s  = vals['skip']
                sort_s  = vals['sort']
                frst_s  = vals['frst']
            pass;              #LOG and log('what_s,incl_s,fold_s={}',(what_s,incl_s,fold_s))
            
            stores['reex']  = reex01
            stores['case']  = case01
            stores['word']  = word01
            stores['what']  = add_to_history(what_s, stores.get('what', []), max_hist, unicase=False)
            stores['incl']  = add_to_history(incl_s, stores.get('incl', []), max_hist, unicase=(os.name=='nt'))
            stores['excl']  = add_to_history(excl_s, stores.get('excl', []), max_hist, unicase=(os.name=='nt'))
            stores['fold']  = add_to_history(fold_s, stores.get('fold', []), max_hist, unicase=(os.name=='nt'))
            stores['dept']  = dept_n
            stores['repl']  = add_to_history(repl_s, stores.get('repl', []), max_hist, unicase=False)
            stores['cllc']  = cllc_s
            stores['join']  = join_s
            stores['toed']  = toed_s
            stores['reed']  = reed_s
            stores['skip']  = skip_s
            stores['sort']  = sort_s
            stores['frst']  = frst_s
            open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            
            if btn=='help':
                l           = '\n'
                RE_DOC_REF  = 'https://docs.python.org/3/library/re.html'
                HELP_BODY   = _(
r'''Masks "In file" and "Not in file" can use 
    ?       for any single symbol,
    *       for everything (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
Option "w" is ignored if 
    option ".*" turns on.
    "Find" contains not only letters, digits and "_".
Long-term searching can be interrupted with Esc 
RegExp tips:
- Format for found groups in Replace: \1
''')
                DW, DH      = 600, 400
                dlg_wrapper(_('Help for "Find in files"'), GAP+DW+GAP,GAP+DH+GAP,
                     [dict(cid='htx',tp='me'    ,t=GAP  ,h=DH-28,l=GAP          ,w=DW   ,props='1,1,1'                                  ) #  ro,mono,border
                     ,dict(          tp='ln-lb' ,tid='-'        ,l=GAP          ,w=180  ,cap=_('RegExp on python.org'),props=RE_DOC_REF )
                     ,dict(cid='-'  ,tp='bt'    ,t=GAP+DH-23    ,l=GAP+DW-80    ,w=80   ,cap=_('&Close')                                )
                     ], dict(htx=HELP_BODY), focus_cid='htx')
                continue#while
            if btn=='pres':
                pset_l  = stores.setdefault('pset', [])
                dlg_list= [f(_('Restore: {nm}\t[{il}]In files, [{fo}]In folder, [{aa}].*aAw, [{fn}]Adv. find, [{rp}]Adv. report')
                            ,nm=ps['name']
                            ,il=ps.get('_il_',' ')
                            ,fo=ps.get('_fo_',' ')
                            ,aa=ps.get('_aa_',' ')
                            ,fn=ps.get('_fn_',' ')
                            ,rp=ps.get('_rp_',' ')
                            ) 
                            for ps in pset_l] \
                        + [_('Save preset...')]
                ps_ind  = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(dlg_list))
                if ps_ind is None:  continue#while
                if ps_ind<len(pset_l):
                    # Restore
                    ps  = pset_l[ps_ind]
                    incl_s = ps.get('incl', incl_s)
                    excl_s = ps.get('excl', excl_s)
                    fold_s = ps.get('fold', fold_s)
                    dept_n = ps.get('dept', dept_n)
                    reex01 = ps.get('reex', reex01)
                    case01 = ps.get('case', case01)
                    word01 = ps.get('word', word01)
                    cllc_s = ps.get('cllc', cllc_s)
                    join_s = ps.get('join', join_s)
                    toed_s = ps.get('toed', toed_s)
                    reed_s = ps.get('reed', reed_s)
                    skip_s = ps.get('skip', skip_s)
                    sort_s = ps.get('sort', sort_s)
                    frst_s = ps.get('frst', frst_s)
                    app.msg_status(_('Restore preset: ')+ps['name'])
                else:
                    custs   = app.dlg_input_ex(6, _('Save preset')
                        , _('Preset name')                                            , f(_('Preset #{}'), 1+len(pset_l))
                        , _('Save "In files"/"Not in files" (0/1)')                   , '1'   # 1
                        , _('Save "In folder"/"Subfolders" (0/1)')                    , '1'   # 2
                        , _('Save ".*"/"aA"/"w" (0/1)')                               , '1'   # 3
                        , _('Save (Adv. find) "Skip"/"Sort"/"Firsts" (0/1)')          , '1'   # 4
                        , _('Save (Adv. report) "Collect"/"Append"/"In editor" (0/1)'), '1'   # 5
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
                        ps['dept']  = dept_n
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
                        ps['reed']  = reed_s
                        pass
                    pset_l += [ps]
                    open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                    app.msg_status(_('Save new preset'))
                
            if btn=='more':
                stores['wo_adva']       = not stores.get('wo_adva', True)
                open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                continue#while
            if btn=='cust':
                custs   = app.dlg_input_ex(3, _('Adjust dialog')
                    , _('Width edit Find/Replace/... (min 300)'), str(stores.get('wd_txts', 300))
                    , _('Width button Browse/Help    (min 100)'), str(stores.get('wd_btns', 100))
                    , _('Show Exclude masks (0/1)')             , str(0 if stores.get('wo_excl', True) else 1)
#                   , _('Show Replace (0/1)')                   , str(0 if stores.get('wo_repl', True) else 1)
                    )
                if custs is not None:
                    stores['wd_txts']   = max(300, int(custs[0]))
                    stores['wd_btns']   = max(100, int(custs[1]))
                    stores['wo_excl']   = (custs[2]=='0')
#                   stores['wo_repl']   = (custs[3]=='0')
                    open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                continue#while

            open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            if False:pass
            elif btn=='brow':
                path    = app.dlg_dir(fold_s)
                fold_s  = path if path else fold_s
            elif btn=='cfld':
                path    = ed.get_filename()
                fold_s  = os.path.dirname(path) if path else fold_s

            elif btn=='!rep':
                pass
            elif btn in ('!cnt', '!fnd'):
                if not what_s:
                    app.msg_box(_('Fill "Find"'), app.MB_OK) 
                    focused     = 'what'
                    continue#while
                if reex01=='1':
                    try:
                        re.compile(what_s)
                    except Exception as ex:
                        app.msg_box(f(_('Set proper "Find"\n\nError:\n{}'),ex), app.MB_OK) 
                        focused     = 'what'
                        continue#while
                if not fold_s or not os.path.isdir(fold_s):
                    app.msg_box(_('Set real "In folder"'), app.MB_OK) 
                    focused     = 'fold'
                    continue#while
                if not incl_s:
                    app.msg_box(_('Fill "In files"'), app.MB_OK) 
                    focused     = 'incl'
                    continue#while
                if 0 != incl_s.count('"')%2:
                    app.msg_box(_('Fix quotes in "In files"'), app.MB_OK) 
                    focused     = 'incl'
                    continue#while
                if 0 != excl_s.count('"')%2:
                    app.msg_box(_('Fix quotes in "Not in files"'), app.MB_OK) 
                    focused     = 'excl'
                    continue#while
                how_walk   =dict(
                     root       =fold_s
                    ,file_incl  =incl_s
                    ,file_excl  =excl_s
                    ,depth      =dept_n-1               # ['All', 'In folder only', '1 level', ...]
                    ,skip_hidn  =skip_s in ('1', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                    ,skip_binr  =skip_s in ('2', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                    ,sort_type  =apx.icase( sort_s=='0','' 
                                           ,sort_s=='1','date,desc' 
                                           ,sort_s=='2','date,asc' ,'') # [' ', 'By date, from newest', 'By date, from oldest']
                    ,only_frst  =int(frst_s)
                    )
                what_find  =dict(
                     find       =what_s
                    ,mult       =False
                    ,reex       =reex01=='1'
                    ,case       =case01=='1'
                    ,word       =word01=='1'
                    )
                what_save  =dict(  # cllc_s in ['All matches', 'Match counts'==(btn=='!cnt'), 'Filenames']
                     count      = btn=='!cnt' or  cllc_s!='2'
                    ,place      = btn!='!cnt' and cllc_s=='0'
                    ,fragm      = btn!='!cnt' and cllc_s=='0' #and reex01=='0'
                    ,lines      = btn!='!cnt' and cllc_s=='0' #and reex01=='0'
                    )
                rpt_data, frs= find_in_files(
                     how_walk   = how_walk
                    ,what_find  = what_find
                    ,what_save  = what_save
                    ,progressor = ProgressAndBreak()
                    )
                pass;          #LOG and log('frs={}, rpt_data=\n{}',frs, pf(rpt_data))
                app.msg_status(_('Matches not found')
                                if 0==len(rpt_data) else
                               f(_('Found {} match(es) in {} file(s)'), frs, len(rpt_data))
                            )
                if '1'==vals['toed']:
                    self._report_to_tab(rpt_data, dict(frs=frs, files=len(rpt_data)), '1'==vals['reed'], '1'==vals['join'], how_walk, what_find, what_save)
           #while
#       return (res, data)

#       open(cfg_json, 'w').write(json.dumps(stores, indent=4))
       #def show_dlg

    last_ed_num = 0
    def _report_to_tab(self, rpt_data, rpt_stat, reed_tab, join_to_end, how_walk, what_find, what_save):
        pass;                   LOG and log('join_to_end={}',join_to_end)
        rpt_ed  = None
        start_ln= 0
        if reed_tab or join_to_end:
            for h in app.ed_handles(): 
                try_ed   = app.Editor(h)
                if try_ed.get_prop( app.PROP_TAG) == 'f-in-f_'+str(self.last_ed_num):
                    rpt_ed  = try_ed
                    if join_to_end:
                        start_ln= -1
                    else:
                        rpt_ed.set_text_all('')
                    pass;      LOG and log('found ed',)
                    break #for h
        if rpt_ed is None:
            app.file_open('')
            self.last_ed_num += 1
            ed.set_prop(            app.PROP_TAG,    'f-in-f_'+str(self.last_ed_num))
            rpt_ed  = ed

        rpt_ed.set_text_line(start_ln, f(_('Search for "{}" in folder "{}" ({} matches in {} files)')
                                ,what_find['find']
                                ,how_walk['root']
                                ,rpt_stat['frs']
                                ,rpt_stat['files']))
        for path_d in rpt_data:
            path    = path_d['file']
            if False:pass
            elif 1==len(path_d):
                rpt_ed.set_text_line(    -1, path)
            elif 2==len(path_d):
                rpt_ed.set_text_line(    -1, f('{}: #{}', path, path_d['count']))
            elif 3==len(path_d):
                items   = path_d['items']
                for item in items:
                    rpt_ed.set_text_line(-1, f(_('{}({}): {}'), path, 1+item.get('row',0), item.get('line','')))
       #def _report_to_tab
   #class Commandc

def add_to_history(val, lst, max_len, unicase=True):
    """ Add/Move val to list head.
    """
#   if not val:
#       return lst
    pass;                      #LOG and log('val, lst={}',(val, lst))
    lst_u = [ s.upper() for s in lst] if unicase else lst
    val_u = val.upper()               if unicase else val
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

##############################################################################
def find_in_files(how_walk:dict, what_find:dict, what_save:dict, progressor=None):
    """ Scan files by how_walk with keys:
            'root'         !str
            'depth'         int(-1)    -1=all, 0=only root
            'file_incl'    !str
            'file_excl'     str('')
            'sort_type'     str('')     ''/'date,desc'/'date,asc'
            'only_frst'     int(0)      0=all
            'skip_hidn'     bool(T)
            'skip_binr'     bool(F) 
            'skip_size'     int(0)      0=all Kbyte
        for find in it fragments by what_find with keys:
            'find'         !str
            'mult'          bool(F)     Multylines 
            'reex'          bool(F)     
            'case'          bool(F)     
            'word'          bool(F)     
        and and save info by what_save with keys:
            'count'         bool(T)     Need counts
            'place'         bool(T)     Need places
            'fragm'         bool(F)     Need fragments
            'lines'         bool(T)     Need lines with fragments
        Return 
            [{file:'path'}          if not what_save['count']
            ,{file:'path'
             ,count:int}                if what_save['count'] and not what_save['place']
            ,{file:'path'
             ,count:int                 if what_save['count']
             ,items:[
                ,place:(row,col,len)    if what_save['place'] and not what_save['fragm']
             ]}
            ,{file:'path'
             ,count:int                 if what_save['count']
             ,items:[
                ,place:(row,col,len)    if what_save['place']
                ,fragm:'text'           if what_save['fragm']
             }
            ,{file:'path'
             ,count:int                 if what_save['count']
             ,items:[
                {place:(row,col,len)    if what_save['place']
                ,fragm:'text'           if what_save['fragm']
                ,lines:'line'           if what_save['lines']
                }
             }
            ,...]
    """
    pass;                      #LOG and log('how_walk={}',pf(how_walk))
    pass;                      #LOG and log('what_find={}',pf(what_find))
    pass;                      #LOG and log('what_save={}',pf(what_save))
    files   = collect_files(how_walk, progressor)
    pass;                       LOG and log('#files={}',len(files))
    pass;                      #LOG and log('files={}',pf(files))
    
    pttn_s  =           what_find['find']
    mult_b  = what_find['mult']
    case_b  = what_find['case']
    flags   = re.M if mult_b else 0 \
            +    0 if case_b else re.I
    if not what_find['reex']:
        if what_find['word'] and re.match('^\w+$', pttn_s):
            pttn_s  = r'\b'+pttn_s+r'\b'
        else:
            pttn_s  = re.escape(pttn_s)
    pass;                      #LOG and log('pttn_s, flags={}',(pttn_s, flags))
    pttn    = re.compile(pttn_s, flags)

    rsp_l   = []
    rsp_frs = 0
    cnt_b   = what_save['count']
    plc_b   = what_save['place']
    fra_b   = what_save['fragm']
    lin_b   = what_save['lines']
    pass;                   t=log('?? files (==',) if LOG else 0
    for path_n, path in enumerate(files):
        if progressor and 0==path_n%17:
            progressor.set_progress(f('Seaching: {}% (found {} match(es) in {} file(s))', int(100*path_n/len(files)), rsp_frs, len(rsp_l)))
#           progressor.set_progress(f('Seaching: {}% (found {} match(es) in {} file(s))', round(100*path_n/len(files),2), rsp_frs, len(rsp_l)))
            if progressor.need_break():
                break#for path
        try:
            with open(path) as h_path:
                if not cnt_b:
                    # Only path finding
                    body    = h_path.read()
                    if pttn.search(body):
                        rsp_l  += [dict(file=path)]
                        rsp_frs+= 1
                    continue#for path

                if mult_b:
                    # Find MULTILINE fragments
                    body    = h_path.read()
                    mtchs   = list(pttn.finditer(body))
                    count   = len(mtchs)
                    if not plc_b:
                        # Only counting
                        rsp_l  += [dict(file=path
                                    ,count=count)]
                        rsp_frs+= count
                        continue#for path
                    items   = []
                    for mtch in mtchs:
                        ln      = 0#??
                        item    =       dict(row=ln, col=mtch.start(), ln=mtch.end()-mtch.start())
                        if fra_b:
                            item.update(dict(fragm=mtch.group()))
                        if lin_b:
                            line    = ''#??
                            item.update(dict(line=line))
                        items  += [item]
                    rsp_l  += [dict( file=path
                                    ,count=count
                                    ,items=items)]
                    rsp_frs+= count
                    continue#for path
               #if not mult_b:
                # Find IN-LINE fragments
                count   = 0
                items   = []
                lines   = h_path.readlines()
                for ln,line in enumerate(lines):
                    mtchs   = list(pttn.finditer(line))
                    if not plc_b:
                        # Only counting
                        count  += len(mtchs)
                    else:
                        for mtch in mtchs:
                            count  += 1
                            item    =       dict(row=ln, col=mtch.start(), ln=mtch.end()-mtch.start())
                            if fra_b:
                                item.update(dict(fragm=mtch.group()))
                            if lin_b:
                                item.update(dict(line=line))
                            items  += [item]
                   #for line
                if not count:
                    continue#for path
                if not plc_b:
                    # Only counting
                    rsp_l  += [dict( file=path
                                    ,count=count)]
                    rsp_frs+= count
                else:
                    rsp_l  += [dict( file=path
                                    ,count=count
                                    ,items=items)]
                    rsp_frs+= count
               #with h_path
        except Exception as ex:
            print(f(_('Cannot open "{}": {}'), path, ex))
       #for path
    pass;                      #t=None
    pass;                       LOG and log('ok files ==) #rsp_l={}',len(rsp_l))
    return rsp_l, rsp_frs
   #def find_in_files

def collect_files(how_walk, progressor=None):
    """ how_walk keys:
        'root'         !str
        'depth'         int(-1)    -1=all, 0=only root
        'file_incl'    !str
        'file_excl'     str('')
        'sort_type'     str('')     ''/'date,desc'/'date,asc'
        'only_frst'     int(0)      0=all
        'skip_hidn'     bool(T)
        'skip_binr'     bool(F) 
        'skip_size'     int(0)      0=all Kbyte
    """
    pass;                       t=log('>>(:)how_walk={}',how_walk) if LOG else 0 
    root    = how_walk['root']
    if not os.path.isdir(root): return []
    rsp     = []
    incl    = how_walk[    'file_incl'    ].strip()
    excl    = how_walk.get('file_excl', '').strip()
    depth   = how_walk.get('depth', -1)
    hidn    = how_walk.get('skip_hidn', True)
    binr    = how_walk.get('skip_binr', False)
    size    = how_walk.get('skip_size', 0)
    frst    = how_walk.get('only_frst', 0)
    sort    = how_walk.get('sort_type', '')
    def prep_masks(mask):
        mask    = mask.strip()
        if '"' in mask:
            # Temporary replace all ' ' into "" to '/'
            re_binqu= re.compile(r'"([^"]+) ([^"]+)"')
            while re_binqu.search(mask):
                mask= re_binqu.sub(r'"\1/\2"', mask) 
            masks   = mask.split(' ')
            masks   = [m.strip('"').replace('/', ' ') for m in masks if m]
        else:
            masks   = mask.split(' ')
        masks   = [m for m in masks if m]
        return masks
    incls   = prep_masks(incl)
    excls   = prep_masks(excl)
    pass;                       LOG and log('incls={}',incls)
    pass;                       LOG and log('excls={}',excls)
    dir_n   = 0
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root)):
        pass;                  #LOG and log('dirpath, #filenames={}',(dirpath, len(filenames)))
        pass;                  #LOG and log('dirpath, dirnames, filenames={}',(dirpath, dirnames, filenames))
        dir_n   += dir_n
        if progressor and 0==dir_n%17:
            progressor.set_progress(_('Collect files in: ')+dirpath)
            if progressor.need_break():
                return []
        if hidn:
            # Cut hidden dirs
            dir4cut  = [dirname for dirname in dirnames if is_hidden_file(os.path.join(dirpath, dirname))]
            for dirname in dir4cut:
                dirnames.remove(dirname)
            
        walk_depth  = 0 \
                        if os.path.samefile(dirpath, root) else \
                      1+os.path.relpath(dirpath, root).count(os.sep)
        pass;                  #LOG and log('depth,walk_depth={}',(depth,walk_depth))
        if walk_depth>depth>0:
            pass;               LOG and log('skip by >depth',())
            dirnames.clear()
            continue#for dirpath
        for filename in filenames:
            if not      any(map(lambda cl:fnmatch(filename, cl), incls)):   continue#for filename
            if excl and any(map(lambda cl:fnmatch(filename, cl), excls)):   continue#for filename
            path    = os.path.join(dirpath, filename)
            if hidn and is_hidden_file(path):                               continue#for filename
            if binr and is_birary_file(path):                               continue#for filename
            if size and os.path.getsize(path) > size*1024:                  continue#for filename
            rsp    += [path]
            if  not sort and len(rsp)>=frst>0:
                break#for filename
           #for filename
        if      not sort and len(rsp)>=frst>0:
            pass;               LOG and log('break by >frst',())
            break#for dirpath
        if depth==0:
            pass;               LOG and log('break by depth==0',())
            break#for dirpath
       #for dirpath
    if sort:
        tm_pth  = [(os.path.getmtime(path),path) for path in rsp]
        rsp     = [tp[1] for tp in sorted(tm_pth, reverse=(sort=='date,desc'))]
        if len(rsp)>=frst>0:
            rsp = rsp[:frst]
    return rsp
   #def collect_files
    
TEXTCHARS = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
def is_birary_file(path, blocksize=1024, def_ans=None):
    if not os.path.isfile(path):    return def_ans
    try:
        block   = open(path, 'r').read(blocksize)
        if not      block:  return False
        if b'\0' in block:  return True
        return bool(block.translate(None, TEXTCHARS))
    except:
        return def_ans
   #def is_birary_file

if os.name == 'nt':
    # For Windows use file attribute.
    import ctypes
    FILE_ATTRIBUTE_HIDDEN = 0x02
def is_hidden_file(path):
    """ Cross platform hidden file/dir test  """
    if os.name == 'nt':
        # For Windows use file attribute.
        attrs   = ctypes.windll.kernel32.GetFileAttributesW(path)
        return attrs & FILE_ATTRIBUTE_HIDDEN

    # For *nix use a '.' prefix.
    return os.path.basename(path).startswith('.')
   #def is_hidden_file

if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[+][kv-kv][25feb16] 'Sort files' with opts No/By date desc/By date asc 
[+][kv-kv][25feb16] 'First N files'
[ ][kv-kv][25feb16] 'Append to results'
[ ][kv-kv][25feb16] 'Show results in' with opts Panel/Tab/CB
[+][kv-kv][25feb16] 'Only count in each files'
[?][kv-kv][25feb16] 'Show files to select'
[+][kv-kv][25feb16] 'include/exclude masks'
[+][kv-kv][25feb16] 'depth' for recursion
[+][kv-kv][25feb16] 'preset'
[ ][kv-kv][0?apr16] 'Firsts' for walk or for results?
[+][kv-kv][06apr16] testing re-expr correction on btn=='!...'
[+][kv-kv][06apr16] exclude file by size
[+][kv-kv][07apr16] how to show progress?
[+][kv-kv][08apr16] how to user can break?
[+][kv-kv][08apr16] 'try' to open next file
[+][kv-kv][08apr16] incl/excl many masks
[+][kv-kv][08apr16] if []==stores.get('incl')?
[ ][kv-kv][08apr16] Del/Edit presets
[+][kv-kv][08apr16] status report: Found N fragments in M files
'''
