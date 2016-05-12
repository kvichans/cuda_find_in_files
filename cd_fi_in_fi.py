''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.9.3 2016-05-11'
ToDo: (see end of file)
'''

import  re, os, sys, locale, json, collections
from    fnmatch         import fnmatch
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    .cd_plug_lib    import *
from    .chardet.universaldetector import UniversalDetector

OrdDict = collections.OrderedDict
c9, c10, c13    = chr(9), chr(10), chr(13) 
#FROM_API_VERSION= '1.0.119'

pass;                           Tr.tr   = Tr(apx.get_opt('fif_log_file', '')) if apx.get_opt('fif_log_file', '') else Tr.tr
pass;                           LOG     = (-1==-1)  # Do or dont logging.
pass;                           FNDLOG  = (-2== 2) and LOG or apx.get_opt('fif_FNDLOG', False)
pass;                           RPTLOG  = (-3== 3) and LOG or apx.get_opt('fif_RPTLOG', False)
pass;                           NAVLOG  = (-4== 4) and LOG or apx.get_opt('fif_NAVLOG', False)
pass;                           DBG_DATA_TO_REPORT  =         apx.get_opt('fif_DBG_data_to_report', False)
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

def fit_mark_style_for_attr(js:dict)->dict:
    """ Convert 
            {"color_back":"", "color_font":"", "font_bold":false, "font_italic":false
            ,"color_border":"", "borders":{"l":"","r":"","b":"","t":""}}
        to dict with params for call ed.attr
            (color_bg=COLOR_NONE, color_font=COLOR_NONE, font_bold=0, font_italic=0, 
            color_border=COLOR_NONE, border_left=0, border_right=0, border_down=0, border_up=0)
    """
    V_L     = ['solid', 'dash', '2px', 'dotted', 'rounded', 'wave']
    shex2int= apx.html_color_to_int
    kwargs  = {}
    if js.get('color_back'  , ''):   kwargs['color_bg']      = shex2int(js['color_back'])
    if js.get('color_font'  , ''):   kwargs['color_font']    = shex2int(js['color_font'])
    if js.get('color_border', ''):   kwargs['color_border']  = shex2int(js['color_border'])
    if js.get('font_bold'   , False):kwargs['font_bold']     = 1
    if js.get('font_italic' , False):kwargs['font_italic']   = 1
    jsbr    = js.get('borders', {})
    if jsbr.get('left'  , ''):       kwargs['border_left']   = V_L.index(jsbr['left'  ])+1
    if jsbr.get('right' , ''):       kwargs['border_right']  = V_L.index(jsbr['right' ])+1
    if jsbr.get('bottom', ''):       kwargs['border_down']   = V_L.index(jsbr['bottom'])+1
    if jsbr.get('top'   , ''):       kwargs['border_up']     = V_L.index(jsbr['top'   ])+1
    return kwargs
   #def fit_mark_style_for_attr
   
GAP     = 5

IN_OPEN_FILES   = _('<Open Files>')
TOP_RES_SIGN    = _('+Search for')
CLLC_MATCH      = _('Normal matches')
CLLC_COUNT      = _('Count only')
CLLC_FNAME      = _('Filenames only')
TOTB_USED_TAB   = _('<prior tab>')
TOTB_NEW_TAB    = _('<new tab>')
SHTP_SHORT_R    = _('path(r):line')
SHTP_SHORT_RCL  = _('path(r:c:l):line')
SHTP_MIDDL_R    = _('dir/file(r):line')
SHTP_MIDDL_RCL  = _('dir/file(r:c:l):line')
SHTP_SPARS_R    = _('dir/file/(r):line')
SHTP_SPARS_RCL  = _('dir/file/(r:c:l):line')
cllc_l          = [CLLC_MATCH, CLLC_COUNT, CLLC_FNAME]
shtp_l          = [SHTP_SHORT_R, SHTP_SHORT_RCL
                  ,SHTP_MIDDL_R, SHTP_MIDDL_RCL
                  ,SHTP_SPARS_R, SHTP_SPARS_RCL
                  ]
ENCO_DETD       = _('"detected"')

lexers_l        = apx.get_opt('fif_lexers'                  , ['Search results', 'FiF'])
FIF_LEXER       = apx.choose_avail_lexer(lexers_l) #select_lexer(lexers_l)
lexers_l        = list(map(lambda s: s.upper(), lexers_l))
USE_EDFIND_OPS  = apx.get_opt('fif_use_edfind_opt_on_start' , False)
USE_SEL_ON_START= apx.get_opt('fif_use_selection_on_start'  , False)
ESC_FULL_STOP   = apx.get_opt('fif_esc_full_stop'           , False)
REPORT_FAIL     = apx.get_opt('fif_report_no_matches'       , False)
FOLD_PREV_RES   = apx.get_opt('fif_fold_prev_res'           , False)
CLOSE_AFTER_GOOD= apx.get_opt('fif_hide_if_success'         , False)
LEN_TRG_IN_TITLE= apx.get_opt('fif_len_target_in_title'     , 10)
MARK_STYLE      = apx.get_opt('fif_mark_style'              , {'borders':{'bottom':'dotted'}})
MARK_STYLE      = fit_mark_style_for_attr(MARK_STYLE)
DEF_LOC_ENCO    = 'cp1252' if sys.platform=='linux' else locale.getpreferredencoding()
class Command:
    def find_in_ed(self):
        filename= ed.get_filename()
        return dlg_fif(what='', opts=dict(
             incl = os.path.basename(filename) if filename else ed.get_prop(app.PROP_TAB_TITLE)
            ,fold = IN_OPEN_FILES
            ,cllc = str(cllc_l.index(CLLC_MATCH))
            ))
       #def find_in_ed

    def find_in_tabs(self):
        return dlg_fif(what='', opts=dict(
             incl = '*'
            ,fold = IN_OPEN_FILES
            ,cllc = str(cllc_l.index(CLLC_MATCH))
            ))
       #def find_in_ed

    def show_dlg(self, what='', opts={}):
        return dlg_fif(what, opts)

    def _nav_to_src(self, where:str, how_act='move'):
        return nav_to_src(where, how_act)
   #class Command

def dlg_press(stores, cfg_json, invl_l, desc_l):
    pset_l  = stores.setdefault('pset', [])
    keys_l  = ['reex','case','word'
              ,'incl','excl'
              ,'fold','dept'
              ,'skip','sort','frst','enco'
              ,'cllc','totb','join','shtp','algn','cntx']
    totb_i  = keys_l.index('totb')
    invl_l  = [v for v in invl_l]
    invl_l[totb_i]  = str(min(1, int(invl_l[totb_i])))
    ouvl_l  = [v for v in invl_l]
    caps_l  = ['.*','aA','"w"'
              ,'In files','Not in files'
              ,'In folder','Subfolders'
              ,'Skip files','Sort file list','Firsts','Encodings'
              ,'Collect','Show in','Append results','Tree type','Align','Show context']
    def upgrd(ps:list)->list:
        if '_aa_' not in ps:  return ps
        if ps.pop('_aa_', ''):
            ps['_reex'] = 'x'
            ps['_case'] = 'x'
            ps['_word'] = 'x'
        if ps.pop('_il_', ''):
            ps['_incl'] = 'x'
            ps['_excl'] = 'x'
        if ps.pop('_fo_', ''):
            ps['_fold'] = 'x'
            ps['_dept'] = 'x'
        if ps.pop('_fn_', ''):
            ps['_skip'] = 'x'
            ps['_sort'] = 'x'
            ps['_frst'] = 'x'
            ps['_enco'] = 'x'
        if ps.pop('_rp_', ''):
            ps['_cllc'] = 'x'
            ps['_totb'] = 'x'
            ps['_join'] = 'x'
            ps['_shtp'] = 'x'
            ps['_algn'] = 'x'
            ps['_cntx'] = 'x'
        return ps
       #def upgrd
    for ps in pset_l:
        upgrd(ps)
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
              ,_('Delete preset\tSelect name...')
              ,_('Save as preset\tSelect options to save...')]
    ind_inop= len(pset_l)
    ind_del = len(pset_l)+1
    ind_save= len(pset_l)+2
    ps_ind  = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(dlg_list))      #NOTE: dlg-menu-press
    if ps_ind is None:  return None
    if False:pass
    elif ps_ind==ind_inop:
        # Find in open files
#       fold_s = IN_OPEN_FILES
        ouvl_l[keys_l.index('fold')]    = IN_OPEN_FILES
        return ouvl_l
        
    elif ps_ind<len(pset_l):
        # Restore
        ps      = pset_l[ps_ind]
        for i, k in enumerate(keys_l):
            if ps.get('_'+k, '')=='x':
                ouvl_l[i]   = ps.get(k, ouvl_l[i])
        ouvl_l[totb_i]  = str(min(1, int(ouvl_l[totb_i])))
        app.msg_status(_('Restored preset: ')+ps['name'])
        return ouvl_l
        
    elif ps_ind==ind_del and pset_l:
        # Delete
        ind4del = app.dlg_menu(app.MENU_LIST, '\n'.join([ps['name'] for ps in pset_l]))
        if ind4del is None:  return None
        ps      = pset_l[ind4del]
        del pset_l[ind4del]
        open(cfg_json, 'w').write(json.dumps(stores, indent=4))
        app.msg_status(_('Deleted preset: ')+ps['name'])
        return None
        
    elif ps_ind==ind_save:
        # Save
        items   = [f('{} -- {}', caps_l[i], desc_l[i]) for i, k in enumerate(keys_l)]
        btn,vals,chds   = dlg_wrapper(_('Save preset'), GAP+300+GAP,GAP+500+GAP,     #NOTE: dlg-pres
             [dict(           tp='lb'    ,t=GAP             ,l=GAP          ,w=300  ,cap=_('&Name:')            ) # &n
             ,dict(cid='name',tp='ed'    ,t=GAP+20          ,l=GAP          ,w=300                              ) # 
             ,dict(           tp='lb'    ,t=GAP+55          ,l=GAP          ,w=300  ,cap=_('&What to save:')    ) # &w
             ,dict(cid='what',tp='ch-lbx',t=GAP+75,h=390    ,l=GAP          ,w=300  ,items=items               )
             ,dict(cid='!'   ,tp='bt'    ,t=GAP+500-28      ,l=GAP+300-170  ,w=80   ,cap=_('&Save'),props='1'   ) # &s  default
             ,dict(cid='-'   ,tp='bt'    ,t=GAP+500-28      ,l=GAP+300-80   ,w=80   ,cap=_('Close')             )
             ],    dict(name=f(_('#{}: {} in {}'), 1+len(pset_l), desc_l[keys_l.index('incl')], desc_l[keys_l.index('fold')])
                       ,what=(0,['1']*len(keys_l))), focus_cid='name')
        pass;                  #LOG and log('vals={}',vals)
        if btn is None or btn=='-': return None
        ps_name = vals['name']
        sl,vals = vals['what']
        pass;                  #LOG and log('vals={}',vals)
        ps      = OrdDict([('name',ps_name)])
        for i, k in enumerate(keys_l):
            if vals[i]=='1':
                ps['_'+k] = 'x'
                ps[    k] = invl_l[i]
            else:
                ps['_'+k] = '_'
        pass;                  #LOG and log('ps={}',(ps))
        pset_l += [ps]
        open(cfg_json, 'w').write(json.dumps(stores, indent=4))
        app.msg_status(_('Saved preset: ')+ps['name'])
        return None
    return      ouvl_l
   #def dlg_press

def dlg_help(word_h, shtp_h, cntx_h):
    RE_DOC_REF  = 'https://docs.python.org/3/library/re.html'
    TIPS_BODY   = _(r'''
• Values of "In file" and "Not in file" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
 
• Set special value "{tags}" for field "In folder" to search in all opened documents.
    Preset "In folder={tags}" helps to do this.
    To search in unsaved tabs use mask "*" in field "In files".
 
• "w" - {word}
 
• Long-term searching can be interrupted with ESC.
    Search has three stages: 
        picking files, 
        finding fragments, 
        reporting.
    ESC stops any stage. When picking and finding, ESC stops only this stage, so next stage begins.
''').strip().format(word=word_h.replace('\r', '\n'), tags=IN_OPEN_FILES)
#• Reg.ex. tips:
#   Format for found groups in Replace: \1
    TREE_BODY   = _(r'''
Option "Tree type" - {shtp}
''').strip().format(shtp=shtp_h.replace('\r', '\n'))
    OPTS_BODY   = _(r'''
Extra options for "user.json" (need restart after changing). 
Default values:
    // Fill Find with selection from current file when dialog starts
    "fif_use_selection_on_start":false,
    
    // Copy find-options ".*", "aA", "w" from editor find to dialog on start
    "fif_use_edfind_opt_on_start":false,
    
    // ESC will stop all stages 
    "fif_esc_full_stop":false,
    
    // Close dialog if searching was success
    "fif_hide_if_success":false,
    
    // What part of target ("Find") will appear in title of the result tab
    "fif_len_target_in_title":10,
    
    // Need reporting if nothing found
    "fif_report_no_matches":false,
    
    // "Show context" will append N around source lines to report
    "fif_context_width":1,
    
    // Style to mark found fragment in report-text
    // Full form
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
    
    // Exact encoding to read files
    "fif_locale_encoding":"{def_enco}",
    
    // List of lexer names. First available will be applyed.
    "fif_lexers":["Search results"],
    
    // Skip big files (0 - read all)
    "fif_skip_file_size_more_Kb":0,
    
    // Size of "head" buffer to detect "binary file"
    "fif_read_head_size":1024,
''').strip().replace('{def_enco}', DEF_LOC_ENCO)
#   // Before append result fold all previous ones
#   "fif_fold_prev_res":false,
#   
    DW, DH      = 600, 600
#   vals_hlp    = dict(htxt=TIPS_BODY)
    vals_hlp    = dict(htxt=TIPS_BODY
                      ,tips=True
                      ,tree=False
                      ,opts=False
                      )
    while_hlp   = True
    while while_hlp:
        btn_hlp,    \
        vals_hlp,   \
        chds_hlp    = dlg_wrapper(_('Help for "Find in files"'), GAP+DW+GAP,GAP+DH+GAP,     #NOTE: dlg-hlp
             [dict(cid='htxt',tp='me'    ,t=GAP  ,h=DH-28,l=GAP          ,w=DW   ,props='1,0,1'                                  ) #  ro,mono,border
             ,dict(           tp='ln-lb' ,tid='-'        ,l=GAP          ,w=180  ,cap=_('Reg.ex. on python.org'),props=RE_DOC_REF)
             ,dict(cid='tips',tp='ch-bt' ,t=GAP+DH-23    ,l=GAP+DW-380   ,w=80   ,cap=_('T&ips')                ,act='1'         )
             ,dict(cid='tree',tp='ch-bt' ,t=GAP+DH-23    ,l=GAP+DW-280   ,w=80   ,cap=_('&Tree')                ,act='1'         )
             ,dict(cid='opts',tp='ch-bt' ,t=GAP+DH-23    ,l=GAP+DW-180   ,w=80   ,cap=_('&Opts')                ,act='1'         )
             ,dict(cid='-'   ,tp='bt'    ,t=GAP+DH-23    ,l=GAP+DW-80    ,w=80   ,cap=_('&Close')                                )
             ], vals_hlp, focus_cid='htxt')
        pass;                  #LOG and log('vals_hlp={}',vals_hlp)
        if btn_hlp is None or btn_hlp=='-': break#while_hlp
        if False:pass
        elif btn_hlp=='tips':   vals_hlp["htxt"] = TIPS_BODY; vals_hlp["tips"] = True; vals_hlp["tree"] = False;vals_hlp["opts"] = False
        elif btn_hlp=='tree':   vals_hlp["htxt"] = TREE_BODY; vals_hlp["tips"] = False;vals_hlp["tree"] = True; vals_hlp["opts"] = False
        elif btn_hlp=='opts':   vals_hlp["htxt"] = OPTS_BODY; vals_hlp["tips"] = False;vals_hlp["tree"] = False;vals_hlp["opts"] = True
       #while_hlp
   #def dlg_help

def dlg_fif(what='', opts={}):
    max_hist= apx.get_opt('ui_max_history_edits', 20)
    cfg_json= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_find_in_files.json'
    stores  = apx._json_loads(open(cfg_json).read(), object_pairs_hook=OrdDict)    if os.path.exists(cfg_json) else    OrdDict()
    mask_h  = _('Space-separated file masks.\rDouble-quote mask, which needs space-char.\rUse ? for any character and * for any fragment.')
    reex_h  = _('Regular expression')
    case_h  = _('Case sensitive')
    word_h  = _('Option "Whole words". It is ignored when'
                '\r    Regular expression (".*") is turned on,'
                '\r    "Find" contains not only letters, digits and "_".'
                )
    brow_h  = _('Choose folder')
    curr_h  = _('Use folder of current file')
    more_h  = _('Show/Hide advanced options')
    adju_h  = _('Change dialog layout')
    frst_h  = _('Search only inside N first found files')
    shtp_h  = f(_(  'Format of the reported tree structure.'
                '\rCompact - report all found line with full file info:'
                '\r    path(r[:c:l]):line'
                '\r  Tree scheme'
                '\r    +Search for "*"'
                '\r      <full_path(row[:col:len])>: line with ALL marked fragments'
                '\rMiddle - report separated folders and fragments:'
                '\r    dir/file(r[:c:l]):line'
                '\r  Tree scheme'
                '\r    +Search for "*"'
                '\r      <root>: #count'
                '\r        <dir>: #count'
                '\r          <file.ext(row[:col:len])>: line with ONE marked fragment'
                '\rSparse - report separated folders and lines and fragments:'
                '\r    dir/file/(r[:c:l]):line'
                '\r  Tree scheme'
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
#   cntx_h  = _('Append around source lines in Results')
    cntx_h  = _('Show result line and both its nearest lines, above and below result')
#   algn_h  = _("Align path/row/col/len (what are) in Results lines with found fragment")
    algn_h  = _("Align columns (filenames/numbers) by widest column width")
    coun_h  = _('Count matches only.\rIt is like pressing Find with option Collect: "Count only".')
    pset_h  = _('Save options for future.\rRestore saved options.')
    dept_l  = [_('All'), _('In folder only'), _('1 level'), _('2 levels'), _('3 levels'), _('4 levels'), _('5 levels')]
    skip_l  = [_("Don't skip"), _('Hidden'), _('Binary'), _('Hidden, Binary')]
    sort_l  = [_("Don't sort"), _('By date, from newest'), _('By date, from oldest')]

    loc_enco= apx.get_opt('fif_locale_encoding', DEF_LOC_ENCO)
    enco_h  = f(_('What is encoding to read files.\rFirst suitable will be applyed.\r{} is slow.\r\rDefault encoding: {}'), ENCO_DETD, loc_enco)
    enco_l  = ['{}, UTF-8, '+ENCO_DETD 
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
    enco_l  = [f(enco, loc_enco) for enco in enco_l]
        
    DLG_W0, \
    DLG_H0  = (700, 355)

    what_s  = what if what else ed.get_text_sel() if USE_SEL_ON_START else ''
    what_s  = what_s.splitlines()[0] if what_s else ''
    repl_s  = opts.get('repl', '')
    reex01  = opts.get('reex', stores.get('reex', '0'))
    case01  = opts.get('case', stores.get('case', '0'))
    word01  = opts.get('word', stores.get('word', '0'))
    if USE_EDFIND_OPS:
        ed_opt  = app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
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
    totb_s  = opts.get('totb', stores.get('totb', '0'));    totb_s = str(min(1, int(totb_s)))
    shtp_s  = opts.get('shtp', stores.get('shtp', '0'))
    cntx_s  = opts.get('cntx', stores.get('cntx', '0'))
    algn_s  = opts.get('algn', stores.get('algn', '0'))
    skip_s  = opts.get('skip', stores.get('skip', '0'))
    sort_s  = opts.get('sort', stores.get('sort', '0'))
    frst_s  = opts.get('frst', stores.get('frst', '0'))
    enco_s  = opts.get('enco', stores.get('enco', '0'))

    def add_to_history(val:str, lst:list, max_len:int, unicase=True)->list:
        """ Add/Move val to list head. """
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
    def get_live_restabs()->list:
        rsp = []
        for h in app.ed_handles():
            try_ed  = app.Editor(h)
            tag     = try_ed.get_prop(app.PROP_TAG)
            lxr     = try_ed.get_prop(app.PROP_LEXER_FILE)
            if False:pass
            elif lxr.upper() in lexers_l:
                rsp+= [try_ed.get_prop(app.PROP_TAB_TITLE)]
            elif tag.startswith('FiF'):
                rsp+= [try_ed.get_prop(app.PROP_TAB_TITLE)]
        return rsp
       #def get_live_restabs
    
    focused = 'what'
    while_fif   = True
    while while_fif:
        what_l  = [s for s in stores.get('what', []) if s ]
        incl_l  = [s for s in stores.get('incl', []) if s ]
        excl_l  = [s for s in stores.get('excl', []) if s ]
        fold_l  = [s for s in stores.get('fold', []) if s ]
        repl_l  = [s for s in stores.get('repl', []) if s ]
        totb_l  = [TOTB_NEW_TAB, TOTB_USED_TAB] + get_live_restabs()
        
        wo_excl = stores.get('wo_excl', True)
        wo_repl = True
#       wo_repl = stores.get('wo_repl', True)
        wo_adva = stores.get('wo_adva', True)
        c_more  = _('Mor&e >>') if wo_adva else _('L&ess <<')
        gap1    = (GAP- 28 if wo_excl else GAP)
        gap2    = (GAP- 28 if wo_repl else GAP)+gap1
        gap3    = (GAP-115 if wo_adva else GAP)+gap2
        TXT_W   = stores.get('wd_txts', 400)
        BTN_W   = stores.get('wd_btns', 100)
        lbl_l   = GAP+35*3+GAP+25
        cmb_l   = lbl_l+100
        tl2_l   = lbl_l+220
        tbn_l   = cmb_l+TXT_W+GAP
        DLG_W,\
        DLG_H   = (tbn_l+BTN_W+GAP, DLG_H0+gap3)
        #NOTE: fif-cnts
        cnts    = ([]                                                                                                              # gmqvyz
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
                 +[dict(           tp='lb'      ,tid='fold'     ,l=lbl_l    ,r=cmb_l    ,cap=_('I&n folder:')                   )] # &n
                 +[dict(cid='fold',tp='cb'      ,t=gap1+84      ,l=cmb_l    ,w=TXT_W    ,items=fold_l                           )] # 
                 +[dict(cid='brow',tp='bt'      ,tid='fold'     ,l=tbn_l    ,w=BTN_W    ,cap=_('&Browse...')        ,hint=brow_h)] # &b
                 +[dict(           tp='lb'      ,tid='dept'     ,l=cmb_l    ,w=100      ,cap=_('In s&ubfolders:')               )] # &u
                 +[dict(cid='dept',tp='cb-ro'   ,t=gap1+112     ,l=tl2_l    ,w=140      ,items=dept_l                           )] # 
                 +[dict(cid='cfld',tp='bt'      ,tid='fold'     ,l=GAP      ,w=35*3     ,cap=_('&Current folder')   ,hint=curr_h)] # &c
                +([] if wo_repl else []                         
                 +[dict(           tp='lb'      ,tid='repl'     ,l=lbl_l    ,r=cmb_l    ,cap=_('&Replace with:')                )] # &r
                 +[dict(cid='repl',tp='cb'      ,t=gap1+140     ,l=cmb_l    ,w=TXT_W    ,items=repl_l                           )] # 
                 +[dict(cid='!rep',tp='bt'      ,tid='repl'     ,l=tbn_l    ,w=BTN_W    ,cap=_('Re&place')                      )] # &p
                )                                               
                +([] if wo_adva else  []                        
                 +[dict(           tp='lb'      ,t=gap2+170     ,l=GAP      ,w=150      ,cap=_('== Adv. report options ==')     )] # 
                 +[dict(           tp='lb'      ,tid='cllc'     ,l=GAP      ,w=100      ,cap=_('Co&llect:')                     )] # &l
                 +[dict(cid='cllc',tp='cb-ro'   ,t=gap2+190     ,l=GAP+80   ,r=cmb_l    ,items=cllc_l                           )] # 
                 +[dict(           tp='lb'      ,tid='totb'     ,l=GAP      ,w=100      ,cap=_('Show in&:')                     )] # &:
                 +[dict(cid='totb',tp='cb-ro'   ,t=gap2+217     ,l=GAP+80   ,r=cmb_l    ,items=totb_l                           )] # 
                 +[dict(cid='join',tp='ch'      ,t=gap2+244     ,l=GAP+80   ,w=150      ,cap=_('Appen&d results')               )] # &d
                 +[dict(           tp='lb'      ,tid='shtp'     ,l=GAP      ,w=100      ,cap=_('Tree type &/:')     ,hint=shtp_h)] # &/
                 +[dict(cid='shtp',tp='cb-ro'   ,t=gap2+271     ,l=GAP+80   ,r=cmb_l    ,items=shtp_l                           )] # 
                 +[dict(cid='algn',tp='ch'      ,t=gap2+298     ,l=GAP      ,w=100      ,cap=_('Align &|')          ,hint=algn_h)] # &|
                 +[dict(cid='cntx',tp='ch'      ,t=gap2+298     ,l=GAP+80   ,w=150      ,cap=_('Show conte&xt')     ,hint=cntx_h)] # &x
                                                
                 +[dict(           tp='lb'      ,t=gap2+170     ,l=tl2_l    ,w=150      ,cap=_('== Adv. search options ==')     )] # 
                 +[dict(           tp='lb'      ,tid='skip'     ,l=tl2_l    ,w=100      ,cap=_('S&kip files:')                  )] # &k
                 +[dict(cid='skip',tp='cb-ro'   ,t=gap2+190     ,l=tl2_l+100,w=180      ,items=skip_l                           )] # 
                 +[dict(           tp='lb'      ,tid='sort'     ,l=tl2_l    ,w=100      ,cap=_('S&ort file list:')              )] # &o
                 +[dict(cid='sort',tp='cb-ro'   ,t=gap2+217     ,l=tl2_l+100,w=180      ,items=sort_l                           )] # 
                 +[dict(           tp='lb'      ,tid='frst'     ,l=tl2_l    ,w=100      ,cap=_('Firsts (&0=all):')  ,hint=frst_h)] # &0
                 +[dict(cid='frst',tp='ed'      ,t=gap2+244     ,l=tl2_l+100,w=180                                              )] # 
                 +[dict(           tp='lb'      ,tid='enco'     ,l=tl2_l    ,w=100      ,cap=_('Encodings:')        ,hint=enco_h)] # 
                 +[dict(cid='enco',tp='cb-ro'   ,t=gap2+271     ,l=tl2_l+100,w=180      ,items=enco_l                           )] # 
                )                                                                                                               
                 +[dict(cid='help',tp='bt'      ,t=DLG_H-GAP-50 ,l=tbn_l    ,w=BTN_W    ,cap=_('&Help...')                      )] # &h
                 +[dict(cid='!fnd',tp='bt'      ,tid='what'     ,l=tbn_l    ,w=BTN_W    ,cap=_('Find'),props='1'                )] #    default
                 +[dict(cid='!cnt',tp='bt'      ,tid='incl'     ,l=tbn_l    ,w=BTN_W    ,cap=_('Coun&t')            ,hint=coun_h)] # &t
                 +[dict(cid='more',tp='bt'      ,t=DLG_H-GAP-25 ,l=GAP      ,w=35*3     ,cap=c_more                 ,hint=more_h)] # &e
                 +[dict(cid='cust',tp='bt'      ,t=DLG_H-GAP-25 ,l=GAP*2+35*3,w=35*3    ,cap=_('Ad&just...')        ,hint=adju_h)] # &j
                 +[dict(cid='-'   ,tp='bt'      ,t=DLG_H-GAP-25 ,l=tbn_l    ,w=BTN_W    ,cap=_('Close')                         )] # 
#                +[dict(cid='pres',tp='bt'      ,t=gap2+165     ,l=tbn_l    ,w=100      ,cap=_('Pre&sets...')       ,hint=pset_h)] # &s
                 +[dict(cid='pres',tp='bt'      ,tid='incl'     ,l=GAP      ,w=105      ,cap=_('Pre&sets...')       ,hint=pset_h)] # &s
#                +[dict(cid='pres',tp='bt'      ,t=DLG_H-GAP-25 ,l=tbn_l-95 ,w=90       ,cap=_('Pre&sets...')       ,hint=pset_h)] # &s
                )
        pass;                  #LOG and log('cnts=¶{}',pf(cnts))
        pass;                  #LOG and log('cnts=¶{}',pf([dict(cid=d['cid'], t=d['t']) for d in cnts if 'cid' in d and 't' in d]))
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
        btn,vals,chds=dlg_wrapper(_('Find in Files'), DLG_W, DLG_H, cnts, vals, focus_cid=focused)     #NOTE: dlg-fif
        if btn is None or btn=='-': return None
        focused     = chds[0] if 1==len(chds) else focused
        pass;                  #LOG and log('vals={}',pf(vals))
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
            totb_s  = vals['totb']
            shtp_s  = vals['shtp']
            cntx_s  = vals['cntx']
            algn_s  = vals['algn']
            skip_s  = vals['skip']
            sort_s  = vals['sort']
            frst_s  = vals['frst']
            enco_s  = vals['enco']
        pass;                  #LOG and log('what_s,incl_s,fold_s={}',(what_s,incl_s,fold_s))
            
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
        stores['totb']  = str(min(1, int(totb_s)))
        stores['shtp']  = shtp_s
        stores['cntx']  = cntx_s
        stores['algn']  = algn_s
        stores['skip']  = skip_s
        stores['sort']  = sort_s
        stores['frst']  = frst_s
        stores['enco']  = enco_s
        stores.pop('toed',None)
        stores.pop('reed',None)
        open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            
        if btn=='more':
            stores['wo_adva']       = not stores.get('wo_adva', True)
            open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif

        if btn=='help':
            dlg_help(word_h, shtp_h, cntx_h)
            continue#while_fif
            
        if btn=='pres':
            ans = dlg_press(stores, cfg_json,
                       (reex01,case01,word01,
                        incl_s,excl_s,
                        fold_s,dept_n,
                        skip_s,sort_s,frst_s,enco_s,
                        cllc_s,totb_s,join_s,shtp_s,algn_s,cntx_s),
                       ('On' if reex01=='1' else 'Off','On' if case01=='1' else 'Off','On' if word01=='1' else 'Off',
                        '"'+incl_s+'"','"'+excl_s+'"',
                        '"'+fold_s+'"',dept_l[dept_n],
                        skip_l[int(skip_s)],sort_l[int(sort_s)],frst_s,enco_l[int(enco_s)],
                        cllc_l[int(cllc_s)],totb_l[int(totb_s)],'On' if join_s=='1' else 'Off',shtp_l[int(shtp_s)],'On' if algn_s=='1' else 'Off','On' if cntx_s=='1' else 'Off')
                        )
            if ans is not None:
                       (reex01,case01,word01,
                        incl_s,excl_s,
                        fold_s,dept_n,
                        skip_s,sort_s,frst_s,enco_s,
                        cllc_s,totb_s,join_s,shtp_s,algn_s,cntx_s)  = ans
            continue#while_fif
                
        if btn=='cust':
            #NOTE: dlg-cust
            custs   = app.dlg_input_ex(4, _('Adjust dialog')
                , _('Width of edits Find/Replace (min 400)'), str(stores.get('wd_txts', 400))
                , _('Width of buttons Browse/Help (min 100)'),str(stores.get('wd_btns', 100))
                , _('Show Exclude masks (0/1)')             , str(0 if stores.get('wo_excl', True) else 1)
                , _('Show Replace (0/1)')                   , str(0 if stores.get('wo_repl', True) else 1)
                )
            if custs is not None:
                stores['wd_txts']   = max(400, int(custs[0]))
                stores['wd_btns']   = max(100, int(custs[1]))
                stores['wo_excl']   = (custs[2]=='0')
                stores['wo_repl']   = (custs[3]=='0')
                open(cfg_json, 'w').write(json.dumps(stores, indent=4))
            continue#while_fif

        open(cfg_json, 'w').write(json.dumps(stores, indent=4))
        if False:pass
        elif btn=='brow':
            path    = app.dlg_dir(fold_s)
            fold_s  = path if path else fold_s
        elif btn=='cfld':
            path    = ed.get_filename()
            fold_s  = os.path.dirname(path) if path else fold_s

        elif btn=='!rep':
            if app.ID_YES != app.msg_box(_('Are you sure to replace in all found files?'), app.MB_YESNO):
                continue#while_fif
        elif btn in ('!cnt', '!fnd'):
            root        = fold_s.rstrip(r'\/') if fold_s!='/' else fold_s
            root        = os.path.expanduser(root)
            root        = os.path.expandvars(root)
            if not what_s:
                app.msg_box(_('Fill the "Find" field'), app.MB_OK) 
                focused     = 'what'
                continue#while_fif
            if reex01=='1':
                try:
                    re.compile(what_s)
                except Exception as ex:
                    app.msg_box(f(_('Set correct "Find" reg.ex.\n\nError:\n{}'),ex), app.MB_OK) 
                    focused = 'what'
                    continue#while_fif
#           if fold_s!=IN_OPEN_FILES and (not fold_s or not os.path.isdir(fold_s)):
            if fold_s!=IN_OPEN_FILES and (not root or not os.path.isdir(root)):
                app.msg_box(f(_('Set existing "In folder" value or use "{}" (see Presets)'), IN_OPEN_FILES), app.MB_OK) 
                focused     = 'fold'
                continue#while_fif
            if not incl_s:
                app.msg_box(_('Fill the "In files" field'), app.MB_OK) 
                focused     = 'incl'
                continue#while_fif
            if 0 != incl_s.count('"')%2:
                app.msg_box(_('Fix quotes in the "In files" field'), app.MB_OK) 
                focused     = 'incl'
                continue#while_fif
            if 0 != excl_s.count('"')%2:
                app.msg_box(_('Fix quotes in the "Not in files" field'), app.MB_OK) 
                focused     = 'excl'
                continue#while_fif
            if shtp_l[int(shtp_s)] in (SHTP_MIDDL_R, SHTP_MIDDL_RCL
                                      ,SHTP_SPARS_R, SHTP_SPARS_RCL
                                      ) and \
               sort_s!='0':
                app.msg_box(_('Conflict "Sort file list" and "Tree type" options.\n\nSee Help--Tree.'), app.MB_OK) 
                focused     = 'shtp'
                continue#while_fif
            if shtp_l[int(shtp_s)] in (SHTP_MIDDL_R, SHTP_MIDDL_RCL
                                      ,SHTP_SPARS_R, SHTP_SPARS_RCL
                                      ) and \
               fold_s==IN_OPEN_FILES:
                app.msg_box(f(_('Conflict "{}" and "Tree type" options.\n\nSee Help--Tree.'),IN_OPEN_FILES), app.MB_OK) 
                focused     = 'shtp'
                continue#while_fif
#           focused     = 'what'
            how_walk    =dict(                                  #NOTE: fif params
                 root       =root
                ,file_incl  =incl_s
                ,file_excl  =excl_s
                ,depth      =dept_n-1               # ['All', 'In folder only', '1 level', ...]
                ,skip_hidn  =skip_s in ('1', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                ,skip_binr  =skip_s in ('2', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
                ,sort_type  =apx.icase( sort_s=='0','' 
                                       ,sort_s=='1','date,desc' 
                                       ,sort_s=='2','date,asc' ,'')
                ,only_frst  =int(frst_s)
                ,enco       =enco_l[int(enco_s)].split(', ')
                )
            what_find   =dict(
                 find       =what_s
                ,mult       =False
                ,reex       =reex01=='1'
                ,case       =case01=='1'
                ,word       =word01=='1'
                )
            cllc_v      = cllc_l[int(cllc_s)]
            what_save   = dict(  # cllc_s in ['All matches', 'Match counts'==(btn=='!cnt'), 'Filenames']
                 count      = btn=='!cnt' or  cllc_v!=CLLC_FNAME
                ,place      = btn!='!cnt' and cllc_v==CLLC_MATCH
#               ,fragm      = btn!='!cnt' and cllc_v==CLLC_MATCH #and reex01=='0'
                ,lines      = btn!='!cnt' and cllc_v==CLLC_MATCH #and reex01=='0'
                )
            shtp_v      = shtp_l[int(shtp_s)]
            how_rpt     = dict(
                 totb   =    totb_l[int(totb_s)]
                ,sprd   =    sort_s=='0' and          shtp_v not in (SHTP_SHORT_R, SHTP_SHORT_RCL)
                ,shtp   =    shtp_v if sort_s=='0' or shtp_v     in (SHTP_SHORT_R, SHTP_SHORT_RCL) else SHTP_SHORT_R
                ,cntx   =    '1'==cntx_s
                ,algn   =    '1'==algn_s
                ,join   =    '1'==join_s
                )
            totb_s  = str(min(1, int(totb_s)))
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
            report_to_tab(                      #NOTE: run-report
                rpt_data
               ,rpt_info
               ,how_rpt
               ,how_walk, what_find, what_save
               ,progressor = progressor
               )
            progressor.set_progress(msg_rpt)
            ################################
            if 0<frgms and CLOSE_AFTER_GOOD:    break#while_fif
       #while_fif
   #def dlg_fif

last_ed_num = 0
def report_to_tab(rpt_data:dict, rpt_info:dict, rpt_type:dict, how_walk:dict, what_find:dict, what_save:dict, progressor=None):
    pass;                       RPTLOG and log('rpt_type={}',rpt_type)
    pass;                      #RPTLOG and log('rpt_data=¶{}',pf(rpt_data))
    pass;                      #RPTLOG and log('what_find={}',what_find)
    pass;                      #RPTLOG and log('what_save={}',what_save)
    
    global last_ed_num
    # Choose/Create tab for report
    rpt_ed  = None
    def create_new(title_ext='')->app.Editor:
        app.file_open('')
        new_ed  = ed
        new_ed.set_prop(app.PROP_ENC,       'UTF-8')
        new_ed.set_prop(app.PROP_TAB_TITLE, _('Results')+title_ext)  #??
        return new_ed
        
    title_ext   = f(' ({})', what_find['find'][:LEN_TRG_IN_TITLE])
    if False:pass
    elif rpt_type['totb']==TOTB_NEW_TAB:
        pass;                  #RPTLOG and log('!new',)
        rpt_ed  = create_new(title_ext)
    elif rpt_type['totb']==TOTB_USED_TAB: #if reed_tab: #or join_to_end:
        pass;                  #RPTLOG and log('!find used',)
        # Try to use prev or old
        olds    = []
        for h in app.ed_handles(): 
            try_ed  = app.Editor(h)
            ed_tag  = try_ed.get_prop(app.PROP_TAG, '')
            ed_id   = try_ed.get_prop(app.PROP_TAB_ID)
            ed_lxr  = try_ed.get_prop(app.PROP_LEXER_FILE, '')
            pass;              #RPTLOG and log('tit, ed_tag={}',(try_ed.get_prop(app.PROP_TAB_TITLE), ed_tag))
            if ed_tag.startswith('FiF_') or ed_lxr.upper() in lexers_l:
                olds+= [(ed_tag, ed_id)]
            if ed_tag == 'FiF_'+str(last_ed_num):
                rpt_ed  = try_ed
                pass;          #RPTLOG and log('found ed',)
                break #for h
        pass;                  #RPTLOG and log('found={}',)
        if rpt_ed is None and olds:
            rpt_ed  = apx.get_tab_by_id(max(olds)[1])  # last used ed
            pass;              #RPTLOG and log('get from olds',)
    else:
        # Try to use pointed
        the_title   = rpt_type['totb']
        cands       = [app.Editor(h) for h in app.ed_handles() 
                        if app.Editor(h).get_prop(app.PROP_TAB_TITLE)==the_title]
        rpt_ed      = cands[0] if cands else None
            
    rpt_ed  = create_new(title_ext) if rpt_ed is None else rpt_ed
    if rpt_ed.get_filename():
        rpt_ed.set_prop(app.PROP_TAB_TITLE, os.path.basename(rpt_ed.get_filename())+title_ext)  #??
    last_ed_num += 1
    rpt_ed.set_prop(app.PROP_TAG,       'FiF_'+str(last_ed_num))
    rpt_ed.focus()

    # Prepare tab
    if not rpt_type['join']:
        rpt_ed.set_text_all('')
        rpt_ed.attr(app.MARKERS_DELETE_ALL)

    # Fill tab
    rpt_ed.set_prop(app.PROP_LEXER_FILE,'')  #?? optimized?
    def mark_fragment(rw:int, cl:int, ln:int, to_ed=rpt_ed):
        pass;                  #RPTLOG and log('rw={}',rw)
        to_ed.attr(app.MARKERS_ADD
                , x=cl, y=rw, len=ln
                , **MARK_STYLE
                )
    def append_line(line:str, to_ed=rpt_ed)->int:
        ''' Append one line to end of to_ed. Return row of added line.'''
        pass;                  #RPTLOG and log('line={}',repr(line))
        line    = line.rstrip('\r\n')
        if to_ed.get_line_count()==1 and not to_ed.get_text_line(0):
            # Empty doc
            to_ed.set_text_line(0, line)
            return 0
        else:
            to_ed.set_text_line(-1, line)
        return to_ed.get_line_count()-2
       #def append_line
    def calc_width(rpt_data, algn, need_rcl, need_pth, only_fn):
        # Find max(len(*)) for path, row, col, ln
        fl_wd, rw_wd, cl_wd, ln_wd  = 0, 0, 0, 0
        if not algn:
            return fl_wd, rw_wd, cl_wd, ln_wd
        max_rw, max_cl, max_ln      = 0, 0, 0
        for path_d in rpt_data:
            path        = path_d['file']         if need_pth                else ''
            path        = os.path.basename(path) if need_pth and only_fn    else path
            fl_wd       = max(fl_wd , len(path))
            for item in path_d.get('items', ''):
                max_rw  = max(max_rw, item.get('row', 0))
                if not need_rcl:    continue#for item
                max_cl  = max(max_cl, item.get('col', 0))
                max_ln  = max(max_ln, item.get('ln',  0))
               #for item
           #for path_d
        rw_wd   = len(str(max_rw))
        cl_wd   = len(str(max_cl))
        ln_wd   = len(str(max_ln))
        return fl_wd, rw_wd, cl_wd, ln_wd
       #def calc_width
    def calc_width4depth(rpt_data, algn, need_rcl, need_pth, only_fn):
        # Find max(len(*)) for path, row, col, ln
        wds     = {}
#       fl_wd, rw_wd, cl_wd, ln_wd  = 0, 0, 0, 0
        if not algn:
            return wds # fl_wd, rw_wd, cl_wd, ln_wd
#       max_rw, max_cl, max_ln      = 0, 0, 0
        for path_d in rpt_data:
            dept        = 1+path_d.get('dept', 0)
            wds_d       = wds.setdefault(dept, {})
            path        = path_d['file']         if need_pth                else ''
            path        = os.path.basename(path) if need_pth and only_fn    else path
            wds_d['fl'] =         max(wds_d.get('fl', 0), len(path))
            for item in path_d.get('items', ''):
                wds_d['max_rw'] = max(wds_d.get('max_rw', 0), item.get('row', 0))
                if not need_rcl:    continue#for item
                wds_d['max_cl'] = max(wds_d.get('max_cl', 0), item.get('col', 0))
                wds_d['max_ln'] = max(wds_d.get('max_ln', 0), item.get('ln',  0))
               #for item
           #for path_d
        for wds_d in wds.values():
            wds_d['rw']    = len(str(wds_d.get('max_rw', 0)))
            wds_d['cl']    = len(str(wds_d.get('max_cl', 0)))
            wds_d['ln']    = len(str(wds_d.get('max_ln', 0)))
        return wds
       #def calc_width4depth
    onfn    = not what_save['count']
    shtp    = rpt_type['shtp']
    algn    = rpt_type['algn']
    need_rcl= shtp in (SHTP_SHORT_RCL, SHTP_MIDDL_RCL, SHTP_SPARS_RCL)
    need_pth= shtp in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_MIDDL_R, SHTP_MIDDL_RCL)
    only_fn = shtp in (SHTP_MIDDL_R, SHTP_MIDDL_RCL)
    pass;                       RPTLOG and log('algn, need_rcl, need_pth, only_fn={}',(algn, need_rcl, need_pth, only_fn))
    fl_wd, rw_wd, cl_wd, ln_wd  = calc_width(       rpt_data, algn, need_rcl, need_pth, only_fn)
    pass;                       RPTLOG and log('fl_wd,rw_wd,cl_wd,ln_wd={}',(fl_wd,rw_wd,cl_wd,ln_wd))
#   wds                         = calc_width4depth( rpt_data, algn, need_rcl, need_pth, only_fn)
#   pass;                       RPTLOG and log('wds={}',(wds))
    root    = how_walk['root']

    row4crt = append_line(f(_('{} "{}" in "{}" ({} matches in {} files)')
                            ,TOP_RES_SIGN
                            ,what_find['find']
                            ,root
                            ,rpt_info['frgms']
                            ,rpt_info['files']))
    for path_n, path_d in enumerate(rpt_data):                  #NOTE: rpt main loop
        if progressor and 0==path_n%37:
            pc  = int(100*path_n/len(rpt_data))
            progressor.set_progress( f(_('(ESC?) Reporting: {}%'), pc))
            if progressor.need_break():
                progressor.prefix += f(_('(Reporting stopped {}%)'), pc)
                append_line(         f('\t<{}>', progressor.prefix))
                break#for path
        has_cnt = 'count' in path_d and 0<path_d['count']     # skip count==0
        has_itm = 'items' in path_d
        path    = path_d['file']
        isfl    = path_d.get('isfl')
        pass;                   RPTLOG and log('path={}',path)
        if shtp     in (SHTP_MIDDL_R, SHTP_MIDDL_RCL, SHTP_SPARS_R, SHTP_SPARS_RCL) and \
            path!=root:
            if isfl:
                path= os.path.basename(path)
                pass;           RPTLOG and log('(basename)path={}',path)
            elif 'prnt' in path_d and path_d['prnt'] is not None:
                path= os.path.relpath(path, path_d['prnt']['file'])
                pass;           RPTLOG and log('(prnt-rel)path={}',path)
            else:
                path= os.path.relpath(path, root)
                pass;           RPTLOG and log('(root-rel)path={}',path)
        dept    = 1+path_d.get('dept', 0)
        c9dt    = c9*dept
        pass;                   RPTLOG and log('onfn,has_cnt,has_itm,c9dt={}',(onfn,has_cnt,has_itm,repr(c9dt)))
        if False:pass
        elif not has_cnt and onfn and not isfl: pass
        elif                 onfn and     isfl: append_line(c9dt+'<'+path+'>')
        elif     has_cnt and onfn:              append_line(c9dt+f('<{}>: #{}', path, path_d['count']))
        elif                 onfn:              append_line(c9dt+'<'+path+'>')
        elif not has_cnt and not has_itm:       pass
        elif     has_cnt and not has_itm:       append_line(c9dt+f('<{}>: #{}', path, path_d['count']))
        elif                     has_itm:
            items   = path_d['items']
            prefix  = ''
            new_row = -1
            pre_rw  = -1
            if shtp in (SHTP_SPARS_R, SHTP_SPARS_RCL):
                append_line(c9dt+f('<{}>: #{}', os.path.basename(path), len(items)))
                path= '' 
                c9dt= c9*(1+dept)
                pass;           RPTLOG and log('SPARS path,c9dt={}',(path,repr(c9dt)))
            for item in items:
                src_rw  = item.get('row', 0)
                if -1==src_rw:
                    # Separator
                    append_line(c9dt+'<>:')
                    continue#for path_n
                if  shtp not in (SHTP_SPARS_R, SHTP_SPARS_RCL) and \
                    src_rw==pre_rw and prefix and new_row!=-1 and 'col' in item and 'ln' in item:
                    # Add mark in old line
                    mark_fragment(new_row, item['col']+len(prefix), item['ln'], rpt_ed)
                    continue#for path_n

                src_cl  = item.get('col', -1)
                src_ln  = item.get('ln', -1)
                src_rw_s=                       str(1+src_rw)
                src_cl_s= '' if -1==src_cl else str(1+src_cl)
                src_ln_s= '' if -1==src_ln else str(  src_ln)
                if algn:
                    path    = path.ljust(    fl_wd, ' ')
                    src_rw_s= src_rw_s.rjust(rw_wd, ' ')
                    src_cl_s= src_cl_s.rjust(cl_wd, ' ')
                    src_ln_s= src_ln_s.rjust(ln_wd, ' ')
                prefix  = c9dt+f('<{}({}:{}:{})>: ', path, src_rw_s, src_cl_s, src_ln_s)    \
                            if      need_pth and     need_rcl else                          \
                          c9dt+f('<{}({})>: '      , path, src_rw_s                    )    \
                            if      need_pth and not need_rcl else                          \
                          c9dt+f('<({}:{}:{})>: '  ,       src_rw_s, src_cl_s, src_ln_s)    \
                            if  not need_pth and     need_rcl else                          \
                          c9dt+f('<({})>: '        ,       src_rw_s                    )
                new_row = append_line(prefix+item.get('line',''))
                pass;          #RPTLOG and log('new_row, prefix={}',(new_row, prefix))
                if 'col' in item and 'ln' in item:
                    mark_fragment(new_row, item['col']+len(prefix), item['ln'], rpt_ed)
                pre_rw  = src_rw
               #for item              
 
    pass;                       # Append work data to report
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.set_text_line(-1, '')
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.insert(0,rpt_ed.get_line_count()-1, json.dumps(rpt_type, indent=2))
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.insert(0,rpt_ed.get_line_count()-1, json.dumps(rpt_data, indent=2))

    # AT-hack to update folding
    pass;                       RPTLOG and log('?? set lxr',)
    rpt_ed.set_prop(app.PROP_LEXER_FILE, FIF_LEXER)
    pass;                       RPTLOG and log('ok set lxr',)
    line0 = rpt_ed.get_text_line(0)
    rpt_ed.set_text_line(0, '')
    rpt_ed.set_text_line(0, line0)
        
    pass;                      #RPTLOG and log('row4crt={}',row4crt)
    rpt_ed.set_caret(0, row4crt)
#   if rpt_type['join'] and FOLD_PREV_RES:
#       pass;                   RPTLOG and log('?? fold',)
##       fold_all_found_up(rpt_ed, TOP_RES_SIGN)
#       rpt_ed.cmd(cmds.cCommand_FoldAll)
##       rpt_ed.cmd(cmds.cmd_FoldingUnfoldAtCurLine)
##       rpt_ed.set_caret(0, row4crt)
   #def report_to_tab
       
def nav_to_src(where:str, how_act='move'):
    """ Try to open file and navigate to row[+col+sel].
        FiF-res structure variants
            +text about finding
            ¬<abs-path>
            ¬<abs-path>: info
            ¬<abs-path(row)>: info
            ¬<abs-path(row:col)>: info
            ¬<abs-path(row:col:len)>: info
            +text about finding
            ¬<dir>
            ¬¬<rel-path(row)>: info
            ¬¬<rel-path(row:col)>: info
            ¬¬<rel-path(row:col:len)>: info
            +text about finding
            ¬<dir>
            ¬¬<rel-path>
            ¬¬¬<(row)>: info
            ¬¬¬<(row:col)>: info
            ¬¬¬<(row:col:len)>: info
    """
    pass;                   NAVLOG and log('where, how_act={}',(where, how_act))
    crts    = ed.get_carets()
    if len(crts)>1:         return app.msg_status(_("Command doesn't work with multi-carets"))
        
    reSP    = re.compile(  r'(?P<S>\t+)'        # Shift !
                          r'<(?P<P>[^>]+)>')    # Path  !
    reSPR   = re.compile(  r'(?P<S>\t+)'        # Shift !
                          r'<(?P<P>[^>]+)'      # Path  !
                         r'\((?P<R> *\d+)'      # Row   !
                           r'(?P<C>: *\d+)?'    # Col?
                           r'(?P<L>: *\d+)?\)>')# Len?
    reSR    = re.compile(  r'(?P<S>\t+)'        # Shift !
                        r'<\((?P<R> *\d+)'      # Row   !
                           r'(?P<C>: *\d+)?'    # Col?
                           r'(?P<L>: *\d+)?\)>')# Len?
    def parse_line(line:str, what:str)->list:                   #NOTE: nav parse_line
        pass;               NAVLOG and log('what, line={}',(what, line))
        if what=='SP':
            mtSP    = reSP.search(line)
            if mtSP:
                gdct= mtSP.groupdict()
                pass;       NAVLOG and log('ok mtSP gdct={}', gdct)
                return mtSP.group(0),   gdct['S'], gdct['P']
            return [None]*3
        mtSR   = reSR.search(line)
        if mtSR:
            gdct= mtSR.groupdict()
            pass;           NAVLOG and log('ok mtSR gdct={}', gdct)
            cl  = gdct['C']
            ln  = gdct['L']
            return mtSR.group(0),   gdct['S'], '' \
                ,int(gdct['R'])-1, int(cl[1:])-1 if cl else -1, int(ln[1:]) if ln else -1
        mtSPR   = reSPR.search(line)
        if mtSPR:   
            gdct= mtSPR.groupdict()
            pass;           NAVLOG and log('ok mtSPR gdct={}', gdct)
            cl  = gdct['C']
            ln  = gdct['L']
            return mtSPR.group(0),  gdct['S'], gdct['P'].rstrip() \
                ,int(gdct['R'])-1, int(cl[1:])-1 if cl else -1, int(ln[1:]) if ln else -1
        mtSP    = reSP.search(line)
        if mtSP:
            gdct= mtSP.groupdict()
            pass;           NAVLOG and log('ok mtSP gdct={}', gdct)
            return mtSP.group(0),   gdct['S'], gdct['P'], -1, -1, -1
        return [None]*6
       #def parse_line
    row     = crts[0][1]
    line    = ed.get_text_line(row)
    full,   \
    shft,   \
    path,   \
    rw,cl,ln= parse_line(line, 'all')
    if not full:            return  app.msg_status(f(_("At the line {} no data for navigation"), 1+row))
    pass;                   NAVLOG and log('full={}', full)
    pass;                   NAVLOG and log('shft, path, rw, cl, ln={}', (shft, path, rw, cl, ln))
    def open_and_nav(path:str, rw=-1, cl=-1, ln=-1):
        pass;               NAVLOG and log('path,rw,cl,ln={}',(path,rw,cl,ln))
        op_ed   = None
        if path.startswith(_('tab:')):
            tab_id  = int(path.split('/')[0].split(':')[1])
            pass;           NAVLOG and log('tab_id={}',(tab_id))
            op_ed   = apx.get_tab_by_id(tab_id)
            if not op_ed:   return  app.msg_status(f(_("No tab for navigation"), ))
        elif not os.path.isfile(path):
            pass;           NAVLOG and log('not isfile',())
            return
        the_ed_id   = ed.get_prop(app.PROP_TAB_ID)
        the_ed_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
        pass;               NAVLOG and log('the_ed_id={}',(the_ed_id))
#       ed.set_prop(app.PROP_TAG, 'FiF=open_and_nav')
        # Already opened?
        if not op_ed:
            for h in app.ed_handles(): 
                t_ed  = app.Editor(h)
                if t_ed.get_filename() and os.path.samefile(path, t_ed.get_filename()):
                    op_ed   = t_ed
                    pass;   NAVLOG and log('found filename',())
                    break
        if not op_ed:
            # Open it
            ed_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
            grps    = apx.get_groups_count() # len({app.Editor(h).get_prop(app.PROP_INDEX_GROUP) for h in app.ed_handles()})
            op_grp  = apx.icase(False,-1
                            ,app.app_proc(app.PROC_GET_GROUPING,'')==app.GROUPS_ONE , -1
                            ,where=='same'                                          , -1
                            ,where=='next'                                          , (ed_grp+1)%grps
                            ,where=='prev'                                          , (ed_grp-1)%grps
                            )
            pass;           NAVLOG and log('ed_grp, grps, op_grp={}',(ed_grp, grps, op_grp))
            app.file_open(path, op_grp)
            op_ed   = ed
        op_ed.focus()
        if False:pass
        elif rw==-1:
            pass
        elif cl==-1 and how_act=='move':
            op_ed.set_caret(0,      rw)
        elif cl==-1:
            l_ln= len(op_ed.get_text_line(rw))
            op_ed.set_caret(0,   rw,   l_ln,  rw)   # inverted sel to show line head if window is narrow 
        elif ln==-1:
            op_ed.set_caret(cl,     rw)
        else:
            op_ed.set_caret(cl+ln,  rw,     cl, rw)
        if rw!=-1:
            top_row = max(0, rw - max(5, apx.get_opt('find_indent_vert', ed_cfg=op_ed)))
            op_ed.set_prop(app.PROP_LINE_TOP, str(top_row))

        if how_act=='move' or the_ed_grp == ed.get_prop(app.PROP_INDEX_GROUP):
            op_ed.focus()
        else:
            the_ed  = apx.get_tab_by_id(the_ed_id)
            the_ed.focus()
       #def open_and_nav
    pass;                   NAVLOG and log('path={}', (path))
    if os.path.isfile(path) or path.startswith(_('tab:')):
        open_and_nav(path, rw, cl, ln)
        return
#   testings="""
#+Search for "smtH" in "c:\temp\try-ff" (10 matches in 7 files)
#<c:\temp\try-ff\s1\t1-s1.txt>
#	<(3)>: SMTH
#	<(3:2)>: SMTH
#	<(3:2:2)>: SMTH
#+Search for "smtH" in "c:\temp\try-ff" (10 matches in 7 files)
#<c:\temp\try-ff\s1>
#	<t1-s1.txt(5)>: SMTH
#	<t1-s1.txt(5:4)>: SMTH
#	<t1-s1.txt(5:4:2)>: SMTH
#+Search for "smtH" in "c:\temp\try-ff" (10 matches in 7 files)
#<c:\temp\try-ff\s1\t1-s1.txt(3)>: SMTH
#+Search for "smtH" in "c:\temp\try-ff" (10 matches in 7 files)
#<c:\temp\try-ff\s1\t1-s1.txt>: #4
#+Search for "smtH" in "c:\temp\try-ff" (7 matches in 7 files)
#<c:\temp\try-ff\s1\t2-s1.txt>
#   """
    # Try to build path from prev lines
    for t_row in range(row-1, -1, -1):                          #NOTE: nav build path
        t_line  = ed.get_text_line(t_row)
        pass;               NAVLOG and log('t_row, t_line={}', (t_row, t_line))
        if t_line.startswith('+'):                              break#for t_row         as top
        if len(shft) <= len(t_line)-len(t_line.lstrip('\t')):   continue#for t_row      as same level
#       if row-step < 0:    return app.msg_status(f(_("At the line {} no data for navigation"), 1))
        t_fll,  \
        t_sft,  \
        t_pth   = parse_line(t_line, 'SP')
        pass;               NAVLOG and log('t_sft, t_pth={}', (t_sft, t_pth))
        if len(t_sft) == len(shft): 
            pass;           NAVLOG and log('skip: t_sft==shft', ())
            continue#for t_row
        if len(t_sft) >  len(shft):
            pass;           NAVLOG and log('bad: t_sft>shft', ())
            return app.msg_status(f(_("At the line {} bad data for navigation"), 1+t_row))
        path    = os.path.join(t_pth, path) if path else t_pth
        pass;               NAVLOG and log('new path={}', (path))
        if os.path.isfile(path):
            open_and_nav(path, rw, cl, ln)
            return
        shft    = t_sft
       #for t_row
    return app.msg_status(f(_("At the line {} no data for navigation"), 1+row))
   #def nav_to_src

#def fold_all_found_up(rpt_ed:app.Editor, what:str):
#   user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
#   # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrapp
##   rpt_ed.set_caret(0, 0)
#   rpt_ed.cmd(    cmds.cmd_FinderAction, chr(1).join(['findprev', what, '', 'cf']))
#   pass;                       LOG and log('row,sel={}',(rpt_ed.get_carets()[0][1], rpt_ed.get_text_sel()))
##   while rpt_ed.get_text_sel():
#   for i in range(2):  ##!!
#       pass;                   LOG and log('row,sel={}',(rpt_ed.get_carets()[0][1], rpt_ed.get_text_sel()))
#       rpt_ed.set_caret(1, rpt_ed.get_carets()[0][1])
#       rpt_ed.cmd(cmds.cmd_FoldingFoldAtCurLine)
#       rpt_ed.cmd(cmds.cmd_FinderAction, chr(1).join(['findprev', what, '', 'cf']))
#   app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)
#  #def fold_all_found_up

##############################################################################
def find_in_files(how_walk:dict, what_find:dict, what_save:dict, how_rpt:dict, progressor=None)->(list, dict):
    """ Scan files by how_walk:
            'root'         !str         disk folder or <in open files> to scan tabs
            'depth'         int(-1)    -1=all, 0=only root
            'file_incl'    !str
            'file_excl'     str('')
            'sort_type'     str('')     '','date,desc','date,asc'
            'only_frst'     int(0)      0=all
            'skip_hidn'     bool(T)
            'skip_binr'     bool(F) 
            'skip_size'     int(0)      0=all Kbyte
            'enco'          [str]       ['UTF-8']
        to find fragments by what_find:
            'find'         !str
            'mult'          bool(F)     Multylines 
            'reex'          bool(F)     
            'case'          bool(F)     
            'word'          bool(F)     
        and to save info by what_save:
            'count'         bool(T)     Need counts
            'place'         bool(T)     Need places
            'fragm'         bool(F)     Need fragments
            'lines'         bool(T)     Need lines with fragments
        From par how_rpt use keys: 
            'sprd'          bool(F)     Separate dirs
            'cntx'          bool(F)     Append around lines
        Return 
            [{file:'path'
             ,isfl=<True for file>} if not what_save['count']
            ,{file:'path'
             ,isfl=<True for file>
             ,count:int}                if what_save['count'] and not what_save['place']
            ,{file:'path'
             ,isfl=<True for file>
             ,count:int                 if what_save['count']
             ,items:[
                {row:N,col:N,ln:N}      if what_save['place'] and not what_save['fragm']
             ]}
            ,{file:'path'
             ,isfl=<True for file>
             ,count:int                 if what_save['count']
             ,items:[
                {row:N,col:N,ln:N       if what_save['place']
                ,fragm:'text'}          if what_save['fragm']
             }
            ,{file:'path'
             ,isfl=<True for file>
             ,count:int                 if what_save['count']
             ,items:[
                {row:N,col:N,ln:N       if what_save['place']
                ,fragm:'text'           if what_save['fragm']
                ,lines:'line'           if what_save['lines']
                }
             }
            ,...]
    """
    pass;                      #FNDLOG and log('ESC_FULL_STOP={}',ESC_FULL_STOP)
    pass;                      #FNDLOG and log('how_walk={}',pf(how_walk))
    pass;                       FNDLOG and log('what_find={}',pf(what_find))
    pass;                       FNDLOG and log('what_save={}',pf(what_save))

    rsp_l   = []
    rsp_i   = dict(cllc_files=0
                  ,cllc_stopped=False
                  ,find_stopped=False
                  ,brow_files=0, files=0, frgms=0)

    root    = how_walk['root']
    files,  \
    cllc_stp= collect_tabs(how_walk) \
                if root==IN_OPEN_FILES else \
              collect_files(how_walk, progressor)
    if cllc_stp and ESC_FULL_STOP:   return [], {}
    pass;                      #FNDLOG and log('#collect_files={}',len(files))
    pass;                      #FNDLOG and log('files={}',pf(files))
    rsp_i['cllc_files']     = len(files)
    rsp_i['cllc_stopped']   = cllc_stp
    
    pttn_s  = what_find['find']
    mult_b  = what_find['mult']
    case_b  = what_find['case']
    flags   = re.M if mult_b else 0 \
            +    0 if case_b else re.I
    if not    what_find['reex']:
        if    what_find['word'] and re.match('^\w+$', pttn_s):
            pttn_s  = r'\b'+pttn_s+r'\b'
        else:
            pttn_s  = re.escape(pttn_s)
    pass;                      #FNDLOG and log('pttn_s, flags={}',(pttn_s, flags))
    pttn    = re.compile(pttn_s, flags)

    cnt_b   = what_save['count']
    plc_b   = what_save['place']
    lin_b   = what_save['lines']
    spr_dirs= how_rpt['sprd']

    cntx    = how_rpt['cntx']
    ext_lns = apx.get_opt('fif_context_width', 1) if cntx else 0

    enco_l  = how_walk.get('enco', ['UTF-8'])
    def detect_encoding(path, detector):
        detector.reset()
        with open(path, 'rb') as h_path:
            line = h_path.readline()
            lines= 1
            bytes= len(line)
            while line:
                detector.feed(line)
                if detector.done: break
                line = h_path.readline()
                lines+= 1
                bytes+= len(line)
        detector.close()
        pass;                      #LOG and log('lines={}, bytes={} detector.done={}, detector.result={}'
                                   #            ,lines, bytes, detector.done, detector.result)
        encoding    = detector.result['encoding'] if detector.done else locale.getpreferredencoding()
        return encoding
       #def detect_encoding
    detector= UniversalDetector() if ENCO_DETD in enco_l else None
    rpt_enc_fail= apx.get_opt('fif_log_encoding_fail', False)

    def find_for_body(   body:str, dept:int, rsp_l:list, rsp_i:list):
        if pttn.search(body):
            rsp_l           += [dict(dept=dept, file=path, isfl=True)]
            rsp_i['files']  += 1
            rsp_i['frgms']  += 1
            return 1
        return 0
    def find_for_lines(lines:list, dept:int, rsp_l:list, rsp_i:list)->int:
        count   = 0
        items   = []
        for ln,line in enumerate(lines):
            line    = line.rstrip(c10+c13)
            mtchs   = list(pttn.finditer(line))
            if not plc_b:
                # Only counting
                count  += len(mtchs)
            else:
                for mtch in mtchs:
                    count  += 1
                    for ext_ln in range(max(0, ln-ext_lns), ln):
                        item    =       dict(row=ext_ln)
                        if lin_b:  item.update(dict(line=lines[ext_ln]))
                        items  += [item]
                    item        =       dict(row=ln, col=mtch.start(), ln=mtch.end()-mtch.start())
                    if lin_b:      item.update(dict(line=line))
                    items      += [item]
                    for ext_ln in range(ln+1, min(len(lines), ln+ext_lns+1)):
                        item    =       dict(row=ext_ln)
                        if lin_b:  item.update(dict(line=lines[ext_ln]))
                        items  += [item]
                    if ext_lns>0:
                        # Separator
                        items  += [dict(row=-1, line='')]
           #for line
        if not count:
            # No matches
            return count #continue#for path
        if not plc_b:
            # Only counting
            rsp_l  += [dict( dept=dept
                            ,file=path
                            ,isfl=True
                            ,count=count)]
        else:
            rsp_l  += [dict( dept=dept
                            ,file=path
                            ,isfl=True
                            ,count=count
                            ,items=items)]
        rsp_i['files']  += 1
        rsp_i['frgms']  += count
        return count
       #def find_for_lines

    if root==IN_OPEN_FILES:
        # Find in tabs
        for path, h_tab in files:
            try_ed  = app.Editor(h_tab)
            if not cnt_b:
                # Only path finding
                find_for_body(try_ed.get_text_all()                                         , 0, rsp_l, rsp_i)
                continue#for path
            find_for_lines([try_ed.get_text_line(r) for r in range(try_ed.get_line_count())], 0, rsp_l, rsp_i)
           #for path
        return rsp_l, rsp_i
        
    def get_prnt_path_dct(path, tree):
#       while True:
        for i in range(25):##!!
            if not path:        return None
            if path in tree:    return tree[path]
            path = os.path.dirname(path)
        return None
    tree4rsp= {}                # {path:rsp_l[?]} 
                                # (1) store dir-items, 
                                # (2) tree-parent-links in item of rsp_l to sum 'count' for dir
    if spr_dirs:    # Separate dir in rsp
        tree4rsp[root]  = dict(dept=0, file=root, count=0, prnt=None)
        rsp_l          += [tree4rsp[root]]
        pass;                  #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
    
    pass;                       t=log('?? files (==',) if LOG else 0
#   pass;                       t=log('?? files (==',) if FNDLOG else 0
    
    for path_n, path in enumerate(files):                       #NOTE: scan main loop
        pass;                   FNDLOG and log('path_n, path={}',(path_n, path))
        if progressor and 0==path_n%17:
            pc  = int(100*path_n/len(files))
            progressor.set_progress( f(_('(ESC?) Seaching: {}% (found {} match(es) in {} file(s))')
                                    , pc
                                    , rsp_i['frgms'], rsp_i['files']))
            if progressor.need_break():
                if ESC_FULL_STOP:   return [], {}
                rsp_i['find_stopped']   = True
                progressor.prefix += f(_('(Finding stopped {}%)'), pc)
                break#for path
        
        prntdct = None
        if spr_dirs:# Separate dir in rsp
            # For dir with path need to add item in rsp_l
            #   NB! Rely to Up-Down dir sequence in files
            pathdir = os.path.dirname(path)
            pass;              #FNDLOG and log('?path,pathdir={}',(path,pathdir))
            prntdct = tree4rsp.get(pathdir)
            if not prntdct:
                prntdct = get_prnt_path_dct(pathdir, tree4rsp)
                pass;          #FNDLOG and log('prntdct={}',prntdct)
                if not prntdct:
                    pass;      #FNDLOG and log('no prntdct=',())
                if prntdct:
                    dct     = dict(dept=1+prntdct['dept'], file=pathdir, count=0, prnt=prntdct)
                    tree4rsp[pathdir]= dct
                    rsp_l  += [dct]
                    prntdct = dct
                pass;          #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
        dept    = 1+prntdct['dept'] if prntdct else 0
        pass;                  #FNDLOG and log('dept={}',dept)
        # Find in file
        h_path  = None
        encd    = ''
        for enco_n, enco_s in enumerate(enco_l):
            if enco_s==ENCO_DETD:
                enco_s  = detect_encoding(path, detector)
                enco_l[enco_n] = enco_s
            try:
                with open(path, encoding=enco_s) as h_path:
                    if not cnt_b:
                        # Only path finding
                        count   = find_for_body( h_path.read()      , dept, rsp_l, rsp_i)
#                       break#for enco_n
                    else:
                        count   = find_for_lines(h_path.readlines() , dept, rsp_l, rsp_i)
                    rsp_i['brow_files']     += 1
                    if not count:
                        break#for enco_n
                    if prntdct:
        #               prntdct['count']+=count
        #               prntdct = prntdct['prnt']
                        for i in range(25):  ##!!
                            if not prntdct:  break#for i
        #               while prntdct:
                            prntdct['count']+=count
                            prntdct  = prntdct['prnt']
                        pass;  #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
                    break#for enco_n
                   #with
            except Exception as ex:
                if rpt_enc_fail and enco_n == len(enco_l)-1:
                    print(f(_('Cannot read "{}" (encoding={}/{}): {}'), path, enco_s, enco_l, ex))
           #for encd_n
       #for path
    pass;                      #t=None
    pass;                      #FNDLOG and log('rsp_l=¶{}',pf(rsp_l))
    pass;                       LOG and log('ok files ==) #rsp_i={}',rsp_i)
#   pass;                       FNDLOG and log('ok files ==) #rsp_i={}',rsp_i)
    return rsp_l, rsp_i
   #def find_in_files

def prep_filename_masks(mask:str)->list:
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
   #def prep_filename_masks
    
def collect_tabs(how_walk:dict)->list:
    """ how_walk keys:
            'file_incl'    !str
            'file_excl'     str('')
    """
    incl    = how_walk[    'file_incl'    ].strip()
    excl    = how_walk.get('file_excl', '').strip()
    incls   = prep_filename_masks(incl)
    excls   = prep_filename_masks(excl)
    rsp     = []
    for h_tab in app.ed_handles(): 
        try_ed  = app.Editor(h_tab)
        filename= try_ed.get_filename()
        title   = try_ed.get_prop(app.PROP_TAB_TITLE, '')
        tab_id  = try_ed.get_prop(app.PROP_TAB_ID, '')
        if not      any(map(lambda cl:fnmatch(title, cl), incls)):   continue#for h
        if excl and any(map(lambda cl:fnmatch(title, cl), excls)):   continue#for h
        path    = filename if filename else f(_('tab:')+'{}/{}', tab_id, title)
        rsp    += [(path, h_tab)]
       #for h_tab
    return rsp, False
   #def collect_tabs

def collect_files(how_walk:dict, progressor=None)->list:        #NOTE: cllc
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
        Return
            [path], stoped
    """
    pass;                       t=log('>>(:)how_walk={}',how_walk) if LOG else 0 
    root    = how_walk['root']
    if not os.path.isdir(root): return [], False
    rsp     = []
    stoped  = False
    incl    = how_walk[    'file_incl'    ].strip()
    excl    = how_walk.get('file_excl', '').strip()
    depth   = how_walk.get('depth', -1)
    hidn    = how_walk.get('skip_hidn', True)
    binr    = how_walk.get('skip_binr', False)
    size    = how_walk.get('skip_size', apx.get_opt('fif_skip_file_size_more_Kb', 0))
    frst    = how_walk.get('only_frst', 0)
    sort    = how_walk.get('sort_type', '')
    incls   = prep_filename_masks(incl)
    excls   = prep_filename_masks(excl)
    pass;                      #LOG and log('incls={}',incls)
    pass;                      #LOG and log('excls={}',excls)
    dir_n   = 0
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root)):
        pass;                  #LOG and log('dirpath, #filenames={}',(dirpath, len(filenames)))
        pass;                  #LOG and log('dirpath, dirnames, filenames={}',(dirpath, dirnames, filenames))
        dir_n   += dir_n
        if progressor and 0==dir_n%13:
            progressor.set_progress(f(_('(ESC?)(#{}) Picking files in: {}'), len(rsp), dirpath))
            if progressor.need_break():
                if ESC_FULL_STOP:   return [], True
                stoped  = True
                progressor.prefix += _('(Picking stopped)')
                break#for dirpath
        # Cut links
        dir4cut     = [dirname for dirname in dirnames if os.path.islink(os.path.join(dirpath, dirname))]
        for dirname in dir4cut:
            dirnames.remove(dirname)
        if hidn:
            # Cut hidden dirs
            dir4cut = [dirname for dirname in dirnames if is_hidden_file(os.path.join(dirpath, dirname))]
            for dirname in dir4cut:
                dirnames.remove(dirname)
            
        walk_depth  = 0 \
                        if os.path.samefile(dirpath, root) else \
                      1 +  os.path.relpath( dirpath, root).count(os.sep)
        pass;                  #LOG and log('depth,walk_depth={}',(depth,walk_depth))
        if walk_depth>depth>0:
            pass;              #LOG and log('skip by >depth',())
            dirnames.clear()
            continue#for dirpath
        for filename in filenames:
            if not      any(map(lambda cl:fnmatch(filename, cl), incls)):   continue#for filename
            if excl and any(map(lambda cl:fnmatch(filename, cl), excls)):   continue#for filename
            path    = os.path.join(dirpath, filename)
            if          os.path.islink(path):                               continue#for filename
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
    pass;                       LOG and log('|rsp|, stoped={}',(len(rsp), stoped))
    return rsp, stoped
   #def collect_files

BLOCKSIZE = apx.get_opt('fif_read_head_size', 1024)
TEXTCHARS = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
def is_birary_file(path:str, blocksize=BLOCKSIZE, def_ans=None)->bool:
    if not os.path.isfile(path):    return def_ans
    try:
        block   = open(path, 'br').read(blocksize)
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
def is_hidden_file(path:str)->bool:
    """ Cross platform hidden file/dir test  """
    if os.name == 'nt':
        # For Windows use file attribute.
        attrs   = ctypes.windll.kernel32.GetFileAttributesW(path)
        return attrs & FILE_ATTRIBUTE_HIDDEN

    # For *nix use a '.' prefix.
    return os.path.basename(path).startswith('.')
   #def is_hidden_file

class ProgressAndBreak:
    """ Helper for 
        - Show progress of working
        - Allow user to stop long procces
    """
    def __init__(self):
        self.prefix = ''
        app.app_proc(app.PROC_SET_ESCAPE, '0')

    def set_progress(self, msg:str):
        app.msg_status(self.prefix+msg, process_messages=True)

    def need_break(self, with_request=False, process_hint=_('Stop?'))->bool:
        was_esc = app.app_proc(app.PROC_GET_ESCAPE, '')
        app.app_proc(app.PROC_SET_ESCAPE, '0')
        if was_esc and with_request:
            if app.ID_YES == app.msg_box(process_hint, app.MB_YESNO):
                return True
            was_esc = False
        return was_esc
   #class ProgressAndBreak

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
[ ][kv-kv][29apr16] find_in_ed must pass to dlg title + tab_id
[+][kv-kv][29apr16] extract 'pres' to dlg_preset
[-][kv-kv][04may16] BUG? Encoding ex breaks reading file ==> next encoding doubles stat data
[ ][a1-kv][10may16] Replace in files
[ ][at-kv][10may16] Checks for preset
[ ][kv-kv][11may16] Try to save last active control
'''