''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.2.14 2017-04-12'
ToDo: (see end of file)
'''

import  re, os, sys, locale, json, collections #, traceback

try:
    import  cudatext            as app
    from    cudatext        import ed
    import  cudax_lib           as apx
    MIN_API_VER = '1.0.168'
except:
    import  sw                  as app
    from    sw              import ed
    from . import cudax_lib     as apx
    MIN_API_VER = '1.0.162'

from    .cd_plug_lib        import *
from    .cd_fif_api         import *

OrdDict = collections.OrderedDict

pass;                          #Tr.tr   = Tr(apx.get_opt('fif_log_file', '')) if apx.get_opt('fif_log_file', '') else Tr.tr
pass;                           LOG     = (-1== 1)         or apx.get_opt('fif_LOG'   , False) # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

MAX_HIST= apx.get_opt('ui_max_history_edits', 20)
CFG_JSON= CdSw.get_setting_dir()+os.sep+'cuda_find_in_files.json'
#CFG_JSON= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_find_in_files.json'

USE_EDFIND_OPS  = apx.get_opt('fif_use_edfind_opt_on_start' , False)
DEF_LOC_ENCO    = 'cp1252' if sys.platform=='linux' else locale.getpreferredencoding()
loc_enco        = apx.get_opt('fif_locale_encoding', DEF_LOC_ENCO)
if 'sw'==app.__name__:
    USE_EDFIND_OPS  = False

GAP     = 5

totb_l          = [TOTB_NEW_TAB, TOTB_USED_TAB]
cllc_l          = [CLLC_MATCH, CLLC_COUNT, CLLC_FNAME]
shtp_l          = [SHTP_SHORT_R, SHTP_SHORT_RCL
                  ,SHTP_MIDDL_R, SHTP_MIDDL_RCL
                  ,SHTP_SPARS_R, SHTP_SPARS_RCL
                  ,SHTP_SHRTS_R, SHTP_SHRTS_RCL
                  ]
dept_l          = [_('All'), _('In folder only'), _('1 level'), _('2 levels'), _('3 levels'), _('4 levels'), _('5 levels')]
skip_l          = [_("Don't skip"), _('Hidden'), _('Binary'), _('Hidden, Binary')]
sort_l          = [_("Don't sort"), _('By date, from newest'), _('By date, from oldest')]
enco_l          = ['{}, UTF-8, '+ENCO_DETD 
                  ,'UTF-8, {}, '+ENCO_DETD 
                  ,'{}, '       +ENCO_DETD 
                  ,'UTF-8, '    +ENCO_DETD 
                  ,'{}, UTF-8'             
                  ,'UTF-8, {}'             
                  ,'{}'                    
                  ,'UTF-8'                 
                  ,              ENCO_DETD
                  ]     \
                    if loc_enco!='UTF-8' else   \
                  ['{}, '       +ENCO_DETD 
                  ,'{}'                    
                  ,              ENCO_DETD
                  ]
enco_l          = [f(enco, loc_enco) for enco in enco_l]

def desc_fif_val(fifkey, val=None):
    pass;                      #LOG and log('fifkey, val={}',(fifkey, val))
    if val is None: return ''
    if False:pass
    elif fifkey in ('incl','excl','fold','frst'):   return val
    elif fifkey in ('reex','case','word'
                   ,'join','algn','cntx'):          return _('On') if val=='1' else _('Off')
    elif fifkey=='totb':    return totb_l[int(val)] if val in ('0', '1') else val
    val = int(val)
    if False:pass
    elif fifkey=='dept':    return dept_l[val] if 0<=val<len(dept_l) else ''
    elif fifkey=='skip':    return skip_l[val] if 0<=val<len(skip_l) else ''
    elif fifkey=='sort':    return sort_l[val] if 0<=val<len(sort_l) else ''
    elif fifkey=='enco':    return enco_l[val] if 0<=val<len(enco_l) else ''
    elif fifkey=='cllc':    return cllc_l[val] if 0<=val<len(cllc_l) else ''
#   elif fifkey=='totb':    return totb_l[val] if 0<=val<len(totb_l) else ''
    elif fifkey=='shtp':    return shtp_l[val] if 0<=val<len(shtp_l) else ''
   #def desc_fif_val


class Command:
#   def undo_by_report(self):
#       undo_by_report()
       #def undo_by_report


    def find_in_ed(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        filename= ed.get_filename()
        return dlg_fif(what='', opts=dict(
             incl = os.path.basename(filename) if filename else ed.get_prop(app.PROP_TAB_TITLE)
            ,fold = IN_OPEN_FILES
            ,cllc = str(cllc_l.index(CLLC_MATCH))
            ))
       #def find_in_ed

    def find_in_tabs(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        return dlg_fif(what='', opts=dict(
             incl = '*'
            ,fold = IN_OPEN_FILES
            ,cllc = str(cllc_l.index(CLLC_MATCH))
            ))
       #def find_in_ed

    def repeat_find_by_rpt(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        if ed.get_prop(app.PROP_LEXER_FILE).upper() not in lexers_l:
            return app.msg_status(_('The command works only with reports of FindInFile plugin'))
        req_opts  = report_extract_request(ed)
        if not req_opts:
            return app.msg_status(_('No info to Repeat Finding'))
        req_opts= json.loads(req_opts)
        what    = req_opts.pop('what', '')
        return dlg_fif(what=what, opts=req_opts)
       #def repeat_find_by_rpt

    def show_dlg(self, what='', opts={}):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        return dlg_fif(what, opts)

    def _nav_to_src(self, where:str, how_act='move'):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        return nav_to_src(where, how_act)
    def _jump_to(self, drct:str, what:str):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        return jump_to(drct, what)
    def on_goto_def(self, ed_self):
        pass;                   LOG and log('',())
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Need update application'))
        if ed_self.get_prop(app.PROP_LEXER_FILE).upper() in lexers_l:
            self._nav_to_src('same', 'move')
            return True
    def on_click_dbl(self, ed_self, scam):
        dcls    = Command.get_dcls()
        dcl     = dcls.get(scam, '')
        pass;                   LOG and log('scam, dcl={}',(scam, dcl))
        if not dcl:
            return
        if ed_self.get_prop(app.PROP_LEXER_FILE).upper() not in lexers_l:
            return
        return not self._nav_to_src(*dcl.split(','))
       #def on_click_dbl
    
    dcls    = None
    dcls_def= {'':'same,stay'}
    @staticmethod
    def get_dcls():
        if Command.dcls is None:
            stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                        if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                      OrdDict()
            Command.dcls    = stores.get('dcls', Command.dcls_def)
        return Command.dcls
       #def get_dcls
    
    def dlg_nav_by_dclick(self):
        pass;                   LOG and log('ok',())
        dcls    = Command.get_dcls()
        godef   = apx.get_opt('mouse_goto_definition', 'a')
        hint    = _('See "mouse_goto_definition" in default.json and user.json')
        acts_l  = ["<no action>"
                  ,'Navigate to same group'
                  ,'Navigate to next group'
                  ,'Navigate to prev group'
                  ,'Navigate to next group, activate'
                  ,'Navigate to prev group, activate'
                  ]
        sgns_l  = [''
                  ,'same,stay'
                  ,'next,stay'
                  ,'prev,stay'
                  ,'next,move'
                  ,'prev,move'
                  ]
        aid,vals,*_t   = dlg_wrapper(_('Configure found result navigation by double-click'), 505,280,     #NOTE: dlg-dclick
             [dict(           tp='lb'    ,tid='nnn' ,l=5        ,w=220  ,cap=              '>[double-click]:'                               ) #
             ,dict(cid='nnn' ,tp='cb-ro' ,t=5       ,l=5+220+5  ,w=270  ,items=acts_l                                                       ) #
             ,dict(           tp='lb'    ,tid='snn' ,l=5        ,w=220  ,cap=        '>Shift+[double-click]:'                               ) #
             ,dict(cid='snn' ,tp='cb-ro' ,t=5+ 30   ,l=5+220+5  ,w=270  ,items=acts_l                                                       ) #
             ,dict(           tp='lb'    ,tid='ncn' ,l=5        ,w=220  ,cap=         '>Ctrl+[double-click]:'                               ) #
             ,dict(cid='ncn' ,tp='cb-ro' ,t=5+ 60   ,l=5+220+5  ,w=270  ,items=acts_l                                                       ) #
             ,dict(           tp='lb'    ,tid='scn' ,l=5        ,w=220  ,cap=   '>Shift+Ctrl+[double-click]:'                               ) #
             ,dict(cid='scn' ,tp='cb-ro' ,t=5+ 90   ,l=5+220+5  ,w=270  ,items=acts_l                                                       ) #
             ,dict(           tp='lb'    ,tid='nna' ,l=5        ,w=220  ,cap=          '>Alt+[double-click]:'   ,en=godef!='a'  ,hint=hint  ) #
             ,dict(cid='nna' ,tp='cb-ro' ,t=5+120   ,l=5+220+5  ,w=270  ,items=acts_l                           ,en=godef!='a'  ,hint=hint  ) #
             ,dict(           tp='lb'    ,tid='sna' ,l=5        ,w=220  ,cap=    '>Shift+Alt+[double-click]:'   ,en=godef!='sa' ,hint=hint  ) #
             ,dict(cid='sna' ,tp='cb-ro' ,t=5+150   ,l=5+220+5  ,w=270  ,items=acts_l                           ,en=godef!='sa' ,hint=hint  ) #
             ,dict(           tp='lb'    ,tid='nca' ,l=5        ,w=220  ,cap=     '>Alt+Ctrl+[double-click]:'   ,en=godef!='ca' ,hint=hint  ) #
             ,dict(cid='nca' ,tp='cb-ro' ,t=5+180   ,l=5+220+5  ,w=270  ,items=acts_l                           ,en=godef!='ca' ,hint=hint  ) #
             ,dict(           tp='lb'    ,tid='sca' ,l=5        ,w=220  ,cap='>Shift+Ctrl+Alt+[double-click]:'  ,en=godef!='sca',hint=hint  ) #
             ,dict(cid='sca' ,tp='cb-ro' ,t=5+210   ,l=5+220+5  ,w=270  ,items=acts_l                           ,en=godef!='sca',hint=hint  ) #
             ,dict(cid='!'   ,tp='bt'    ,t=5+240   ,l=5+330    ,w=80   ,cap=_('OK')                            ,def_bt=True                ) #
             ,dict(cid='-'   ,tp='bt'    ,t=5+240   ,l=5+415    ,w=80   ,cap=_('Cancel')                                                    )              
             ],    dict(nnn=sgns_l.index(dcls.get('',   ''))
                       ,snn=sgns_l.index(dcls.get('s',  ''))
                       ,ncn=sgns_l.index(dcls.get('c',  ''))
                       ,scn=sgns_l.index(dcls.get('sc', ''))
                       ,nna=sgns_l.index(dcls.get('a',  ''))
                       ,sna=sgns_l.index(dcls.get('sa', ''))
                       ,nca=sgns_l.index(dcls.get('ca', ''))
                       ,sca=sgns_l.index(dcls.get('sca',''))
                       ), focus_cid='nnn')
        pass;              #LOG and log('vals={}',vals)
        if aid is None or aid=='-': return
        for nnn in ('nnn', 'snn', 'ncn', 'scn', 'nna', 'sna', 'nca', 'sca'):
            sca = nnn.replace('n', '')
            if 0==vals[nnn]:
                dcls.pop(sca, None)
            else:
                dcls[sca]   = sgns_l[vals[nnn]]
        Command.dcls    = dcls
        stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  OrdDict()
        stores['dcls']  = dcls
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
       #def dlg_nav_by_dclick

    def dlg_fif_opts(self):
        return dlg_fif_opts()
   #class Command

def dlg_fif_opts():
    FIF_OPTS    = os.path.dirname(__file__)+os.sep+'fif_options.json'
    fif_opts    = json.loads(open(FIF_OPTS).read())
    from cuda_options_editor import dlg_opt_editor
    dlg_opt_editor('FiF options', fif_opts, subset='fif.')
   #def dlg_fif_opts

def dlg_press(stores, hist_order, invl_l, desc_l):
    pset_l  = stores.setdefault('pset', [])
    stores.setdefault('pset_nnus', 0)
    keys_l  = ['reex','case','word'
              ,'incl','excl'
              ,'fold','dept'
              ,'skip','sort','frst','enco'
              ,'cllc','totb','join','shtp','algn','cntx']
#   totb_i  = keys_l.index('totb')
    invl_l  = invl_l[:]#   invl_l  = [v for v in invl_l]
#   invl_l[totb_i]  = '1' if invl_l[totb_i]=='0' else invl_l[totb_i]
#   invl_l[totb_i]  = str(min(1, int(invl_l[totb_i])))
    ouvl_l  = [v for v in invl_l]
    caps_l  = ['.*','aA','"w"'
              ,'In files','Not in files'
              ,'In folder','Subfolders'
              ,'Skip files','Sort file list','Firsts','Encodings'
              ,'Collect','Show in','Append results','Tree type','Align','Show context']
    def upgrd(ps:list)->list:
        if '_aa_' not in ps:  
            for k in ps:
                if k[0]=='_' and ps[k]=='_':
                    ps[k]   = '-'
            return ps
        _aa  = ps.pop('_aa_', '')
        _if  = ps.pop('_if_', '')
        _fo  = ps.pop('_fo_', '')
        _fn  = ps.pop('_fn_', '')
        _rp  = ps.pop('_rp_', '')
        ps['_reex'] = 'x' if _aa else '-'
        ps['_case'] = 'x' if _aa else '-'
        ps['_word'] = 'x' if _aa else '-'
        ps['_incl'] = 'x' if _if else '-'
        ps['_excl'] = 'x' if _if else '-'
        ps['_fold'] = 'x' if _if else '-'
        ps['_dept'] = 'x' if _if else '-'
        ps['_skip'] = 'x' if _fn else '-'
        ps['_sort'] = 'x' if _fn else '-'
        ps['_frst'] = 'x' if _fn else '-'
        ps['_enco'] = 'x' if _fn else '-'
        ps['_cllc'] = 'x' if _rp else '-'
        ps['_totb'] = 'x' if _rp else '-'
        ps['_join'] = 'x' if _rp else '-'
        ps['_shtp'] = 'x' if _rp else '-'
        ps['_algn'] = 'x' if _rp else '-'
        ps['_cntx'] = 'x' if _rp else '-'
        return ps
       #def upgrd
    for ps in pset_l:
        upgrd(ps)
    if hist_order:
        pset_l  = sorted(pset_l, key=lambda ps: ps.get('nnus', 0), reverse=True)

    dlg_list= [f(_('Restore: {}\t[{}{}{}].*aAw, [{}{}]In files, [{}{}]In folders, [{}{}{}{}]Adv. search, [{}{}{}{}{}{}]Adv. report')
                ,ps['name']
                ,ps['_reex'],ps['_case'],ps['_word']
                ,ps['_incl'],ps['_excl']
                ,ps['_fold'],ps['_dept']
                ,ps['_skip'],ps['_sort'],ps['_frst'],ps['_enco']
                ,ps['_cllc'],ps['_totb'],ps['_join'],ps['_shtp'],ps['_algn'],ps['_cntx']
                ) 
                for ps in pset_l] \
            + [f(_('In folder={}\tFind in all opened documents'), IN_OPEN_FILES)
              ,_('Config presets…\tChange, Move up/down, Delete')
              ,_('Save as preset\tSelect options to save…')]
    ind_inop= len(pset_l)
    ind_conf= len(pset_l)+1
    ind_save= len(pset_l)+2
    ps_ind  = CdSw.dlg_menu(CdSw.MENU_LIST_ALT, '\n'.join(dlg_list))      #NOTE: dlg-menu-press
#   ps_ind  = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(dlg_list))
    if ps_ind is None:  return None
    if False:pass
    elif ps_ind==ind_inop:
        # Find in open files
        ouvl_l[keys_l.index('fold')]    = IN_OPEN_FILES
        return ouvl_l
        
    elif ps_ind<len(pset_l):
        # Restore
        ps      = pset_l[ps_ind]
        stores['pset_nnus'] += 1
        ps['nnus'] = stores['pset_nnus']
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        for i, k in enumerate(keys_l):
            if ps.get('_'+k, '')=='x':
                ouvl_l[i]   = ps.get(k, ouvl_l[i])
#       ouvl_l[totb_i]  = '1' if ouvl_l[totb_i]=='0' else ouvl_l[totb_i]
#       ouvl_l[totb_i]  = str(min(1, int(ouvl_l[totb_i])))
        app.msg_status(_('Options is restored from preset: ')+ps['name'])
        return ouvl_l
        
    elif ps_ind==ind_conf and pset_l:
        # Config
        ps_ind      = 0
        DLG_W       = 5*4+245+300
        while_pss   = True
        while while_pss:
            ps      = pset_l[ps_ind]                                                                        if pset_l else {}
            ps_mns  = [ps['name'] for ps in pset_l]                                                         if pset_l else [' ']
            ps_its  = [f('{} -- {}', caps_l[i], desc_fif_val(k, ps.get(k))) for i, k in enumerate(keys_l)]  if pset_l else [' ']
            ps_vls  = [('1' if ps['_'+k]=='x' else '0')                     for    k in           keys_l ]  if pset_l else ['0']
            cnts    =[dict(           tp='lb'    ,t=5           ,l=5        ,w=245  ,cap=_('&Presets:')                     ) # &p
                     ,dict(cid='prss',tp='lbx'   ,t=5+20,h=345  ,l=5        ,w=245  ,items=ps_mns       ,act='1'
                                                                                                        ,en=(len(pset_l)>0) ) #
                      # Content
                     ,dict(           tp='lb'    ,t=5+20+345+10 ,l=5        ,w=245  ,cap=_('&Name:')                        ) # &n
                     ,dict(cid='name',tp='ed'    ,t=5+20+345+30 ,l=5        ,w=245                      ,en=(len(pset_l)>0) ) # 
                      # Acts
                     ,dict(cid='mvup',tp='bt'    ,t=435         ,l=5        ,w=120  ,cap=_('Move &up')  ,en=(len(pset_l)>1) ) # &u
                     ,dict(cid='mvdn',tp='bt'    ,t=460         ,l=5        ,w=120  ,cap=_('Move &down'),en=(len(pset_l)>1) ) # &d
                     ,dict(cid='clon',tp='bt'    ,t=435         ,l=5*2+120  ,w=120  ,cap=_('Clon&e')    ,en=(len(pset_l)>0) ) # &e
                     ,dict(cid='delt',tp='bt'    ,t=460         ,l=5*2+120  ,w=120  ,cap=_('Dele&te')   ,en=(len(pset_l)>0) ) # &t
                      #
                     ,dict(           tp='lb'    ,t=5           ,l=260      ,w=300  ,cap=_('&What to restore:')             ) # &w
                     ,dict(cid='what',tp='ch-lbx',t=5+20,h=400  ,l=260      ,w=300  ,items=ps_its       ,en=(len(pset_l)>0) )
                      #
                     ,dict(cid='!'   ,tp='bt'    ,t=435         ,l=DLG_W-5-100,w=100,cap=_('OK')        ,def_bt=True        ) # &
                     ,dict(cid='-'   ,tp='bt'    ,t=460         ,l=DLG_W-5-100,w=100,cap=_('Cancel')                        )
                     ]
            btn,vals,*_t   = dlg_wrapper(_('Config presets'), DLG_W,490, cnts     #NOTE: dlg-pres-cfg
                             ,  dict(prss=ps_ind
                                    ,name=ps.get('name', '')
                                    ,what=(-1,ps_vls)
                                    )
                             ,  focus_cid='prss')
            pass;                  #LOG and log('vals={}',vals)
            if btn is None or btn=='-': return None
            if btn=='!':
                open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
                break#while_pss
            if not pset_l: continue#while_pss
            ps['name']  = vals['name']
            ps_ind      = vals['prss']
            ps_vls      = vals['what'][1]
            for i, k in enumerate(keys_l):
                ps['_'+k]   = 'x' if ps_vls[i]=='1' else '-'
            if False:pass
            elif btn=='mvup' and ps_ind>0 \
            or   btn=='mvdn' and ps_ind<len(pset_l)-1:
                mv_ind  = ps_ind + (-1 if btn=='mvup' else 1)
                pset_l[mv_ind], \
                pset_l[ps_ind]  = pset_l[ps_ind], \
                                  pset_l[mv_ind]
                ps_ind  = mv_ind

            elif btn=='delt':
                pset_l.pop(ps_ind)
                ps_ind  = min(ps_ind, len(pset_l)-1)

            elif btn=='clon':
                ps  = pset_l[ps_ind]
                psd = {k:v for k,v in ps.items()}
                pset_l.insert(ps_ind, psd)
           #while_pss
        
    elif ps_ind==ind_save:
        # Save
        items   = [f('{} -- {}', caps_l[i], desc_l[i]) for i, k in enumerate(keys_l)]
        btn,vals,*_t   = dlg_wrapper(_('Save preset'), GAP+300+GAP,GAP+500+GAP,     #NOTE: dlg-pres-new
             [dict(           tp='lb'    ,t=GAP             ,l=GAP          ,w=300  ,cap=_('&Name:')            ) # &n
             ,dict(cid='name',tp='ed'    ,t=GAP+20          ,l=GAP          ,w=300                              ) # 
             ,dict(           tp='lb'    ,t=GAP+55          ,l=GAP          ,w=300  ,cap=_('&What to save:')    ) # &w
             ,dict(cid='what',tp='ch-lbx',t=GAP+75,h=390    ,l=GAP          ,w=300  ,items=items                )
             ,dict(cid='!'   ,tp='bt'    ,t=GAP+500-28      ,l=GAP+300-170  ,w=80   ,cap=_('OK')    ,def_bt=True) # &
             ,dict(cid='-'   ,tp='bt'    ,t=GAP+500-28      ,l=GAP+300-80   ,w=80   ,cap=_('Cancel')            )
             ],    dict(name=f(_('#{}: {} in {}'), 1+len(pset_l), desc_l[keys_l.index('incl')], desc_l[keys_l.index('fold')])
                       ,what=(0,['1']*len(keys_l))), focus_cid='name')
        pass;                  #LOG and log('vals={}',vals)
        if btn is None or btn=='-': return None
        ps_name = vals['name']
        sl,vals = vals['what']
        pass;                  #LOG and log('vals={}',vals)
        ps      = OrdDict([('name',ps_name)])
        stores['pset_nnus'] += 1
        ps['nnus'] = stores['pset_nnus']
        for i, k in enumerate(keys_l):
            if vals[i]=='1':
                ps['_'+k] = 'x'
                ps[    k] = invl_l[i]
            else:
                ps['_'+k] = '-'
        pass;                  #LOG and log('ps={}',(ps))
        pset_l += [ps]
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        app.msg_status(_('Options is saved to preset: ')+ps['name'])
        return None
    return      ouvl_l
   #def dlg_press

def dlg_help(word_h, shtp_h, cntx_h, find_h,repl_h,coun_h,cfld_h,brow_h,dept_h,pset_h,more_h,cust_h):
    RE_DOC_REF  = 'https://docs.python.org/3/library/re.html'
    TIPS_BODY   = _(r'''
• ".*" - Option "Regular Expression" allows to use in field "Find" special symbols:
    .   any character
    \d  digit character (0..9)
    \w  word-like character (digits, letters, "_")
    See full documentation by link at bottom.
 
• "aA" - Option "Case sensative"
 
• "w" - {word}
 
—————————————————————————————————————————————— 
 
• Values in fields "In file" and "Not in file" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
 
• Values in fields "In file" and "Not in file" can filter subfolder names if they start with "/".
    Example.
        In file:        /a*  *.txt
        Not in file:    /ab*
        In folder:      c:/root
        In subfolders:  All
    Search will consider all *.txt files in folder c:/root
    and in all subfolders a* except ab*.
 
• Set special value "{tags}" for field "In folder" to search in opened documents.
    Preset "In folder={tags}" helps to do this.
    To search in unsaved tabs, use mask "*" in field "In files".
 
—————————————————————————————————————————————— 
 
• Long-term searches can be interrupted by ESC.
    Search has three stages: 
        picking files, 
        finding fragments, 
        reporting.
    ESC stops any stage. When picking and finding, ESC stops only this stage, so next stage begins.
''').strip().format(word=word_h.replace('\r', '\n'), tags=IN_OPEN_FILES)
    KEYS_BODY       = _(r'''
• "Find" - {find}
 
• "Replace" - {repl}
 
• "Count" - {coun}
 
• "Current folder" - {cfld}
 
• "Browse…" - {brow}
 
• "In subfolders" - {dept}
 
• "Preset…" - {pset}
 
• "More/Less…" - {more}
 
• "Context" - {cntx}
 
• "Adjust…" - {cust}
''').strip().format(
     find=find_h.replace('\r', '\n')
    ,repl=repl_h.replace('\r', '\n')
    ,coun=coun_h.replace('\r', '\n')
    ,cfld=cfld_h.replace('\r', '\n')
    ,brow=brow_h.replace('\r', '\n')
    ,dept=dept_h.replace('\r', '\n')
    ,pset=pset_h.replace('\r', '\n')
    ,more=more_h.replace('\r', '\n')
    ,cntx=cntx_h.replace('\r', '\n')
    ,cust=cust_h.replace('\r', '\n')
    )
#• Reg.ex. tips:
#   Format for found groups in Replace: \1
    TREE_BODY   = _(r'''
Option "Tree type" - {shtp}
''').strip().format(shtp=shtp_h.replace('\r', '\n'))
    OPTS_BODY   = _(r'''
Extra options for "user.json" (needed restart after changing). 
Default values:
    // Use selection-text from current file when dialog opens
    "fif_use_selection_on_start":false,
    
    // Copy options [.*], [aA], ["w"] from CudaText dialog to plugin's dialog
    "fif_use_edfind_opt_on_start":false,
    
    // ESC stops all stages 
    "fif_esc_full_stop":false,
    
    // Close dialog if search has found matches
    "fif_hide_if_success":false,
    // Save report after filling if tab has filename
    "fif_auto_save_if_file":false,
    // Activate tab with report after filling
    "fif_focus_to_rpt":true,
    
    // Save all request details ("Find", "In folder", …) in first line of result file. 
    // The info will be used in command "Repeat search for this report-tab"
    "fif_save_request_to_rpt":false,
    
    // Length of substring (of field "Find") which appears in title of the search result
    "fif_len_target_in_title":10,
    
    // Show report if nothing found
    "fif_report_no_matches":false,
    
    // Option "Show context" appends N nearest lines to reported lines.
    // So, 2*N+1 lines will be reported for each found line.
    "fif_context_width":1,
    // Or N lines before and M lines after for each found line.
    // N or M can be set to 0
    "fif_context_width_before":1,
    "fif_context_width_after":1,
    
    // Style which marks found fragment in report
    // Full form:
    //    "fif_mark_style":{
    //      "color_back":"", 
    //      "color_font":"",
    //      "font_bold":false, 
    //      "font_italic":false,
    //      "color_border":"", 
    //      "borders":{"left":"","right":"","bottom":"","top":""}
    //    },
    //  Color values: "" - skip, "#RRGGBB" - hex-digits
    //  Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave"
    "fif_mark_style":{"borders":{"bottom":"dotted"}},
    "fif_mark_true_replace_style":{"borders":{"bottom":"solid"}},
    "fif_mark_false_replace_style":{"borders":{"bottom":"wave"},"color_border":"#777"},
    
    // Default encoding to read files
    "fif_locale_encoding":"{def_enco}",
    
    // List of lexer names for report. First available lexer will be used.
    "fif_lexers":["Search results"],
    
    // Skip too big files (0 - don't skip)
    "fif_skip_file_size_more_Kb":0,
    
    // Size of buffer (at file start) to detect binary files
    "fif_read_head_size(bytes)":1024,
''').strip().replace('{def_enco}', DEF_LOC_ENCO)
#   // Before append result fold all previous ones
#   "fif_fold_prev_res":false,
#   
    DW, DH      = 800, 600
#   vals_hlp    = dict(htxt=TIPS_BODY)
    vals_hlp    = dict(htxt=TIPS_BODY
                      ,tips=True
                      ,keys=False
                      ,tree=False
                      ,opts=False
                      )
    hints_png   = os.path.dirname(__file__)+os.sep+r'images/fif-hints_770x400.PNG'
    while_hlp   = True
    while while_hlp:
        btn_hlp,    \
        vals_hlp,   \
        *_t         = dlg_wrapper(_('Help for "Find in Files"'), GAP+DW+GAP,GAP+DH+GAP,     #NOTE: dlg-hlp
            ([]
#           +[dict(cid='htxt',tp='me'    ,t=GAP ,h=DH-28,l=GAP          ,w=DW   ,props='1,1,1'                                  )] #  ro,mono,border
           +([dict(cid='htxt',tp='me'    ,t=GAP ,h=DH-28,l=GAP          ,w=DW               ,ro_mono_brd='1,1,1'                )] # 
           if not vals_hlp['keys'] else []
            +[dict(           tp='im'    ,t=GAP         ,h=400          ,l=GAP+15   ,w=770  ,items=hints_png                    )]
            +[dict(cid='htxt',tp='me'    ,t=GAP+400+GAP ,h=DH-28-400-GAP,l=GAP      ,w=DW   ,ro_mono_brd='1,1,1'                )] # 
           )

           +([] if not vals_hlp['tips'] else []
            +[dict(           tp='ln-lb' ,tid='-'       ,l=GAP          ,w=180  ,cap=_('Reg.ex. on python.org'),url=RE_DOC_REF  )]
           )

           +([] if not vals_hlp['opts'] else []
#           +[dict(cid='open',tp='bt'    ,tid='-'       ,l=GAP          ,w=150  ,cap=_('O&pen user.json')                       )] # &p
#           +[dict(cid='prps',tp='bt'    ,tid='-'       ,l=GAP+150+5    ,w=130  ,cap=_('&Edit options…')                        )] # &e
            +[dict(cid='prps',tp='bt'    ,tid='-'       ,l=GAP          ,w=130  ,cap=_('&Edit options…')                        )] # &e
           )
            +[dict(cid='tips',tp='ch-bt',t=GAP+DH-23    ,l=GAP+DW-425   ,w=80   ,cap=_('T&ips')                 ,act='1'        )] # &i
            +[dict(cid='keys',tp='ch-bt',t=GAP+DH-23    ,l=GAP+DW-340   ,w=80   ,cap=_('&Keys')                 ,act='1'        )] # &k
            +[dict(cid='tree',tp='ch-bt',t=GAP+DH-23    ,l=GAP+DW-255   ,w=80   ,cap=_('&Tree')                 ,act='1'        )] # &t
            +[dict(cid='opts',tp='ch-bt',t=GAP+DH-23    ,l=GAP+DW-170   ,w=80   ,cap=_('&Opts')                 ,act='1'        )] # &o
            +[dict(cid='-'   ,tp='bt'   ,t=GAP+DH-23    ,l=GAP+DW-80    ,w=80   ,cap=_('&Close')                                )] # &c
            ), vals_hlp, focus_cid='htxt')
        pass;                  #LOG and log('vals_hlp={}',vals_hlp)
        if btn_hlp is None or btn_hlp=='-': break#while_hlp
        if False:pass
        elif btn_hlp=='tips':vals_hlp["htxt"]=TIPS_BODY; vals_hlp["tips"]=True; vals_hlp["keys"]=False;vals_hlp["tree"]=False;vals_hlp["opts"]=False
        elif btn_hlp=='keys':vals_hlp["htxt"]=KEYS_BODY; vals_hlp["tips"]=False;vals_hlp["keys"]=True; vals_hlp["tree"]=False;vals_hlp["opts"]=False
        elif btn_hlp=='tree':vals_hlp["htxt"]=TREE_BODY; vals_hlp["tips"]=False;vals_hlp["keys"]=False;vals_hlp["tree"]=True; vals_hlp["opts"]=False
        elif btn_hlp=='opts':vals_hlp["htxt"]=OPTS_BODY; vals_hlp["tips"]=False;vals_hlp["keys"]=False;vals_hlp["tree"]=False;vals_hlp["opts"]=True
        elif btn_hlp=='open':
            usr_json    = CdSw.file_open(CdSw.get_setting_dir()+os.sep+'user.json')
        elif btn_hlp=='prps':
            dlg_fif_opts()
       #while_hlp
   #def dlg_help

def dlg_fif(what='', opts={}):
    stores  = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
              OrdDict()
    
    mask_h  = _('Space-separated file or folder masks.'
                '\rFolder mask starts with "/".'
                '\rDouble-quote mask, which needs space-char.'
                '\rUse ? for any character and * for any fragment.'
                '\rNote: "*" matchs all names, "*.*" doesnt match all.')
    reex_h  = _('Regular expression')
    case_h  = _('Case sensative')
    word_h  = _('Option "Whole words". It is ignored when:'
                '\r    Regular expression (".*") is turned on,'
                '\r    "Find" contains not only letters, digits and "_".'
                )
    brow_h  = _('Choose folder.'
                '\rShift+Click - Choose file to find in it.'
                )
    dept_h  = _('Which subfolders will be used to search.'
                '\rAlt+L - Apply "All".'
                '\rAlt+Y - Apply "In folder only".'
                )
    cfld_h  = _('Use folder of current file.'
                '\rShift+Click - Prepare search in the current file.'
                '\rCtrl+Click  - Prepare search in all tabs.'
                '\rCtrl+Shift+Click  - Prepare search in the current tab.'
                )
    more_h  = _('Show/Hide advanced options'
                '\rCtrl+Click  - Show/Hide "Not in files".'
                '\rShift+Click - Show/Hide "Replace".'
                '\rCtrl+Shift+Click - Show/Hide "Not in files" and "Replace".'
                )
    cust_h  = _('Change dialog layout.'
                '\rCtrl+Click  - Adjust vertical alignments'
                '\rShift+Click   - Set wider width for fields What/In files…'
                '\rCtrl+Shift+Click - Set default widths for all fields.'
                )
    frst_h  = _('M[, F]'
                '\rStop after M fragments will be found.'
                '\rSearch only inside F first proper files.'
                '\r    Note: If Sort is on then steps are'
                '\r     - Collect all proper files'
                '\r     - Sort the list'
                '\r     - Use first F files to search'
                )
    shtp_h  = f(_(  'Format of the reported tree structure.'
                '\rCompact - report all found line with full file info:'
                '\r    path(r[:c:l]):line'
                '\r    path/(r[:c:l]):line'
                '\r  Tree schemes'
                '\r    +Search for "*"'
                '\r      <full_path(row[:col:len])>: line with ALL marked fragments'
                '\r    +Search for "*"'
                '\r      <full_path>: #count'
                '\r         <(row[:col:len])>: line with ALL marked fragments'
                '\rSparse - report separated folders and fragments:'
                '\r    dir/file(r[:c:l]):line'
                '\r    dir/file/(r[:c:l]):line'
                '\r  Tree schemes'
                '\r    +Search for "*"'
                '\r      <root>: #count'
                '\r        <dir>: #count'
                '\r          <file.ext(row[:col:len])>: line with ONE marked fragment'
                '\r    +Search for "*"'
                '\r      <root>: #count'
                '\r        <dir>: #count'
                '\r          <file.ext>: #count'
                '\r            <(row[:col:len])>: line with ONE marked fragment'
                '\rFor '
                '\r  sorted files'
                '\rand'
                '\r  In folder={}'
                '\ronly Compact options are used.'
               ),IN_OPEN_FILES)
    cntx_h  = _('Show result line and both its nearest lines, above and below result'
                '\rCtrl+Click  - Set count of above and below lines.')
    algn_h  = _("Align columns (filenames/numbers) by widest cell width")
    find_h  = f(_('Start search.'
                '\rShift+Click  - Put report to new tab.'
                '\r   It is like pressing Find with option "Show in: {}".'
                '\rCtrl+Click  - Append result to existing report.'
                '\r   It is like pressing Find with option "[x]Append results".'
                ), TOTB_NEW_TAB)
    repl_h  = _('Start search and replacement.'
                '\rShift+Click  - Run without question "Do you want to replace…?"'
                )
    coun_h  = f(_('Count matches only.'
                '\r   It is like pressing Find with option Collect: "{}".'
                '\rShift+Click  - Find file names.'
                '\r   It is like pressing Find with option Collect: "{}".'
                ), CLLC_COUNT, CLLC_FNAME)
    pset_h  = _('Save options for future. Restore saved options.'
                '\rShift+Click  - Show preset list in applying history order.'
                '\rCtrl+Click   - Apply last used preset.'
                '\rAlt+1 - Apply first preset.'
                '\rAlt+2 - Apply second preset.'
                '\rAlt+3 - Apply third preset.'
                )
    
    enco_h  = f(_('In which encodings try to read files.'
                '\rFirst suitable will be used.'
                '\r"{}" is slow.'
                '\r '
                '\rDefault encoding: {}'), ENCO_DETD, loc_enco)
    
    W32     = 'win'==get_desktop_environment()
    EG0,EG1,EG2,EG3,EG4,EG5,EG6,EG7,EG8,EG9,EG10 = [0]*11 if W32 else [5*i for i in range(11)]
    DLG_W0, \
    DLG_H0  = (700, 335 + EG1 + EG10)
    DEF_WD_TXTS = 300
    DEF_WD_BTNS = 100

    what_s  = what if what else ed.get_text_sel() if USE_SEL_ON_START else ''
    what_s  = what_s.splitlines()[0] if what_s else ''
    repl_s  = opts.get('repl', '')
    reex01  = opts.get('reex', stores.get('reex', '0'))
    case01  = opts.get('case', stores.get('case', '0'))
    word01  = opts.get('word', stores.get('word', '0'))
    if USE_EDFIND_OPS:
        ed_opt  = CdSw.app_proc(CdSw.PROC_GET_FIND_OPTIONS, '')
#       ed_opt  = app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
        # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrap
        reex01  = '1' if 'r' in ed_opt else '0'
        case01  = '1' if 'c' in ed_opt else '0'
        word01  = '1' if 'w' in ed_opt else '0'
    incl_s  = opts.get('incl', stores.get('incl',  [''])[0])
    excl_s  = opts.get('excl', stores.get('excl',  [''])[0])
    fold_s  = opts.get('fold', stores.get('fold',  [''])[0])
    dept_n  = opts.get('dept', stores.get('dept',  0)-1)+1
    cllc_s  = opts.get('cllc', stores.get('cllc', '0'))
    join_s  = opts.get('join', stores.get('join', '0'))
    totb_s  = opts.get('totb', stores.get('totb', '0'));    totb_s = '1' if totb_s=='0' else totb_s
#   totb_s  = opts.get('totb', stores.get('totb', '0'));    totb_s = str(min(1, int(totb_s)))
    shtp_s  = opts.get('shtp', stores.get('shtp', '0'))
    cntx_s  = opts.get('cntx', stores.get('cntx', '0'))
    algn_s  = opts.get('algn', stores.get('algn', '0'))
    skip_s  = opts.get('skip', stores.get('skip', '0'))
    sort_s  = opts.get('sort', stores.get('sort', '0'))
    frst_s  = opts.get('frst', stores.get('frst', '0'))
    enco_s  = opts.get('enco', stores.get('enco', '0'))

    def add_to_history(val:str, lst:list, max_len:int, unicase=True)->list:
        """ Add/Move val to list head. """
        pass;                  #LOG and log('val, lst={}',(val, lst))
        lst_u = [ s.upper() for s in lst] if unicase else lst
        val_u = val.upper()               if unicase else val
        if val_u in lst_u:
            if 0 == lst_u.index(val_u):   return lst
            del lst[lst_u.index(val_u)]
        lst.insert(0, val)
        pass;                  #LOG and log('lst={}',lst)
        if len(lst)>max_len:
            del lst[max_len:]
        pass;                  #LOG and log('lst={}',lst)
        return lst
       #def add_to_history
    def get_live_fiftabs(_fxs)->list:
        rsp = []
        for h in app.ed_handles():
            try_ed  = app.Editor(h)
            try_fn  = try_ed.get_filename()
            if try_fn in _fxs:
                continue
            tag     = try_ed.get_prop(app.PROP_TAG)
            lxr     = try_ed.get_prop(app.PROP_LEXER_FILE)
            if False:pass
            elif lxr.upper() in lexers_l:
                rsp+= ['tab:'+try_ed.get_prop(app.PROP_TAB_TITLE)]
            elif tag.startswith('FiF'):
                rsp+= ['tab:'+try_ed.get_prop(app.PROP_TAB_TITLE)]
        return rsp
       #def get_live_fiftabs
    
    focused = 'what'
    while_fif   = True
    while while_fif:
        what_l  = [s for s in stores.get('what', []) if s ]
        incl_l  = [s for s in stores.get('incl', []) if s ]
        excl_l  = [s for s in stores.get('excl', []) if s ]
        fold_l  = [s for s in stores.get('fold', []) if s ]
        repl_l  = [s for s in stores.get('repl', []) if s ]
        fxs     = stores.get('tofx', [])
        tofx_l  = [f('file:{1}'+' '*100+'{0}', *os.path.split(fx)) for fx in fxs if os.path.isfile(fx) ]    # ' '*100 to hide folder in list-/combo-boxes
        totb_l  = [TOTB_NEW_TAB, TOTB_USED_TAB] + [_('[Clear fixed files]'), _('[Add fixed file]')] + tofx_l + get_live_fiftabs(fxs)
        
        wo_excl = stores.get('wo_excl', True)
        wo_repl = stores.get('wo_repl', True)
        wo_adva = stores.get('wo_adva', True)
        ad01    = 0 if wo_adva else 1
        c_more  = _('Mor&e >>') if wo_adva else _('L&ess <<')
        txt_w   = stores.get('wd_txts', DEF_WD_TXTS)
        btn_w   = stores.get('wd_btns', DEF_WD_BTNS)
        lbl_l   = GAP+38*3+GAP+25
        cmb_l   = lbl_l+100
        tl2_l   = lbl_l+220-85
        tbn_l   = cmb_l+txt_w+GAP
        gap1    = (GAP- 28 if wo_repl else GAP)
        gap2    = (GAP- 28 if wo_excl else GAP)+gap1 -GAP
        gap3    = (GAP-132 if wo_adva else GAP)+gap2 -GAP
        dlg_w,\
        dlg_h   = (tbn_l+btn_w+GAP, DLG_H0+gap3-(30+EG4 if wo_adva else 0))
        #NOTE: fif-cnts
        cnts    = ([]                                                                                                              # gmqvz
                 +[dict(cid='prs1',tp='bt'      ,tid='incl'     ,l=1000     ,w=0        ,cap=_('&1')                            )] # &1
                 +[dict(cid='prs2',tp='bt'      ,tid='incl'     ,l=1000     ,w=0        ,cap=_('&2')                            )] # &2
                 +[dict(cid='prs3',tp='bt'      ,tid='incl'     ,l=1000     ,w=0        ,cap=_('&3')                            )] # &3
                 +[dict(cid='pres',tp='bt'      ,tid='incl'     ,l=GAP      ,w=38*3*ad01,cap=_('Pre&sets…')         ,hint=pset_h)] # &s
                 +[dict(cid='reex',tp='ch-bt'   ,tid='what'     ,l=GAP+38*0 ,w=38       ,cap='&.*'         ,act='1' ,hint=reex_h)] # &.
                 +[dict(cid='case',tp='ch-bt'   ,tid='what'     ,l=GAP+38*1 ,w=38       ,cap='&aA'         ,act='1' ,hint=case_h)] # &a
                 +[dict(cid='word',tp='ch-bt'   ,tid='what'     ,l=GAP+38*2 ,w=38       ,cap='"&w"'        ,act='1' ,hint=word_h)] # &w
                 +[dict(           tp='lb'      ,tid='what'     ,l=lbl_l    ,r=cmb_l-5  ,cap='>'+_('*&Find what:')              )] # &f
                 +[dict(cid='what',tp='cb'      ,t=GAP          ,l=cmb_l    ,w=txt_w    ,items=what_l                           )] # 
                
                +([] if wo_repl else []                         
                 +[dict(           tp='lb'      ,tid='repl'     ,l=lbl_l    ,r=cmb_l-5  ,cap='>'+_('&Replace with:')            )] # &r
                 +[dict(cid='repl',tp='cb'      ,t=GAP+  28+EG1 ,l=cmb_l    ,w=txt_w    ,items=repl_l                           )] # 
                )                                               
                                                
                 +[dict(           tp='lb'      ,tid='incl'     ,l=lbl_l    ,r=cmb_l-5  ,cap='>'+_('*&In files:')   ,hint=mask_h)] # &i
                 +[dict(cid='incl',tp='cb'      ,t=gap1+ 56+EG2 ,l=cmb_l    ,w=txt_w    ,items=incl_l                           )] # 
                +([] if wo_excl else []                         
                 +[dict(           tp='lb'      ,tid='excl'     ,l=lbl_l    ,r=cmb_l-5  ,cap='>'+_('Not in files:') ,hint=mask_h)] # 
                 +[dict(cid='excl',tp='cb'      ,t=gap1+ 84+EG3 ,l=cmb_l    ,w=txt_w    ,items=excl_l                           )] # 
                )                                               
                 +[dict(           tp='lb'      ,tid='fold'     ,l=lbl_l    ,r=cmb_l-5  ,cap='>'+_('*I&n folder:')              )] # &n
                 +[dict(cid='fold',tp='cb'      ,t=gap2+112+EG4 ,l=cmb_l    ,w=txt_w    ,items=fold_l                           )] # 
                 +[dict(cid='brow',tp='bt'      ,tid='fold'     ,l=tbn_l    ,w=btn_w    ,cap=_('&Browse…')          ,hint=brow_h)] # &b
                 +[dict(           tp='lb'      ,tid='dept'     ,l=lbl_l    ,w=100  -5  ,cap='>'+_('In s&ubfolders:'),hint=dept_h)] # &u
                 +[dict(cid='dept',tp='cb-ro'   ,t=gap2+140+EG5 ,l=cmb_l    ,w=135      ,items=dept_l                           )] # 
                 +[dict(cid='depa',tp='bt'      ,tid='dept'     ,l=1000     ,w=0        ,cap=_('&l')                            )] # &l
                 +[dict(cid='depo',tp='bt'      ,tid='dept'     ,l=1000     ,w=0        ,cap=_('&y')                            )] # &y
                 +[dict(cid='cfld',tp='bt'      ,tid='fold'     ,l=GAP      ,w=38*3     ,cap=_('&Current folder')   ,hint=cfld_h)] # &c
                 +[dict(cid='more',tp='bt'      ,tid='dept'     ,l=GAP      ,w=38*3     ,cap=c_more                 ,hint=more_h)] # &e
                
                +([] if wo_adva else  []                        
                 +[dict(           tp='--'      ,t=gap2+163+EG5                                                                 )] # 
                 +[dict(           tp='lb'      ,t=gap2+175+EG5 ,l=GAP+80   ,r=cmb_l    ,cap=_('Adv. report options')           )] # 
#                +[dict(           tp='lb'      ,tid='skip'     ,l=GAP      ,r=80       ,cap='>'+_('Co&llect:')                 )] # &l
#                +[dict(cid='cllc',tp='cb-ro'   ,tid='skip'     ,l=GAP+80   ,r=cmb_l    ,items=cllc_l                           )] # 
                 +[dict(cid='cllc',tp='cb-ro'   ,t=0            ,l=1000     ,w=0        ,items=cllc_l                           )] # 
                 +[dict(           tp='lb'      ,tid='skip'     ,l=GAP      ,r=80       ,cap='>'+_('Show in&:')                 )] # &:
                 +[dict(cid='totb',tp='cb-ro'   ,tid='skip'     ,l=GAP+80   ,r=cmb_l    ,items=totb_l       ,act='1'            )] # 
                 +[dict(cid='join',tp='ch'      ,tid='sort'     ,l=GAP+80   ,w=150      ,cap=_('Appen&d results')               )] # &d
                 +[dict(           tp='lb'      ,tid='frst'     ,l=GAP      ,r=80       ,cap='>'+_('Tree type &/:') ,hint=shtp_h)] # &/
                 +[dict(cid='shtp',tp='cb-ro'   ,tid='frst'     ,l=GAP+80   ,r=cmb_l    ,items=shtp_l                           )] # 
                 +[dict(cid='algn',tp='ch'      ,tid='enco'     ,l=GAP+80   ,w=100      ,cap=_('Align &|')          ,hint=algn_h)] # &|
                 +[dict(cid='cntx',tp='ch'      ,tid='enco'     ,l=GAP+170  ,w=150      ,cap=_('Conte&xt')  ,act='1',hint=cntx_h)] # &x
                                                
                 +[dict(           tp='lb'      ,t=gap2+175+EG5 ,l=tl2_l+100,r=tbn_l-GAP,cap=_('Adv. search options')           )] # 
                 +[dict(           tp='lb'      ,tid='skip'     ,l=tl2_l    ,w=100-5    ,cap='>'+_('S&kip files:')              )] # &k
                 +[dict(cid='skip',tp='cb-ro'   ,t=gap2+195+EG6 ,l=tl2_l+100,r=tbn_l-GAP,items=skip_l                           )] # 
                 +[dict(           tp='lb'      ,tid='sort'     ,l=tl2_l    ,w=100-5    ,cap='>'+_('S&ort file list:')          )] # &o
                 +[dict(cid='sort',tp='cb-ro'   ,t=gap2+222+EG7 ,l=tl2_l+100,r=tbn_l-GAP,items=sort_l                           )] # 
                 +[dict(           tp='lb'      ,tid='frst'     ,l=tl2_l    ,w=100-5    ,cap='>'+_('Firsts (&0=all):'),hint=frst_h)] # &0
                 +[dict(cid='frst',tp='ed'      ,t=gap2+249+EG8 ,l=tl2_l+100,r=tbn_l-GAP                                        )] # 
                 +[dict(           tp='lb'      ,tid='enco'     ,l=tl2_l    ,w=100-5    ,cap='>'+_('Encodings &\\:'),hint=enco_h)] # \
                 +[dict(cid='enco',tp='cb-ro'   ,t=gap2+276+EG9 ,l=tl2_l+100,r=tbn_l-GAP,items=enco_l                           )] # 
                )                                                                                                               
                 +[dict(cid='!fnd',tp='bt'      ,tid='what'     ,l=tbn_l    ,w=btn_w    ,cap=_('Find'),def_bt=True  ,hint=find_h)] # 
                +([] if wo_repl else []                         
                 +[dict(cid='!rep',tp='bt'      ,tid='repl'     ,l=tbn_l    ,w=btn_w    ,cap=_('Re&place')          ,hint=repl_h)] # &p
                )                                               
                +([]                        
                 +[dict(cid='!cnt',tp='bt'      ,tid='incl'     ,l=tbn_l    ,w=btn_w*ad01   ,cap=_('Coun&t')        ,hint=coun_h)] # &t
                 +[dict(cid='cust',tp='bt'      ,tid='dept'     ,l=tbn_l    ,w=btn_w*ad01   ,cap=_('Ad&just…')      ,hint=cust_h)] # &j
                 +[dict(cid='help',tp='bt'  ,t=dlg_h-GAP-25-EG1 ,l=GAP      ,w=38*3*ad01    ,cap=_('&Help')                     )] # &h
#                +[dict(cid='help',tp='bt'  ,t=dlg_h-GAP-25-EG1 ,l=tbn_l-100-GAP,w=100*ad01 ,cap=_('&Help')                     )] # &h
                 +[dict(cid='-'   ,tp='bt'      ,tid='help'     ,l=tbn_l    ,w=btn_w        ,cap=_('Close')                     )] # 
                if not wo_adva else []
                 +[dict(cid='-'   ,tp='bt'      ,tid='dept'     ,l=tbn_l    ,w=btn_w        ,cap=_('Close')                     )] # 
                )                                                                                                               
                )
        caps    =   {cnt['cid']:cnt['cap']          for cnt         in cnts
                    if cnt['tp'] in ('bt', 'ch')            and 'cap' in cnt}
        caps.update({cnt['cid']:cnts[icnt-1]['cap'] for (icnt,cnt)  in enumerate(cnts)
                    if cnt['tp'] in ('cb', 'cb-ro', 'ed')   and 'cap' in cnts[icnt-1]})
        caps.update({'excl':_('Not in files:')
                    ,'repl':_('&Replace with:')
                    ,'!rep':_('Re&place')
                    })
        caps    = {k:v.strip(' :*|\\/>*').replace('&', '') for (k,v) in caps.items()}
        pass;                  #LOG and log('caps=¶{}',pf(caps))
        pass;                  #LOG and log('cnts=¶{}',pf(cnts))
        pass;                  #LOG and log('gap12={} cnts=¶{}',(gap1,gap2),pf([dict(cid=d['cid'], t=d['t']) for d in cnts if 'cid' in d and 't' in d]))
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
                             ,totb=totb_s
                             ,shtp=shtp_s
                             ,cntx=cntx_s
                             ,algn=algn_s
                             ,skip=skip_s
                             ,sort=sort_s
                             ,frst=frst_s
                             ,enco=enco_s
                            ))
        pass;                  #LOG and log('vals={}',pf(vals))
        btn,vals,fid,chds   = dlg_wrapper(f(_('Find in Files ({}) {}'), VERSION_V
                                           ,'' if not wo_adva else  ' [' + (''
                                                            +   (_(shtp_l[int(shtp_s)]+', ')                        )
                                                            +   (_('Append, ')                if join_s=='1' else '')
                                                            +   (_('Context, ')               if cntx_s=='1' else '')
                                                            +   (_('Sorted, ')                if sort_s!='0' else '')
                                                            +   (_('First ')+frst_s+', '      if frst_s!='0' else '')
                                                            ).rstrip(', ') + ']'
                                           )
                            , dlg_w, dlg_h, cnts, vals
                            , focus_cid=focused)     #NOTE: dlg-fif
        if btn is None or btn=='-': return None
        scam        = app.app_proc(app.PROC_GET_KEYSTATE, '')
        btn_p       = btn
        btn_m       = scam + '/' + btn if scam and scam!='a' else btn   # smth == a/smth
        pass;                  #LOG and log('btn_p, scam, btn_m={}',(btn_p, scam, btn_m))
        focused     = 'what' \
                        if 1==len(chds) and chds[0] in ('reex', 'case', 'word') else \
                      chds[0] \
                        if 1==len(chds) else \
                      focused
        pass;                  #LOG and log('vals={}',pf(vals))
        reex01      = vals['reex']
        case01      = vals['case']
        word01      = vals['word']
        what_s      = vals['what']
        incl_s      = vals['incl']
        if not wo_excl:     
            excl_s  = vals['excl']
        else:
            excl_s  = ''
        fold_s      = vals['fold']
        dept_n      = vals['dept']
        if not wo_repl:     
            repl_s  = vals['repl']
        if not wo_adva:     
            cllc_s  = vals['cllc']
            join_s  = vals['join']
            totb_s  = vals['totb']
            shtp_s  = vals['shtp']
            cntx_s  = vals['cntx']
            algn_s  = vals['algn']
            skip_s  = vals['skip']
            sort_s  = vals['sort']
            frst_s  = vals['frst']
            enco_s  = vals['enco']
        pass;                  #LOG and log('what_s,repl_s,incl_s,fold_s={}',(what_s,repl_s,incl_s,fold_s))
        
        # Save user data
        stores['reex']  = reex01
        stores['case']  = case01
        stores['word']  = word01
        stores['what']  = add_to_history(what_s, stores.get('what', []), MAX_HIST, unicase=False)
        stores['incl']  = add_to_history(incl_s, stores.get('incl', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['excl']  = add_to_history(excl_s, stores.get('excl', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['fold']  = add_to_history(fold_s, stores.get('fold', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['dept']  = dept_n
        stores['repl']  = add_to_history(repl_s, stores.get('repl', []), MAX_HIST, unicase=False)
        stores['cllc']  = cllc_s
        stores['join']  = join_s
        totb_s_pre      = stores.get('totb', '1')
        stores['totb']  = '1' if totb_s=='0' else totb_s
#       stores['totb']  = str(min(1, int(totb_s)))
        stores['shtp']  = shtp_s
        stores['cntx']  = cntx_s
        stores['algn']  = algn_s
        stores['skip']  = skip_s
        stores['sort']  = sort_s
        stores['frst']  = frst_s
        stores['enco']  = enco_s
        stores.pop('toed',None)     # rudiment
        stores.pop('reed',None)     # rudiment
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        
        # Cmds without data: help, custom
        if btn_p=='help':
            dlg_help(word_h, shtp_h, cntx_h, find_h,repl_h,coun_h,cfld_h,brow_h,dept_h,pset_h,more_h,cust_h)
            continue#while_fif
        
#       if btn_p=='more':
        if btn_m=='more':
            stores['wo_adva']       = not stores.get('wo_adva', True)
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif
        if btn_m=='c/more':     # [Ctrl+]More       = show/hide excl
            stores['wo_excl']   = not stores['wo_excl']
        if btn_m=='s/more':     # [Shift+]More      = show/hide repl
            stores['wo_repl']   = not stores['wo_repl']
        if btn_m=='sc/more':    # [Ctrl+Shift+]More = show/hide excl+repl
            stores['wo_excl']   = not stores['wo_excl']
            stores['wo_repl']   = not stores['wo_repl']

        if btn_m=='sc/cust':    # [Ctrl+Shift+]Adjust    = def widths
            stores['wd_txts']   = DEF_WD_TXTS
            stores['wd_btns']   = DEF_WD_BTNS
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif
        if btn_m=='s/cust':     # [Shift+]Adjust  = wider eds
            stores['wd_txts']   = min(800, 25 + stores.get('wd_txts', DEF_WD_TXTS))
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif
        if btn_m=='c/cust':     # [Ctrl+]Adjust  = dlg_valign_consts
            dlg_valign_consts()
            continue#while_fif
#       if btn_m=='c/cust':     # [Ctrl+]Adjust  = wider bts
#           stores['wd_btns']   = min(200, 10 + stores.get('wd_btns', DEF_WD_BTNS))
#           open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
#           continue#while_fif
        if btn_m=='cust':
            wdtx_c  = f(_('Width of main &editors ("{}", "{}"):'), caps['what'], caps['incl'])
            wdbt_c  = f(_('Width of main &buttons ("{}", "{}"):'), caps['!fnd'], caps['brow'])
            shex_c  = f(_('Show "&{}"')                          , caps['excl'])
            shre_c  = f(_('Show "&{}" and "{}"')                 , caps['repl'], caps['!rep'])
            aid,vals,*_t   = dlg_wrapper(_('Adjust dialog controls'), GAP+370+GAP,GAP+145+GAP,     #NOTE: dlg-cust
                 [dict(           tp='lb'    ,tid='wdtx'        ,l=GAP          ,w=300  ,cap=wdtx_c                                     ) # &e
                 ,dict(cid='wdtx',tp='sp-ed' ,t=GAP             ,l=GAP+300      ,w=70   ,props=f('{},{},25',DEF_WD_TXTS,2*DEF_WD_TXTS)  ) # 
                 ,dict(           tp='lb'    ,tid='wdbt'        ,l=GAP          ,w=300  ,cap=wdbt_c                                     ) # &b
                 ,dict(cid='wdbt',tp='sp-ed' ,t=GAP+30          ,l=GAP+300      ,w=70   ,props=f('{},{},10',DEF_WD_BTNS,2*DEF_WD_BTNS)  ) # 
                 ,dict(cid='shex',tp='ch'    ,t=GAP+65          ,l=GAP          ,w=150  ,cap=shex_c                                     ) # &n
                 ,dict(cid='shre',tp='ch'    ,t=GAP+90          ,l=GAP          ,w=150  ,cap=shre_c                                     ) # &r
                 ,dict(cid='!'   ,tp='bt'    ,t=GAP+145-28      ,l=GAP+370-170  ,w=80   ,cap=_('OK')    ,def_bt=True                    ) # 
                 ,dict(cid='-'   ,tp='bt'    ,t=GAP+145-28      ,l=GAP+370-80   ,w=80   ,cap=_('Cancel')                                )
                 ],    dict(wdtx=    stores.get('wd_txts', DEF_WD_TXTS)
                           ,wdbt=    stores.get('wd_btns', DEF_WD_BTNS)
                           ,shex=not stores.get('wo_excl', True)
                           ,shre=not stores.get('wo_repl', True)
                           ), focus_cid='wdtx')
            pass;              #LOG and log('vals={}',vals)
            if aid is None or aid=='-': continue#while_fif
            stores['wd_txts']   = max(DEF_WD_TXTS, min(2*DEF_WD_TXTS, vals['wdtx']))
            stores['wd_btns']   = max(DEF_WD_BTNS, min(2*DEF_WD_BTNS, vals['wdbt']))
            stores['wo_excl']   = not               vals['shex']
            stores['wo_repl']   = not               vals['shre']
            open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif
        
        # Cmds with data
        if btn_p in ('depa', 'depo'):
            dept_n  = 0 if btn_p=='depa' else 1
        
        if btn_p in ('prs1', 'prs2', 'prs3') \
        or btn_m=='c/pres': # Ctrl++Preset - Apply last used preset
            pset_l  = stores.setdefault('pset', [])
            if not pset_l:
                continue#while_fif
            ps  = sorted(pset_l, key=lambda ps: ps.get('nnus', 0), reverse=True)[0] \
                    if btn_m=='c/pres'                  else \
                  pset_l[0] \
                    if btn_p=='prs1'                    else \
                  pset_l[1] \
                    if btn_p=='prs2' and len(pset_l)>1  else \
                  pset_l[2] \
                    if btn_p=='prs3' and len(pset_l)>2  else \
                  None
            if not ps:
                continue#while_fif
            reex01  = ps['reex'] if ps.get('_reex', '')=='x' else reex01
            case01  = ps['case'] if ps.get('_case', '')=='x' else case01
            word01  = ps['word'] if ps.get('_word', '')=='x' else word01
            incl_s  = ps['incl'] if ps.get('_incl', '')=='x' else incl_s
            excl_s  = ps['excl'] if ps.get('_excl', '')=='x' else excl_s
            fold_s  = ps['fold'] if ps.get('_fold', '')=='x' else fold_s
            dept_n  = ps['dept'] if ps.get('_dept', '')=='x' else dept_n
            skip_s  = ps['skip'] if ps.get('_skip', '')=='x' else skip_s
            sort_s  = ps['sort'] if ps.get('_sort', '')=='x' else sort_s
            frst_s  = ps['frst'] if ps.get('_frst', '')=='x' else frst_s
            enco_s  = ps['enco'] if ps.get('_enco', '')=='x' else enco_s
            cllc_s  = ps['cllc'] if ps.get('_cllc', '')=='x' else cllc_s
            totb_s  = ps['totb'] if ps.get('_totb', '')=='x' else totb_s
            join_s  = ps['join'] if ps.get('_join', '')=='x' else join_s
            shtp_s  = ps['shtp'] if ps.get('_shtp', '')=='x' else shtp_s
            algn_s  = ps['algn'] if ps.get('_algn', '')=='x' else algn_s
            cntx_s  = ps['cntx'] if ps.get('_cntx', '')=='x' else cntx_s
            app.msg_status(_('Options is restored from preset: ')+ps['name'])

        if btn_m=='pres' \
        or btn_m=='s/pres': # Shift+Preset - Show list in history order
            onof    = {'0':'Off', '1':'On'}
            totb_i  = int(totb_s)
            totb_i  = totb_i if 0<totb_i<4+len(stores.get('tofx', [])) else 1   # "tab:" skiped
            totb_v  = totb_l[totb_i]
            ans     = dlg_press(stores, btn_m=='s/pres',
                       (reex01,case01,word01,
                        incl_s,excl_s,
                        fold_s,dept_n,
                        skip_s,sort_s,frst_s,enco_s,
                        cllc_s,totb_v,join_s,shtp_s,algn_s,cntx_s),
                       (onof[reex01],onof[case01],onof[word01],
#                      ('On' if reex01=='1' else 'Off','On' if case01=='1' else 'Off','On' if word01=='1' else 'Off',
                        '"'+incl_s+'"','"'+excl_s+'"',
                        '"'+fold_s+'"',dept_l[dept_n],
                        skip_l[int(skip_s)],sort_l[int(sort_s)],frst_s,enco_l[int(enco_s)],
                        cllc_l[int(cllc_s)],totb_v,onof[join_s],shtp_l[int(shtp_s)],onof[algn_s],onof[cntx_s])
#                       cllc_l[int(cllc_s)],totb_l[int(totb_s)],'On' if join_s=='1' else 'Off',shtp_l[int(shtp_s)],'On' if algn_s=='1' else 'Off','On' if cntx_s=='1' else 'Off')
                        )
            if ans is None:
                continue#while_fif
            (           reex01,case01,word01,
                        incl_s,excl_s,
                        fold_s,dept_n,
                        skip_s,sort_s,frst_s,enco_s,
                        cllc_s,totb_v,join_s,shtp_s,algn_s,cntx_s)  = ans
            totb_s  = str(totb_l.index(totb_v))     if totb_v in totb_l         else \
                      totb_v                        if totb_v in ('0', '1')     else \
                      '1'
#           totb_s  = totb_s if int(totb_s)<4+len(stores.get('tofx', [])) else '1'
                
        if False:pass
        elif btn_m=='brow':     # BroDir
            path    = CdSw.dlg_dir(os.path.expanduser(fold_s))
#           path    = app.dlg_dir(os.path.expanduser(fold_s))
            if not path: continue#while_fif
            fold_s  = path
            fold_s  = fold_s.replace(os.path.expanduser('~'), '~', 1) if fold_s.startswith(os.path.expanduser('~')) else fold_s
            focused = 'fold'
        elif btn_m=='s/brow':   # [Shift+]BroDir = BroFile
            fn      = app.dlg_file(True, '', os.path.expanduser(fold_s), '')
            if not fn or not os.path.isfile(fn):    continue#while_fif
            incl_s  = os.path.basename(fn)
            fold_s  = os.path.dirname(fn)
            fold_s  = fold_s.replace(os.path.expanduser('~'), '~', 1) if fold_s.startswith(os.path.expanduser('~')) else fold_s
        elif btn_m=='cfld' and ed.get_filename():
            fold_s  = os.path.dirname(ed.get_filename())
            fold_s  = fold_s.replace(os.path.expanduser('~'), '~', 1) if fold_s.startswith(os.path.expanduser('~')) else fold_s
        elif btn_m=='s/cfld':   # [Shift+]CurDir = CurFile
            if not os.path.isfile(     ed.get_filename()):   continue#while_fif
            incl_s  = os.path.basename(ed.get_filename())
            fold_s  = os.path.dirname( ed.get_filename())
            fold_s  = fold_s.replace(os.path.expanduser('~'), '~', 1) if fold_s.startswith(os.path.expanduser('~')) else fold_s
            dept_n  = 1
            excl_s  = ''
        elif btn_m=='c/cfld':   # [Ctrl+]CurDir  = InTabs
            incl_s  = '*'
            fold_s  = IN_OPEN_FILES
        elif btn_m=='sc/cfld':  # [Ctrl+Shift+]CurDir = CurTab
            incl_s  = ed.get_prop(app.PROP_TAB_TITLE)   ##!! need tab-id?
            fold_s  = IN_OPEN_FILES
            excl_s  = ''
            
        elif btn_p=='totb':
            totb_it = totb_l[int(totb_s)]
            pass;              #LOG and log('totb_s,totb_it={}',(totb_s,totb_it))
            fxs     = stores.get('tofx', [])
            if False:pass
            elif totb_it==_('[Clear fixed files]') and fxs:
                if app.ID_YES == app.msg_box(
                                  f(_('Clear all fixed files ({}) for "Show in?"'), len(fxs))
                                , app.MB_OKCANCEL+app.MB_ICONQUESTION):
                    stores['tofx']  = []
                    totb_s  = '1'                                   # == TOTB_USED_TAB
                else:
                    totb_s  = totb_s_pre
                   #continue#while_fif
            elif totb_it==_('[Add fixed file]'):
                fx      = app.dlg_file(True, '', os.path.expanduser(fold_s), '')
                if not fx or not os.path.isfile(fx):
                    totb_s  = totb_s_pre
                   #continue#while_fif
                else:
                    fxs     = stores.get('tofx', [])
                    if fx in fxs:
                        totb_s  = str(4+fxs.index(fx))
                    else:
                        stores['tofx'] = fxs + [fx]
                        totb_s  = str(4+len(stores['tofx'])-1)      # skip: new,prev,clear,add,files-1
                pass;          #LOG and log('totb_s={}',(totb_s))

        elif btn_m=='c/cntx' and cntx_s=='1':
            sBf = str(apx.get_opt('fif_context_width_before', apx.get_opt('fif_context_width', 1)))
            sAf = str(apx.get_opt('fif_context_width_after' , apx.get_opt('fif_context_width', 1)))
            ans   = app.dlg_input_ex(2, _('Report context settings')
                , _('Report with lines before') , sBf
                , _('Report with lines after')  , sAf
                )
            pass;               LOG and log('cntx ans={}',(ans))
            sBf,sAf = ans   if ans is not None else     ('0', '0')
            pass;               LOG and log('cntx sBf,sAf={}',(sBf,sAf))
            nBf = int(sBf) if sBf.isdigit() else 0
            nAf = int(sAf) if sAf.isdigit() else 0
            pass;               LOG and log('cntx nBf,nAf={}',(nBf,nAf))
            if nBf+nAf > 0:
                apx.set_opt('fif_context_width_before', nBf)
                apx.set_opt('fif_context_width_after' , nAf)
            focused = 'what'

        # Save data after cmd
        stores['reex']  = reex01
        stores['case']  = case01
        stores['word']  = word01
        stores['what']  = add_to_history(what_s, stores.get('what', []), MAX_HIST, unicase=False)
        stores['incl']  = add_to_history(incl_s, stores.get('incl', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['excl']  = add_to_history(excl_s, stores.get('excl', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['fold']  = add_to_history(fold_s, stores.get('fold', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['dept']  = dept_n
        stores['repl']  = add_to_history(repl_s, stores.get('repl', []), MAX_HIST, unicase=False)
        stores['cllc']  = cllc_s
        stores['join']  = join_s
        stores['totb']  = '1' if totb_s=='0' else totb_s
#       stores['totb']  = str(min(1, int(totb_s)))
        stores['shtp']  = shtp_s
        stores['cntx']  = cntx_s
        stores['algn']  = algn_s
        stores['skip']  = skip_s
        stores['sort']  = sort_s
        stores['frst']  = frst_s
        stores['enco']  = enco_s
        open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
        
        # Cmds to act
        if btn_p in ('!cnt', '!fnd', '!rep'):
            if  btn_m=='!rep' \
            and app.ID_OK != app.msg_box(
                 f(_('Do you want to replace in {}?'), 
                    _('current tab')        if fold_s==IN_OPEN_FILES and not ('*' in incl_s or '?' in incl_s) else 
                    _('all tabs')           if fold_s==IN_OPEN_FILES else 
                    _('all found files')
                 )
                ,app.MB_OKCANCEL+app.MB_ICONQUESTION):
                continue#while_fif
            root        = fold_s.rstrip(r'\/') if fold_s!='/' else fold_s
            root        = os.path.expanduser(root)
            root        = os.path.expandvars(root)
            if not what_s:
                app.msg_box(f(_('Fill the "{}" field'), caps['what']), app.MB_OK+app.MB_ICONWARNING)
                focused     = 'what'
                continue#while_fif
            if reex01=='1':
                try:
                    re.compile(what_s)
                except Exception as ex:
                    app.msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}'), caps['what'], ex), app.MB_OK+app.MB_ICONWARNING) 
                    focused = 'what'
                    continue#while_fif
                if btn_p=='!rep':
                    try:
                        re.sub(what_s, repl_s, '')
                    except Exception as ex:
                        app.msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}'), caps['repl'], ex), app.MB_OK+app.MB_ICONWARNING) 
                        focused = 'repl'
                        continue#while_fif
            if fold_s!=IN_OPEN_FILES and (not root or not os.path.isdir(root)):
                app.msg_box(f(_('Set existing value in "{}"  or use "{}" (see {})'), caps['fold'], IN_OPEN_FILES, caps['pres']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'fold'
                continue#while_fif
            if not incl_s:
                app.msg_box(f(_('Fill the "{}" field'), caps['incl']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'incl'
                continue#while_fif
            if 0 != incl_s.count('"')%2:
                app.msg_box(f(_('Fix quotes in the "{}" field'), caps['incl']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'incl'
                continue#while_fif
            if 0 != excl_s.count('"')%2:
                app.msg_box(f(_('Fix quotes in the "{}" field'), caps['excl']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'excl'
                continue#while_fif
            if shtp_l[int(shtp_s)] in (SHTP_MIDDL_R, SHTP_MIDDL_RCL
                                      ,SHTP_SPARS_R, SHTP_SPARS_RCL
                                      ) and \
               sort_s!='0':
                app.msg_box(f(_('Conflicting "{}" and "{}" options.\n\nSee Help--Tree.'), caps['sort'], caps['shtp']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'shtp'
                continue#while_fif
            if shtp_l[int(shtp_s)] in (SHTP_MIDDL_R, SHTP_MIDDL_RCL
                                      ,SHTP_SPARS_R, SHTP_SPARS_RCL
                                      ) and \
               fold_s==IN_OPEN_FILES:
                app.msg_box(f(_('Conflicting "{}" and "{}" options.\n\nSee Help--Tree.'),IN_OPEN_FILES, caps['shtp']), app.MB_OK+app.MB_ICONWARNING) 
                focused     = 'shtp'
                continue#while_fif
            how_walk    =dict(                                  #NOTE: fif params
                 root       =root
                ,file_incl  =incl_s
                ,file_excl  =excl_s
                ,depth      =dept_n-1               # ['All', 'In folder only', '1 level', …]
                ,skip_hidn  =skip_s in ('1', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                ,skip_binr  =skip_s in ('2', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                ,sort_type  =apx.icase( sort_s=='0','' 
                                       ,sort_s=='1','date,desc' 
                                       ,sort_s=='2','date,asc' ,'')
                ,only_frst  =int((frst_s+',0').split(',')[1])
#               ,only_frst  =int(frst_s)
                ,skip_unwr  =btn_p=='!rep'
                ,enco       =enco_l[int(enco_s)].split(', ')
                )
            what_find   =dict(
                 find       =what_s
                ,repl       =repl_s if btn_p=='!rep' else None
                ,mult       =False
                ,reex       =reex01=='1'
                ,case       =case01=='1'
                ,word       =word01=='1'
                ,only_frst  =int((frst_s+',0').split(',')[0])
                )
            cllc_v      = cllc_l[int(cllc_s)]
            what_save   = dict(  # cllc_s in ['All matches', 'Match counts'==(btn=='!cnt'), 'Filenames']
                 count      = not (btn_m=='s/!cnt' or  cllc_v==CLLC_FNAME)
#                count      = (btn=='!cnt' and scam!='s') or  cllc_v!=CLLC_FNAME
#                count      = btn=='!cnt' or  cllc_v!=CLLC_FNAME
                ,place      = btn_p!='!cnt' and cllc_v==CLLC_MATCH
                ,lines      = btn_p!='!cnt' and cllc_v==CLLC_MATCH #and reex01=='0'
                )
            shtp_v      = shtp_l[int(shtp_s)]
            totb_i      = int(totb_s)
            totb_it     = totb_l[totb_i]
            fxs         = stores.get('tofx', [])
            totb_v      = TOTB_NEW_TAB              if btn_m=='s/!fnd' or totb_it==TOTB_NEW_TAB     else \
                          totb_it                   if totb_it.startswith('tab:')                   else \
                          'file:'+fxs[totb_i-4]     if totb_it.startswith('file:')                  else \
                          TOTB_USED_TAB
            pass;               LOG and log('totb_s,totb_it,totb_v={}',(totb_s,totb_it,totb_v))
            how_rpt     = dict(
                 totb   =    totb_v
#                totb   =    totb_l[int(totb_s)] if btn_m!='s/!fnd' else totb_l[0]  # NewTab if Shift+Find
#                totb   =    totb_l[int(totb_s)]
                ,sprd   =              sort_s=='0' and shtp_v not in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_SHRTS_R, SHTP_SHRTS_RCL)
                ,shtp   =    shtp_v if sort_s=='0' or  shtp_v     in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_SHRTS_R, SHTP_SHRTS_RCL) else SHTP_SHORT_R
                ,cntx   =    '1'==cntx_s and btn_p!='!rep'
                ,algn   =    '1'==algn_s
                ,join   =    '1'==join_s or  btn_m=='c/!fnd' # Append if Ctrl+Find
#               ,join   =    '1'==join_s
                )
            totb_s  = '1' if totb_s=='0' else totb_s
#           totb_s  = str(min(1, int(totb_s)))
            ################################
            progressor = ProgressAndBreak()
            rpt_data, rpt_info = find_in_files(     #NOTE: run-fif
                 how_walk   = how_walk
                ,what_find  = what_find
                ,what_save  = what_save
                ,how_rpt    = how_rpt
                ,progressor = progressor
                )
            if not rpt_data and not rpt_info: 
                app.msg_status(_("Search stopped"))
                continue#while_fif
            frfls   = rpt_info['files']
            frgms   = rpt_info['frgms']
            ################################
            pass;              #LOG and log('frgms={}, rpt_data=\n{}',frgms, pf(rpt_data))
            msg_rpt = _('No matches found') \
                        if 0==frfls else \
                      f(_('Found {} match(es) in {} file(s)'), frgms, frfls)
            progressor.set_progress(msg_rpt)
            if 0==frgms and not REPORT_FAIL:    continue#while_fif
            req_opts= None
            if SAVE_REQ_TO_RPT:
                req_opts= {k:v for (k,v) in stores.items() if k[:3] not in ('wd_', 'wo_', 'pse')}
                req_opts['what']=what_s
                req_opts['repl']=repl_s
                req_opts['incl']=incl_s
                req_opts['excl']=excl_s
                req_opts['fold']=fold_s
                req_opts['dept']-=1
                req_opts    = json.dumps(req_opts)
            report_to_tab(                      #NOTE: run-report
                rpt_data
               ,rpt_info
               ,how_rpt
               ,how_walk
               ,what_find
               ,what_save
               ,progressor  = progressor
               ,req_opts    = req_opts
               )
            progressor.set_progress(msg_rpt)
            ################################
            if 0<frgms and CLOSE_AFTER_GOOD:    break#while_fif
       #while_fif
   #def dlg_fif

if __name__ == '__main__' :     # Tests
    Command().show_dlg()    #??
        
'''
ToDo
[+][kv-kv][25feb16] 'Sort files' with opts No/By date desc/By date asc 
[+][kv-kv][25feb16] 'First N files'
[+][kv-kv][25feb16] 'Append to results'
[-][kv-kv][25feb16] 'Show results in' with opts Panel/Tab/CB
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
[+][kv-kv][08apr16] +Del/-Edit presets
[+][kv-kv][08apr16] status report: Found N fragments in M files
[+][kv-kv][14apr16] dont create new tab - reuse tab with max tag
[+][kv-kv][14apr16] opt: "compact output" (file:frag) or "lined" (file:\nfrag)
[+][a1-kv][15apr16] use ed selection for 'what'
[ ][kv-kv][15apr16] use next group for new tab
[+][kv-kv][15apr16] dont fill if 0 matches
[+][kv-kv][18apr16] wait ESC when fill tab
[?][kv-kv][18apr16] ? allow dir in What (like ST)
[?][kv-kv][19apr16] ? allow many roots
[+][kv-kv][20apr16] msg_st('', T) 
[+][kv-kv][20apr16] fold old res-reports before append new
[ ][kv-kv][21apr16] Show stage time in stat-data
[+][kv-kv][21apr16] Add %% to msg about stopping
[+][kv-kv][21apr16] Extra ops: lexers, wait 2nd+3rd ESC
[+][kv-kv][21apr16] Add plugin cmd "Find in cur file"
[+][kv-kv][22apr16] Transfer ops from local Find
[+][a1-kv][22apr16] Extra ops: Style for mark
[+][kv-kv][22apr16] Extra ops: Hide dlg after good res
[+][kv-kv][22apr16] Tips and ExtraOpts in dlg Help
[+][kv-kv][22apr16] Use text from Cud (not from disk!) for modifyed files
[ ][kv-kv][22apr16] Set caret to 1st fragment (with scroll)
[+][at-kv][26apr16] Move select_lexer,get_groups_count,html2rgb to cudax_lib
[+][kv-kv][26apr16] AsSubl: empty InFiles, InFolder ==> find in open files (ready preset?)
[+][kv-kv][26apr16] AsSubl: extra src lines as "context" in report
[+][kv-kv][29apr16] extra inf in title: 10 must be opts
[?][kv-kv][29apr16] aligning for MIDDL need in each dir 
[ ][kv-kv][29apr16] ! find_in_ed must pass to dlg title + tab_id
[+][kv-kv][29apr16] extract 'pres' to dlg_preset
[-][kv-kv][04may16] BUG? Encoding ex breaks reading file ==> next encoding doubles stat data
[+][a1-kv][10may16] Replace in files
[+][at-kv][10may16] Checks for preset
[+][kv-kv][11may16] Try to save last active control
[+][kv-kv][13may16] Set empty Exclude if hidden
[?][kv-kv][13may16] Custom: hide Append+Firsts
[?][kv-kv][13may16] UnDo for ReplaceInFiles by report
[-][kv-kv][13may16] Auto-Click-More before focus hidden field
[+][kv-kv][13may16] Ask "Want repl in OPEN TABS"
[+][kv-kv][13may16] Use os.access(path, os.W_OK)
[+][kv-kv][14may16] Calc place for new fragment: old_head|new|old_tail
[+][a1-kv][14may16] Mark new fragments with new styles
[ ][at-kv][14may16] Optim rpt filling
[+][kv-kv][25may16] Save fold after Browse
[+][kv-kv][30may16] Add tree type path/(r):line
[+][a1-kv][31may16] Use source EOL to save after replacements
[+][kv-kv][01jun16] Use Ctrl/Shift/Alt for more action
[+][kv-kv][02jun16] Add buttons "#&1", "#&2", "#&3" for direct load Preset #1, #2, #3 (outside? width=0!)
[+][kv-kv][11jun16] Add "/folder-mask" for incl/excl
[ ][kv-kv][11jun16] ? Lazy/Yield for cllc--find--rept ?
[-][kv-kv][14jun16] Opt "save active tab on Close" ?
[+][kv-kv][14jun16] Cmds "Show next/prev result" ?
[+][kv-kv][09feb17] Set dept="folder only" when cmd "Search in cur file"
[+][kv-kv][09feb17] Clear excl when cmd "Search in cur file"
[+][kv-kv][09feb17] Clear excl when cmd "Search in cur tab"
[ ][kv-kv][09feb17] ? New menu cmd (wo dlg): Find sel in cur file
[ ][kv-kv][09feb17] ? New menu cmd (wo dlg): Find sel in cur tab
[ ][kv-kv][09feb17] ? New menu cmd (wo dlg): Find sel in all tab
[ ][kv-kv][09feb17] ? New menu cmd (wo dlg): Find sel in cur dir
[+][kv-kv][09feb17] Help: show button "open user.json" when Opt, ref "RE" when Tips
[+][kv-kv][09feb17] Replace "..." to "…"
[ ][kv-kv][09feb17] After stoping show (2942 matches in 166 (stop at NN%) files)
[+][at-kv][00feb17] DblClick to nav
[ ][kv-kv][15feb17] More scam-Find command: Close dlg, Nav to first result
[+][kv-kv][22feb17] Opt to "Show in" fixed fif-file(s)
[+][kv-kv][23feb17] scam+Less/More to hide/show excl or repl
[+][kv-kv][23feb17] "In subf" v-align with "In fold"
[-][kv-kv][23feb17] Show min width in Cust
[+][kv-kv][23feb17] Show "Show in"+"Append"+"Tree type" in title for compact mode
[+][at-kv][22mat17] "fif_read_head_size(bytes)"
[+][kv-kv][23mat17] "fif_context_width_before", "fif_context_width_after"
[ ][kv-kv][30mat17] Sort and Tree conflict is too hard. Use "Stop? Without sort?"
[+][kv-kv][30mat17] !! Need Properties dlg to show/edit opts from/to user.json
[ ][kv-kv][12apr17] os.walk is wide or depth? How to switch mode?
'''