''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '2.3.16 2019-02-12'
ToDo: (see end of file)
'''

import  re, os, sys, locale, json, collections, traceback, time
from    datetime        import datetime, timedelta
from    fnmatch         import fnmatch

import  cudatext            as app
from    cudatext        import ed
import  cudax_lib           as apx
from    .cd_plug_lib        import *
from    .chardet.universaldetector import UniversalDetector

OrdDict = collections.OrderedDict

pass;                           Tr.tr   = Tr(apx.get_opt('fif_log_file', '')) if apx.get_opt('fif_log_file', '') else Tr.tr
pass;                           LOG     = (-1== 1)         or apx.get_opt('fif_LOG'   , False) # Do or dont logging.
pass;                           FNDLOG  = (-2== 2) and LOG or apx.get_opt('fif_FNDLOG', False)
pass;                           RPTLOG  = (-3== 3) and LOG or apx.get_opt('fif_RPTLOG', False)
pass;                           NAVLOG  = (-4== 4) and LOG or apx.get_opt('fif_NAVLOG', False)
pass;                           DBG_DATA_TO_REPORT  =         apx.get_opt('fif_DBG_data_to_report', False)
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)
pass;                           ##!! waits correction

_   = get_translation(__file__) # I18N

_statusbar       = None
def use_statusbar(st):
    global _statusbar
    _statusbar   = st
def msg_status(msg, process_messages=True):
    pass;                      #log('###',())
    if _statusbar:
        app.statusbar_proc(_statusbar, app.STATUSBAR_SET_CELL_TEXT, tag=1, value=msg)
        if process_messages:
            app.app_idle()
    else:
        app.msg_status(msg, process_messages)

RPT_FIND_SIGN   = _('+Search')
RPT_REPL_SIGN   = _('+Replace')

IN_PROJ_FOLDS   = _('<Project Folders>')
IN_OPEN_FILES   = _('<Open Files>')
root_is_proj    = lambda rt:    (rt[:2]+rt[-1]).upper() in ('<P>')
root_is_tabs    = lambda rt:    (rt[:2]+rt[-1]).upper() in ('<O>', '<T>')
roots_is_proj   = lambda rts:1==len(rts) and root_is_proj(rts[0])
roots_is_tabs   = lambda rts:1==len(rts) and root_is_tabs(rts[0])
TOTB_USED_TAB   = _('<prior tab>')
TOTB_NEW_TAB    = _('<new tab>')
SHTP_SHORT_R    = _('path(r):line')
SHTP_SHORT_RCL  = _('path(r:c:l):line')
SHTP_SHRTS_R    = _('path/(r):line')
SHTP_SHRTS_RCL  = _('path/(r:c:l):line')
SHTP_MIDDL_R    = _('dir/file(r):line')
SHTP_MIDDL_RCL  = _('dir/file(r:c:l):line')
SHTP_SPARS_R    = _('dir/file/(r):line')
SHTP_SPARS_RCL  = _('dir/file/(r:c:l):line')
ENCO_DETD       = _('detect')

lexers_l        = apx.get_opt('fif_lexers'                  , ['Search results', 'FiF'])
FIF_LEXER       = apx.choose_avail_lexer(lexers_l) #select_lexer(lexers_l)
lexers_l        = list(map(lambda s: s.upper(), lexers_l))
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
def api_reload_opts():
    global                      LOG, FNDLOG, RPTLOG, NAVLOG, DBG_DATA_TO_REPORT
    pass;                       LOG     = (-1== 1)         or apx.get_opt('fif_LOG'   , False) # Do or dont logging.
    pass;                       FNDLOG  = (-2== 2) and LOG or apx.get_opt('fif_FNDLOG', False)
    pass;                       RPTLOG  = (-3== 3) and LOG or apx.get_opt('fif_RPTLOG', False)
    pass;                       NAVLOG  = (-4== 4) and LOG or apx.get_opt('fif_NAVLOG', False)
    pass;                       DBG_DATA_TO_REPORT  =         apx.get_opt('fif_DBG_data_to_report', False)

    global FIF_LEXER,lexers_l,USE_SEL_ON_START,ESC_FULL_STOP,REPORT_FAIL,FOLD_PREV_RES,LEN_TRG_IN_TITLE
    global BLOCKSIZE,CONTEXT_WIDTH,SKIP_FILE_SIZE,AUTO_SAVE,FOCUS_TO_RPT,SAVE_REQ_TO_RPT,TAB_SIZE_IN_RPT
    global MARK_FIND_STYLE,MARK_TREPL_STYLE,MARK_FREPL_STYLE
    global ALWAYS_EXCL
    lexers_l        = apx.get_opt('fif_lexers'                  , ['Search results', 'FiF'])
    FIF_LEXER       = apx.choose_avail_lexer(lexers_l) #select_lexer(lexers_l)
    lexers_l        = list(map(lambda s: s.upper(), lexers_l))
    USE_SEL_ON_START= apx.get_opt('fif_use_selection_on_start'  , False)
    ESC_FULL_STOP   = apx.get_opt('fif_esc_full_stop'           , False)
    REPORT_FAIL     = apx.get_opt('fif_report_no_matches'       , False)
    FOLD_PREV_RES   = apx.get_opt('fif_fold_prev_res'           , False)
    LEN_TRG_IN_TITLE= apx.get_opt('fif_len_target_in_title'     , 10)
    BLOCKSIZE       = apx.get_opt('fif_read_head_size(bytes)'   , apx.get_opt('fif_read_head_size', 1024))
    CONTEXT_WIDTH   = apx.get_opt('fif_context_width'           , 1)
    SKIP_FILE_SIZE  = apx.get_opt('fif_skip_file_size_more_Kb'  , 0)
    AUTO_SAVE       = apx.get_opt('fif_auto_save_if_file'       , False)
    FOCUS_TO_RPT    = apx.get_opt('fif_focus_to_rpt'            , True)
    SAVE_REQ_TO_RPT = apx.get_opt('fif_save_request_to_rpt'     , False)
    TAB_SIZE_IN_RPT = apx.get_opt('fif_lexer_auto_tab_size'     , 2)
    MARK_FIND_STYLE = apx.get_opt('fif_mark_style'              , {'borders':{'bottom':'dotted'}})
    MARK_TREPL_STYLE= apx.get_opt('fif_mark_true_replace_style' , {'borders':{'bottom':'solid'}})
    MARK_FREPL_STYLE= apx.get_opt('fif_mark_false_replace_style', {'borders':{'bottom':'wave'},'color_border':'#777'})
    MARK_FIND_STYLE = fit_mark_style_for_attr(MARK_FIND_STYLE)
    MARK_TREPL_STYLE= fit_mark_style_for_attr(MARK_TREPL_STYLE)
    MARK_FREPL_STYLE= fit_mark_style_for_attr(MARK_FREPL_STYLE)
    ALWAYS_EXCL     = apx.get_opt('fif_always_not_in_files'     , '/.svn /.git /.hg /.idea')
   #def api_reload_opts
api_reload_opts()
if 'sw'==app.__name__:
    FOLD_PREV_RES   = False

REQ_KEY = (' '*100)+'_req_info_='
def report_extract_request(red):
    """ Extract first(!) request info from the report.
        If no req-info return ('', None)
        Return  (what, opts)
    """
    line_req    = red.get_text_line(0)      # First
    if REQ_KEY not in line_req: return None
    req_opts= line_req[line_req.index(REQ_KEY)+len(REQ_KEY):]
    return req_opts
   #def report_extract_request

SPRTR       = -0xFFFFFFFF
last_ed_num = 0
last_rpt_tid= None
def report_to_tab(rpt_data:dict
                , rpt_info:dict
                , rpt_type:dict
                , how_walk:dict
                , what_find:dict
                , what_save:dict
                , progressor=None
                , req_opts=None):
    pass;                       LOG and log('(== |paths|={}',len(rpt_data))
    pass;                       RPTLOG and log('rpt_type={}',rpt_type)
    pass;                      #RPTLOG and log('rpt_data=¶{}',pf(rpt_data))
    pass;                      #RPTLOG and log('what_find={}',what_find)
    pass;                      #RPTLOG and log('what_save={}',what_save)
    
    global last_ed_num, last_rpt_tid
    # Choose/Create tab for report
    rpt_ed  = rpt_type.get('rpt_to_ed')
    if 'rpt_to_ed' in rpt_type: rpt_ed.set_prop(app.PROP_RO, False)
    def create_new(_title_ext='')->app.Editor:
        app.file_open('')
        new_ed  = ed
        new_ed.set_prop(app.PROP_ENC,       'UTF-8')
        new_ed.set_prop(app.PROP_TAB_TITLE, _('Results')+_title_ext)  #??
        return new_ed
        
    title_ext   = f(' ({})', what_find['find'][:LEN_TRG_IN_TITLE])
    if False:pass
    elif rpt_ed:    pass
    elif rpt_type['totb']==TOTB_NEW_TAB:
        pass;                   RPTLOG and log('!new',)
        rpt_ed  = create_new(title_ext)
    elif rpt_type['totb']==TOTB_USED_TAB: #if reed_tab: #or join_to_end:
        # Try to use prev or old
        pass;                   RPTLOG and log('!used',)
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
    elif rpt_type['totb'].startswith('tab:'): #if reed_tab: #or join_to_end:
        # Try to use pointed tab
        the_title   = rpt_type['totb'][len('tab:'):]
        pass;                   RPTLOG and log('!pointed the_title={}',(the_title))
        cands       = [app.Editor(h) for h in app.ed_handles() 
                        if app.Editor(h).get_prop(app.PROP_TAB_TITLE)==the_title]
        rpt_ed      = cands[0] if cands else None
    elif rpt_type['totb'].startswith('file:'): 
        # Try to use pointed file
        the_file    = rpt_type['totb'][len('file:'):]
        pass;                   RPTLOG and log('!pointed the_file={}',(the_file))
        if os.path.isfile(the_file):
            cands   = [app.Editor(h) for h in app.ed_handles() 
                        if app.Editor(h).get_filename()==the_file]
            if cands:
                rpt_ed  = cands[0]
            else:
                app.file_open(the_file)
                rpt_ed  = ed  
    else:
        pass;                   RPTLOG and log('!else',())
        pass
            
    rpt_ed  = create_new(title_ext) if rpt_ed is None else rpt_ed
    last_rpt_tid= rpt_ed.get_prop(app.PROP_TAB_ID)
    if rpt_ed.get_filename():
        rpt_ed.set_prop(app.PROP_TAB_TITLE, os.path.basename(rpt_ed.get_filename())+title_ext)  #??
    last_ed_num += 1
    rpt_ed.set_prop(app.PROP_TAG,       'FiF_'+str(last_ed_num))
    rpt_ed.focus() if FOCUS_TO_RPT else None

    # Prepare tab
    if not rpt_type['join']:
        rpt_ed.set_text_all('')
        rpt_ed.attr(       app.MARKERS_DELETE_ALL)

    # Fold prev res
    if rpt_type['join'] and FOLD_PREV_RES: #?and rpt_ed.get_prop(app.PROP_GUTTER_FOLD)
        pass;                   RPTLOG and log('?? fold',)
        fold_all_roots(rpt_ed, RPT_REPL_SIGN, RPT_FIND_SIGN)
        pass;                   RPTLOG and log('ok fold',)
        
    # Fill tab
#   rpt_ed.set_prop(app.PROP_LEXER_FILE,'')  #?? optimized?
    def mark_fragment(rw:int, cl:int, ln:int, to_ed=rpt_ed, style=MARK_FIND_STYLE):
        pass;                  #RPTLOG and log('rw={}',rw)
        to_ed.attr(       app.MARKERS_ADD
                , x=cl, y=rw, len=ln
                , **style
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
    def calc_width(_rpt_data, _algn, _need_rcl, _need_pth, _only_fn):
        # Find max(len(*)) for path, row, col, ln
        _fl_wd, _rw_wd, _cl_wd, _ln_wd  = 0, 0, 0, 0
        if not _algn:
            return _fl_wd, _rw_wd, _cl_wd, _ln_wd
        max_rw, max_cl, max_ln      = 0, 0, 0
        for _path_d in _rpt_data:
            _path       = _path_d['file']         if _need_pth                  else ''
            _path       = os.path.basename(_path) if _need_pth and _only_fn     else _path
            _fl_wd      = max(_fl_wd , len(_path))
            for _item in _path_d.get('items', ''):
                max_rw  = max(max_rw, _item.get('row', 0))
                if not _need_rcl:    continue#for item
                max_cl  = max(max_cl, _item.get('col', 0))
                max_ln  = max(max_ln, _item.get('ln',  0))
               #for item
           #for path_d
        _rw_wd  = len(str(max_rw))
        _cl_wd  = len(str(max_cl))
        _ln_wd  = len(str(max_ln))
        return _fl_wd, _rw_wd, _cl_wd, _ln_wd
       #def calc_width
#   def calc_width4depth(rpt_data, algn, need_rcl, need_pth, only_fn):
#       # Find max(len(*)) for path, row, col, ln
#       wds     = {}
##       fl_wd, rw_wd, cl_wd, ln_wd  = 0, 0, 0, 0
#       if not algn:
#           return wds # fl_wd, rw_wd, cl_wd, ln_wd
##       max_rw, max_cl, max_ln      = 0, 0, 0
#       for path_d in rpt_data:
#           dept        = 1+path_d.get('dept', 0)
#           wds_d       = wds.setdefault(dept, {})
#           path        = path_d['file']         if need_pth                else ''
#           path        = os.path.basename(path) if need_pth and only_fn    else path
#           wds_d['fl'] =         max(wds_d.get('fl', 0), len(path))
#           for item in path_d.get('items', ''):
#               wds_d['max_rw'] = max(wds_d.get('max_rw', 0), item.get('row', 0))
#               if not need_rcl:    continue#for item
#               wds_d['max_cl'] = max(wds_d.get('max_cl', 0), item.get('col', 0))
#               wds_d['max_ln'] = max(wds_d.get('max_ln', 0), item.get('ln',  0))
#              #for item
#          #for path_d
#       for wds_d in wds.values():
#           wds_d['rw']    = len(str(wds_d.get('max_rw', 0)))
#           wds_d['cl']    = len(str(wds_d.get('max_cl', 0)))
#           wds_d['ln']    = len(str(wds_d.get('max_ln', 0)))
#       return wds
#      #def calc_width4depth
    onfn    = not what_save['count']
    shtp    = rpt_type['shtp']
    algn    = rpt_type['algn']
    need_rcl= shtp in (SHTP_SHORT_RCL, SHTP_SHRTS_RCL, SHTP_MIDDL_RCL, SHTP_SPARS_RCL)
    need_pth= shtp in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_MIDDL_R, SHTP_MIDDL_RCL)
    only_fn = shtp in (SHTP_MIDDL_R, SHTP_MIDDL_RCL)
    roots   = how_walk['roots']
    root    = roots[0] if 1==len(roots) else '_no_root_'
#   root    = how_walk['root']
    repl_b  = what_find['repl'] is not None
    pass;                       RPTLOG and log('algn, need_rcl, need_pth, only_fn={}',(algn, need_rcl, need_pth, only_fn))
    fl_wd, rw_wd, cl_wd, ln_wd  = calc_width(       rpt_data, algn, need_rcl, need_pth, only_fn)
    rw_wd  += 1 if repl_b else 0
    pass;                       RPTLOG and log('fl_wd,rw_wd,cl_wd,ln_wd={}',(fl_wd,rw_wd,cl_wd,ln_wd))
#   wds                         = calc_width4depth( rpt_data, algn, need_rcl, need_pth, only_fn)
#   pass;                       RPTLOG and log('wds={}',(wds))

    line_1  =   f(_('{} for "{}" in "{}" from {} ({} matches in {}({}) files)')
                ,RPT_FIND_SIGN
                ,what_find['find']
                ,how_walk['file_incl']
                ,(repr(roots[0]) if 1==len(roots) else repr(roots)).replace('\\\\','\\').replace("'", '"')
#               ,root
                ,rpt_info['frgms']
                ,rpt_info['files']
                ,rpt_info['cllc_files']) \
            if not repl_b else      \
                f(_('{} "{}" to "{}" in "{}" from {} ({} changes in {}({}) files)')
                ,RPT_REPL_SIGN
                ,what_find['find']
                ,what_find['repl']
                ,how_walk['file_incl']
                ,(repr(roots[0]) if 1==len(roots) else repr(roots)).replace('\\\\','\\').replace("'", '"')
#               ,root
                ,rpt_info['frgms']
                ,rpt_info['files']
                ,rpt_info['cllc_files'])
    line_1 += ' ' + REQ_KEY + req_opts  if req_opts else ''
                
    row4crt = append_line(line_1)
#   rpt_ed.lock()   #?? Pack undo to one cmd
    rpt_stop    = False
    try:
        for path_n, path_d in enumerate(rpt_data):                  #NOTE: rpt main loop
            if progressor and (0==path_n%37):# or 0==rpt_ed.get_line_count()%137):
                pc  = int(100*path_n/len(rpt_data))
                progressor.set_progress( f(_('[ESC?] Report: {}%'), pc))
                if progressor.need_break():
                    progressor.prefix += f(_('(Report stopped on {}%) '), pc)
                    append_line(         f('\t<{}>', progressor.prefix))
                    rpt_stop= True
                    break#for path
            has_cnt = 'count' in path_d and 0<path_d['count']     # skip count==0
            has_itm = 'items' in path_d
            path    = path_d['file']
            isfl    = path_d.get('isfl')
            pass;               RPTLOG and log('path,root={}',(path,root))
            if   shtp   in (SHTP_SHRTS_R, SHTP_SHRTS_RCL):
                pass
            elif shtp   in (SHTP_MIDDL_R, SHTP_MIDDL_RCL, SHTP_SPARS_R, SHTP_SPARS_RCL) and \
                path!=root:
                if isfl:
                    path= os.path.basename(path)
                    pass;       RPTLOG and log('(basename)path={}',path)
                elif 'prnt' in path_d and path_d['prnt'] is not None:
                    path= os.path.relpath(path, path_d['prnt']['file'])
                    pass;       RPTLOG and log('(prnt-rel)path={}',path)
                else:
                    path= os.path.relpath(path, root) if root!='_no_root_' else path
                    pass;       RPTLOG and log('(root-rel)path={}',path)
            dept    = 1+path_d.get('dept', 0)
            c9dt    = c9*dept
            pass;               RPTLOG and log('onfn,has_cnt,isfl,has_itm,c9dt={}',(onfn,has_cnt,isfl,has_itm,repr(c9dt)))
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
                    pass;       RPTLOG and log('SPARS path,c9dt={}',(path,repr(c9dt)))
                if shtp in (SHTP_SHRTS_R, SHTP_SHRTS_RCL):
                    append_line(c9dt+f('<{}>: #{}', path, len(items)))
                    path= '' 
                    c9dt= c9*(1+dept)
                    pass;       RPTLOG and log('SPARS path,c9dt={}',(path,repr(c9dt)))
                for item_n, item in enumerate(items):
                    if progressor and (1000==item_n%1039):
                        pc  = int(100*path_n/len(rpt_data))
                        progressor.set_progress( f(_('[ESC?] Report: {}%'), pc))
                        if progressor.need_break():
                            progressor.prefix += f(_('(Report stopped on {}%) '), pc)
                            append_line(         f('\t<{}>', progressor.prefix))
                            rpt_stop= True
                            break#for item
                    pass;      #RPTLOG and log('item={}',(item))
                    src_rw  = item.get('row', 0)
                    if SPRTR==src_rw:
                        # Separator
                        append_line(c9dt+'<>:')
                        continue#for path_n
                    if  not repl_b and \
                        shtp not in (SHTP_SPARS_R, SHTP_SPARS_RCL) and \
                        src_rw==pre_rw and prefix and new_row!=-1 and 'col' in item and 'ln' in item:
                        # Add mark in old line
                        mark_fragment(new_row, item['col']+len(prefix), item['ln'], rpt_ed)
                        continue#for path_n

                    repl_tf = item.get('res', 0)
                    repl_o  = repl_b and repl_tf
    #               rw_wd   = 1+rw_wd   if repl_b else rw_wd
    #               src_rw  = abs(src_rw)
                    src_rw_ = '=' if repl_o else '!' if repl_b else ''
                    pass;      #LOG and log('repl_b,repl_o,rw_wd,src_rw_={}',(repl_b,repl_o,rw_wd,src_rw_))
                    src_cl  = item.get('col', -1)
                    src_ln  = item.get('ln', -1)
                    src_rw_s= src_rw_+                                 str(1+src_rw)
    #               src_cl_s= '0' if repl_o else '' if -1==src_cl else str(1+src_cl)
    #               src_ln_s= '0' if repl_o else '' if -1==src_ln else str(  src_ln)
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
                    pass;      #RPTLOG and log('new_row, prefix={}',(new_row, prefix))
                    if 'col' in item and 'ln' in item:
                        mark_fragment(new_row, item['col']+len(prefix), item['ln'], rpt_ed
                                     ,MARK_TREPL_STYLE 
                                        if repl_tf==1 else 
                                      MARK_FREPL_STYLE 
                                        if repl_tf==2 else 
                                      MARK_FIND_STYLE)
                    pre_rw  = src_rw
                   #for item
               #elif has_itm
            if rpt_stop: break#for path
           #for path_n
    except Exception:# as ex:
#       log(f(_('Error:{}'),ex)) 
        log(traceback.format_exc()) 
    finally:
        pass
#       rpt_ed.unlock()   #?? Pack undo to one cmd
    pass;                       # Append work data to report
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.set_text_line(-1, '')
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.insert(0,rpt_ed.get_line_count()-1, json.dumps(rpt_type, indent=2))
    pass;                       DBG_DATA_TO_REPORT and rpt_ed.insert(0,rpt_ed.get_line_count()-1, json.dumps(rpt_data, indent=2))

    pass;                      #log('apx.get_opt(tab_size, 0, apx.CONFIG_LEV_LEX_ONLY, ed_cfg=None,lexer=FIF_LEXER)={}',apx.get_opt('tab_size', 0, apx.CONFIG_LEV_LEX_ONLY, ed_cfg=None,lexer=FIF_LEXER))
    need_tab_size   = TAB_SIZE_IN_RPT>0 and (
        apx.get_opt('tab_size', 0,               apx.CONFIG_LEV_LEX_ONLY, ed_cfg=None,lexer=FIF_LEXER)==0
            if apx.version(0)>='0.6.5' else
        apx.get_opt('tab_size', 0,               apx.CONFIG_LEV_LEX,      ed_cfg=None,lexer=FIF_LEXER)==
        apx.get_opt('tab_size', 0,               apx.CONFIG_LEV_DEF) )
    pass;                      #log('TAB_SIZE_IN_RPT,need_tab_size={}',TAB_SIZE_IN_RPT,need_tab_size)
    if need_tab_size:
        apx.set_opt('tab_size', TAB_SIZE_IN_RPT, apx.CONFIG_LEV_LEX,      ed_cfg=None,lexer=FIF_LEXER)
        apx.set_opt('tab_size', TAB_SIZE_IN_RPT, apx.CONFIG_LEV_FILE,     ed_cfg=rpt_ed)
    rpt_ed.set_prop(app.PROP_LEXER_FILE, FIF_LEXER)
#   # AT-hack to update folding
#   line0 = rpt_ed.get_text_line(0)
#   rpt_ed.set_text_line(0, '')
#   rpt_ed.set_text_line(0, line0)
#   app.app_idle()
    if app.app_api_version()>='1.0.162':
        pass;                   RPTLOG and log('rpt_ed.lexer_scan(row4crt) row4crt={}',row4crt)
        rpt_ed.lexer_scan(row4crt)
        
    pass;                      #RPTLOG and log('row4crt={}',row4crt)
    rpt_ed.set_caret(      0, row4crt)

    if AUTO_SAVE and rpt_ed.get_filename() and os.path.isfile(rpt_ed.get_filename()):
        rpt_ed.save()
    pass;                       LOG and log('==) stoped={}',(rpt_stop))
    if 'rpt_to_ed' in rpt_type: rpt_ed.set_prop(app.PROP_RO, True)
   #def report_to_tab

############################################
# Using report to nav
def _open_and_nav(where:str, how_act:str, path:str, rw=-1, cl=-1, ln=-1):
    """ Return True if nav successed. """
    pass;                       NAVLOG and log('where, how_act={}',(where, how_act))
    pass;                       NAVLOG and log('path,rw,cl,ln={}',(path,rw,cl,ln))
    op_ed   = None
    if path.startswith('tab:'):
        tab_id  = int(path.split('/')[0].split(':')[1])
        pass;                   NAVLOG and log('tab_id={}',(tab_id))
        op_ed   = apx.get_tab_by_id(tab_id)
        if not op_ed:   return  msg_status(f(_("No tab for navigation"), ))
    elif not os.path.isfile(path):
        pass;                   NAVLOG and log('not isfile',())
        return
    the_ed_id   = ed.get_prop(app.PROP_TAB_ID)
    the_ed_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
    pass;                       NAVLOG and log('the_ed_id={}',(the_ed_id))
    # Already opened?
    if not op_ed:
        for h in app.ed_handles(): 
            t_ed  = app.Editor(h)
            if t_ed.get_filename() and os.path.samefile(path, t_ed.get_filename()):
                op_ed   = t_ed
                pass;           NAVLOG and log('found filename',())
                break
    if not op_ed:
        # Open it
        ed_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
        grps    = apx.get_groups_count() # len({app.Editor(h).get_prop(app.PROP_INDEX_GROUP) for h in app.ed_handles()})
        op_grp  = -1                                    \
                     if 1==grps                     else\
                  -1                                    \
                     if where=='same'               else\
                  (ed_grp+1)%grps                       \
                     if where=='next'               else\
                  (ed_grp-1)%grps                       \
                     if where=='prev'               else\
                  int(where[3])                         \
                     if where[0:3]=='gr#'           else\
                  -1
        pass;                   NAVLOG and log('ed_grp, grps, op_grp={}',(ed_grp, grps, op_grp))
        app.file_open(path, op_grp)
        op_ed   = ed
    op_ed.focus()
    pass;                       NAVLOG and log('ok op_ed.focus()',())
    nav_to_frag(op_ed, rw, cl, ln, how_act, indent_vert=apx.get_opt('find_indent_vert', -5, ed_cfg=op_ed))

    if how_act=='move' or the_ed_grp == ed.get_prop(app.PROP_INDEX_GROUP):
        op_ed.focus()
    else:
        the_ed  = apx.get_tab_by_id(the_ed_id)
        the_ed.focus()
    return True
   #def _open_and_nav

def nav_as(path, ed_as):
    op_ed   = None
    if path.startswith('tab:'):
        tab_id  = int(path.split('/')[0].split(':')[1])
        pass;                   NAVLOG and log('tab_id={}',(tab_id))
        op_ed   = apx.get_tab_by_id(tab_id)
        if not op_ed:                   return  msg_status(_("No tab for navigation"))
    else:
        if not os.path.isfile(path):    return  msg_status(_("No file for navigation"))
        op_ed   = ed_of_file_open(path)
        if not op_ed:
            app.file_open(path)
            op_ed   = ed
    op_ed.set_caret(*ed_as.get_carets()[0])
   #def nav_as
       
def _unfold_line(ed_, row):
    fold_l  = ed_.folding(app.FOLDING_GET_LIST)
    pass;                      #log('row, fold_l={}',(row, fold_l))
    if not fold_l:  return 

    r_fold_l= [(fold_i,fold_d,row-fold_d[0]) 
                for fold_i,fold_d in enumerate(fold_l) 
                if fold_d[0] <= row <= fold_d[1] and
                   fold_d[0] !=        fold_d[1]]         # [0]/[1] line of range start/end
    pass;                      #log('r_fold_l={}',(r_fold_l))
    if not r_fold_l:  return 

    r_fold_l.sort(key=lambda ifd:ifd[2])
    
    for item in r_fold_l:
        fold_i, fold_d  = item[:2]
        folded  = fold_d[4]
        if folded:
            ed_.folding(app.FOLDING_UNFOLD, index=fold_i)

       
def nav_to_frag(op_ed, rw, cl, ln, how_act='', indent_vert=-5):
    
    _unfold_line(op_ed, rw)
    if cl!=-1:
        op_ed.set_prop(app.PROP_COLUMN_LEFT, '0')

    if False:pass
    elif rw==-1:
        pass
    elif cl==-1 and how_act=='move':
        op_ed.set_caret(        0, rw)
    elif cl==-1:
        l_ln= len(op_ed.get_text_line(rw))
        op_ed.set_caret(        0, rw,   l_ln,  rw)       # inverted sel to show line head if window is narrow 
    elif ln==-1:
        op_ed.set_caret(        cl, rw)
    else:
        op_ed.set_caret(        cl+ln,  rw,     cl, rw)
    if rw!=-1:
        top_row = max(0, rw - min(5, abs(indent_vert)))
        op_ed.set_prop(app.PROP_LINE_TOP, top_row)
   #def nav_to_frag

reSP    = re.compile(  r'(?P<S>\t+)'        # Shift !
                      r'<(?P<P>[^>]+)>')    # Path  !
reSPR   = re.compile(  r'(?P<S>\t+)'        # Shift !
                      r'<(?P<P>[^>]+)'      # Path  !
                     r'\((?P<R> *=?\d+)'    # Row   !
                       r'(?P<C>: *\d+)?'    # Col?
                       r'(?P<L>: *\d+)?\)>')# Len?
reSR    = re.compile(  r'(?P<S>\t+)'        # Shift !
                    r'<\((?P<R> *=?\d+)'    # Row   !
                       r'(?P<C>: *\d+)?'    # Col?
                       r'(?P<L>: *\d+)?\)>')# Len?
def _parse_line(line:str, what:str)->tuple:                  #NOTE: nav _parse_line
    pass;                       NAVLOG and log('what, line={}',(what, line))
    if what=='SP':
        mtSP    = reSP.search(line)
        if mtSP:
            gdct= mtSP.groupdict()
            pass;               NAVLOG and log('ok mtSP gdct={}', gdct)
            return mtSP.group(0),   gdct['S'], gdct['P']
        return (None,)*3
    mtSR   = reSR.search(line)
    if mtSR:
        gdct= mtSR.groupdict()
        pass;                   NAVLOG and log('ok mtSR gdct={}', gdct)
        rw  = gdct['R'].lstrip(' ').lstrip('=')
        cl  = gdct['C']
        ln  = gdct['L']
        return mtSR.group(0),   gdct['S'], '' \
            ,int(rw)-1,        int(cl[1:])-1 if cl else -1, int(ln[1:]) if ln else -1
    mtSPR   = reSPR.search(line)
    if mtSPR:   
        gdct= mtSPR.groupdict()
        pass;                   NAVLOG and log('ok mtSPR gdct={}', gdct)
        rw  = gdct['R'].lstrip(' ').lstrip('=')
        cl  = gdct['C']
        ln  = gdct['L']
        return mtSPR.group(0),  gdct['S'], gdct['P'].rstrip() \
            ,int(rw)-1,        int(cl[1:])-1 if cl else -1, int(ln[1:]) if ln else -1
    mtSP    = reSP.search(line)
    if mtSP:
        gdct= mtSP.groupdict()
        pass;                   NAVLOG and log('ok mtSP gdct={}', gdct)
        return mtSP.group(0),   gdct['S'], gdct['P'], -1, -1, -1
    return (None,)*6
   #def _parse_line

def _build_path(ted, path:str, row:int, shft:str)->str:
    # Try to build path from prev lines
    for t_row in range(row-1, -1, -1):                          #NOTE: nav build path
        t_line  = ted.get_text_line(t_row)
        pass;                   NAVLOG and log('t_row, t_line={}', (t_row, t_line))
        if t_line.startswith('+'):                              break#for t_row         as top
        if len(shft) <= len(t_line)-len(t_line.lstrip('\t')):   continue#for t_row      as same level
        t_fll,  \
        t_sft,  \
        t_pth   = _parse_line(t_line, 'SP')
        pass;                   NAVLOG and log('t_sft, t_pth={}', (t_sft, t_pth))
        if len(t_sft) == len(shft): 
            pass;               NAVLOG and log('skip: t_sft==shft', ())
            continue#for t_row
        if len(t_sft) >  len(shft):
            pass;               NAVLOG and log('bad: t_sft>shft', ())
            return msg_status(f(_("Line {} has bad data for navigation"), 1+t_row))
        path    = os.path.join(t_pth, path) if path else t_pth
        pass;                   NAVLOG and log('new path={}', (path))
        if os.path.isfile(path):
            break#for t_row
        shft    = t_sft
       #for t_row
    return path
   #def _build_path

def get_data4nav(ted, row:int):
    line    = ted.get_text_line(row)
    full,   \
    shft,   \
    path,   \
    rw,cl,ln= _parse_line(line, 'all')
    pass;                       NAVLOG and log('full={}', full)
    pass;                       NAVLOG and log('shft, path, rw, cl, ln={}', (shft, path, rw, cl, ln))
    pass;                       NAVLOG and log('path={}', (path))
    if not full:
        pass;                   NAVLOG and log('return (path, rw, cl, ln)={}', ([None]*4))
        return  [None]*4
#   if not full:            return  msg_status(f(_("Line {} has no data for navigation"), 1+row))
    if os.path.isfile(path) or path.startswith('tab:'):
        pass;                   NAVLOG and log('return (path, rw, cl, ln)={}', (path, rw, cl, ln))
        return (path, rw, cl, ln)
#       return _open_and_nav(where, how_act, path, rw, cl, ln)
    path    = _build_path(ted, path, row, shft)
    if True: # os.path.isfile(path):
        pass;                   NAVLOG and log('return (path, rw, cl, ln)={}', (path, rw, cl, ln))
        return (path, rw, cl, ln)
#       return _open_and_nav(where, how_act, path, rw, cl, ln)
#   return  [None]*4
   #def get_data4nav

def jump_to(drct:str, what:str):
    global last_rpt_tid
    pass;                       NAVLOG and log('drct,what,last_rpt_tid={}',(drct,what,last_rpt_tid))
    if not last_rpt_tid:return msg_status(_('Undefined report to jump. Fill new report or navigate with old one.'))
    rpt_ed  = apx.get_tab_by_id(last_rpt_tid)
    if not rpt_ed:      return msg_status(_('Undefined report to jump. Fill new report or navigate with old one.'))
    crts    = rpt_ed.get_carets()
    if len(crts)>1:     return msg_status(_("Command doesn't work with multi-carets"))
#   last_row= crts[0][1]
    all_rows= rpt_ed.get_line_count()
    
    act_grp =     ed.get_prop(app.PROP_INDEX_GROUP)
    rpt_grp = rpt_ed.get_prop(app.PROP_INDEX_GROUP)
    where   = 'gr#'+str(act_grp)
    how_act = 'move'
    
    base_row= crts[0][1]
    line    = rpt_ed.get_text_line(base_row)
    if line.startswith(RPT_FIND_SIGN):
        base_path   = '/waiting/'
        base_rw     = 0
    else:
        path,rw,\
        cl, ln  = get_data4nav(rpt_ed, base_row)
        if not path \
        or not (os.path.isfile(path) or path.startswith('tab:')):
            return msg_status(f(_('Line "{}":{} has no data for navigation'), rpt_ed.get_prop(app.PROP_TAB_TITLE, ''), 1+base_row))
        base_path   = path
        base_rw     = rw
    pass;                       NAVLOG and log('base_path,base_rw={}',(base_path,base_rw))
    
    def set_rpt_active_row(_row):
        grp_tab = app.ed_group(rpt_grp)
        rpt_vis = grp_tab.get_prop(app.PROP_TAB_ID) == rpt_ed.get_prop(app.PROP_TAB_ID)
        rpt_act =      ed.get_prop(app.PROP_TAB_ID) == rpt_ed.get_prop(app.PROP_TAB_ID)
        if  rpt_vis:
            rpt_ed.focus()
        rpt_ed.set_caret(       0, _row)
        tid     = None
        if  rpt_vis \
        and not (rpt_ed.get_prop(app.PROP_LINE_TOP) <= _row <= ed.get_prop(app.PROP_LINE_BOTTOM)):
            if not rpt_act:
                tid = ed.get_prop(app.PROP_TAB_ID)
                rpt_ed.focus()
            rpt_ed.set_prop(     app.PROP_LINE_TOP, max(0, _row - max(5, apx.get_opt('find_indent_vert', -5))))
            if not rpt_act:
                apx.get_tab_by_id(tid).focus()
       #def set_rpt_active_row
    
    row     = base_row
    while True:
        row    += 1 if drct=='next' else -1
        if not 0<=row<all_rows:                 return msg_status(_('No data to jump'))
        line    = rpt_ed.get_text_line(row)
        if not line.lstrip(c9).startswith('<') \
        or line.startswith(RPT_FIND_SIGN):      return msg_status(_('No data to jump'))
        
        path,rw,\
        cl, ln  = get_data4nav(rpt_ed, row)
        pass;                   NAVLOG and log('path,rw={}',(path,rw))
        if not path \
        or not (os.path.isfile(path) or path.startswith('tab:')):
            continue#while
            
        if  what=='rslt' \
        and (-1==base_rw and -1==rw or -1!=base_rw and -1!=rw):
            # Jump to nearest result
            set_rpt_active_row(row)
            return _open_and_nav(where, how_act, path, rw, cl, ln)
        
        if  what=='file' and base_path!=path \
        and (-1==base_rw and -1==rw or -1!=base_rw and -1!=rw):
            # Jump to result from next file
            set_rpt_active_row(row)
            return _open_and_nav(where, how_act, path, rw, cl, ln)
        
        if  what=='fold' \
        and not base_path.startswith('tab:') \
        and not      path.startswith('tab:') \
        and os.path.dirname(base_path)!=os.path.dirname(path) \
        and (-1==base_rw and -1==rw or -1!=base_rw and -1!=rw):
            # Jump to result from next folder
            set_rpt_active_row(row)
            return _open_and_nav(where, how_act, path, rw, cl, ln)
       #while
   #def jump_to
       
def nav_to_src(where:str, how_act='move', _ed=ed):
    """ Try to open file and navigate to row[+col+sel].
        Return True if nav successed.
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
    global last_rpt_tid
    pass;                   NAVLOG and log('where, how_act={}',(where, how_act))
    crts    = _ed.get_carets()
    if len(crts)>1:         return msg_status(_("Command doesn't work with multi-carets"))
    last_rpt_tid= _ed.get_prop(app.PROP_TAB_ID)
        
    row     = crts[0][1]
    pass;                   _t = get_data4nav(_ed, row)
    pass;                   NAVLOG and log('get_data4nav(ed, row)={}',(_t))
    pass;                   path,rw,cl,ln  = _t
#   path,rw,\
#   cl, ln  = get_data4nav(_ed, row)
    if path and (os.path.isfile(path) or path.startswith('tab:')):
        return _open_and_nav(where, how_act, path, rw, cl, ln)
    msg_status(f(_("Line {} has no data for navigation"), 1+row))
   #def nav_to_src

def fold_all_roots(rpt_ed:app.Editor, what1:str, what2:str):
#   pass;                       RPTLOG and log('?? fold ver="{}"',app.app_api_version())
    if app.app_api_version()<'1.0.162': return
    
    # Waiting
    pass;                      #RPTLOG and log('?? fold',)
    fold_rngs = rpt_ed.folding(app.FOLDING_GET_LIST)
    if not fold_rngs: 
        for loop in range(10):
            time.sleep(0.1)
            app.app_idle()
            if rpt_ed.folding(app.FOLDING_GET_LIST):
                pass;          #RPTLOG and log('wait ok loop={}',loop)
                break
        else:
            pass;              #RPTLOG and log('wait fail',)
            return
    pass;                      #RPTLOG and log('fold_rngs={}',fold_rngs)
    if not fold_rngs: 
        pass;                  #RPTLOG and log('fail - no rngs',)
        return
    for rng_num, rng_info in enumerate(fold_rngs[:]):
        pass;                  #RPTLOG and log('?? rng_num={}',rng_num)
        rng_bgn, rng_end, rng_off, rng_stapled, rng_folded  = rng_info
        if rng_bgn==rng_end:    # simple rng
            pass;              #RPTLOG and log('simple rng rng_num={}',rng_num)
            continue
        if rng_folded:          # already
            pass;              #RPTLOG and log('already rng_num={}',rng_num)
            continue
        rng_1st_line= rpt_ed.get_text_line(rng_bgn).strip()
        if not rng_1st_line.startswith(what1) and not rng_1st_line.startswith(what2):
            pass;              #RPTLOG and log('not startswith rng_num={}',rng_num)
            continue
        pass;                  #RPTLOG and log('?? FOLDING_FOLD rng_num={}',rng_num)
        rpt_ed.folding(app.FOLDING_FOLD, rng_num)
        pass;                  #RPTLOG and log('ok FOLDING_FOLD rng_num={}',rng_num)
   #def fold_all_roots

##############################################################################
def find_in_files(how_walk:dict, what_find:dict, what_save:dict, how_rpt:dict, progressor=None)->(list, dict):
    """ Scan files by how_walk:
            'roots'        ![str]       disk folder(s) 
                                        or <in proj files> 
                                        or <in open files> to scan tabs
        //  'root'         !str         disk folder or <in open files> to scan tabs
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
            'repl'          str(None)   Replace with
            'mult'          bool(F)     Multylines 
            'reex'          bool(F)     
            'case'          bool(F)     
            'word'          bool(F)     
        and to save info by what_save:
            'count'         bool(T)     Need counts
            'place'         bool(T)     Need places
#           'fragm'         bool(F)     Need fragments
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

    roots   = how_walk['roots']
#   root    = how_walk['root']
    if roots_is_proj(roots):
#   if roots==[IN_PROJ_FOLDS]:
        try:
            from cuda_project_man import global_project_info
            roots   = global_project_info['nodes'][:]
            pass;               LOG and log('roots={}',(roots))
            how_walk['roots'] = roots
        except Exception as ex:
            pass;               LOG and log('ex={}',(ex))
#       except:
            roots   = []
            how_walk['roots'] = roots
    pass;                       LOG and log('roots={}',(roots))
    files,  \
    cllc_stp= collect_tabs(how_walk) \
                if roots_is_tabs(roots) else \
              collect_files(how_walk, progressor)
    if cllc_stp and ESC_FULL_STOP:   return [], {}
    pass;                      #FNDLOG and log('#collect_files={}',len(files))
    pass;                      #FNDLOG and log('files={}',pf(files))
    rsp_i['cllc_files']     = len(files)
    rsp_i['cllc_stopped']   = cllc_stp
    
    frst    = what_find.get('only_frst', 0)
    pttn_s  = what_find['find']
    repl_s  = what_find['repl']
    mult_b  = what_find['mult']
    case_b  = what_find['case']
    flags   = re.M if mult_b else 0 \
            +    0 if case_b else re.I
    if not    what_find['reex']:
        if    what_find['word'] and re.match('^\w+$', pttn_s):
            pttn_s  = r'\b'+pttn_s+r'\b'
        else:
            pttn_s  = re.escape(pttn_s)
    pass;                      #FNDLOG and log('pttn_s, flags, repl_s={}',(pttn_s, flags, repl_s))
    pttn_r  = re.compile(pttn_s, flags)

    cnt_b   = what_save['count']
    plc_b   = what_save['place']
    lin_b   = what_save['lines']
    spr_dirs= how_rpt['sprd']

    cntx    = how_rpt['cntx']
    CONTEXT_WIDTH_U = apx.get_opt('fif_context_width_before'    , CONTEXT_WIDTH)
    CONTEXT_WIDTH_D = apx.get_opt('fif_context_width_after'     , CONTEXT_WIDTH)
    extU_lns= CONTEXT_WIDTH_U if cntx else 0
    extD_lns= CONTEXT_WIDTH_D if cntx else 0
    pass;                      #LOG and log('repl_s,extU_lns,extD_lns={}',(repl_s,extU_lns,extD_lns))
#   ext_lns = CONTEXT_WIDTH if cntx else 0
#   pass;                      #LOG and log('repl_s,ext_lns={}',(repl_s,ext_lns))

    enco_l  = how_walk.get('enco', ['UTF-8'])
    detector= UniversalDetector() if ENCO_DETD in enco_l else None
    rpt_enc_fail= apx.get_opt('fif_log_encoding_fail', False)

    def find_for_body(   _body:str, _dept:int, _rsp_l:list, _rsp_i:dict):
        if pttn_r.search(_body):
            _rsp_l          += [dict(dept=_dept, file=path, isfl=True)]
            _rsp_i['files'] += 1
            _rsp_i['frgms'] += 1
            return 1
        return 0
    def find_for_lines(_lines:list, _dept:int, _rsp_l:list, _rsp_i:dict)->int:
        pass;                  #LOG and log('|_lines|, _dept={}',(len(_lines), _dept))
        _count   = 0
        items   = []
        for ln,line_src in enumerate(_lines):
            line    = line_src.rstrip(c10).rstrip(c13)
            mtchs   = list(pttn_r.finditer(line))
            pass;              #LOG and log('len(mtchs), line={}',(len(mtchs), line))
            if not plc_b:
                # Only counting
                _count  += len(mtchs)
            else:
                for mtch in mtchs:                              #NOTE: fif, line
                    _count  += 1
                    for ext_ln in range(max(0, ln-extU_lns), ln):
#                   for ext_ln in range(max(0, ln-ext_lns), ln):
                        item    =       dict(row=ext_ln)
                        if lin_b:  item.update(dict(line=_lines[ext_ln]))
                        items  += [item]
                    item        =       dict(row=ln, col=mtch.start(), ln=mtch.end()-mtch.start())
                    if lin_b:      item.update(dict(line=line))
                    items      += [item]
                    for ext_ln in range(ln+1, min(len(_lines), ln+extD_lns+1)):
#                   for ext_ln in range(ln+1, min(len(_lines), ln+ext_lns+1)):
                        item    =       dict(row=ext_ln)
                        if lin_b:  item.update(dict(line=_lines[ext_ln]))
                        items  += [item]
                    if extU_lns+extD_lns>0:
#                   if ext_lns>0:
                        # Separator
                        items  += [dict(row=SPRTR, line='')]
                    if 0<frst<=(rsp_i['frgms']+_count): break#for mtch
                   #for mtch
                if repl_s is not None and mtchs:
                    mtch0       = mtchs[0] 
                    mtch1       = mtchs[-1] 
                    line_new,rn = pttn_r.subn(repl_s, line_src)
                    assert rn==len(mtchs)
                    items      += [dict(row=ln
                                       ,col=                                          mtch0.start()
                                       ,ln =len(line_new)-(len(line_src)-mtch1.end())-mtch0.start()
                                       ,line=line_new, res=1 if rn==1 else 2)]
                    _lines[ln]  = line_new
                    pass;      #LOG and log('line_new={}',(repr(line_new)))
            if 0<frst<=(rsp_i['frgms']+_count): break#for line
           #for line
        if not _count:
            # No matches
            return _count #continue#for path
        if not plc_b:
            # Only counting
            _rsp_l  += [dict( dept=_dept
                            ,file=path
                            ,isfl=True
                            ,count=_count)]
        else:
            _rsp_l  += [dict( dept=_dept
                            ,file=path
                            ,isfl=True
                            ,count=_count
                            ,items=items)]
        _rsp_i['files'] += 1
        _rsp_i['frgms'] += _count
        return _count
       #def find_for_lines

    if roots_is_tabs(roots):
#   if roots==[IN_OPEN_FILES]:
#   if root == IN_OPEN_FILES:
        # Find in tabs
        for path, h_tab in files:
            ted     = app.Editor(h_tab)
            if not cnt_b:
                # Only path finding
                find_for_body(ted.get_text_all(), 0, rsp_l, rsp_i)
                continue#for path
            lines   = [ted.get_text_line(r) for r in range(ted.get_line_count())]
            count   = find_for_lines(lines, 0, rsp_l, rsp_i)
            if repl_s is not None and count:
                # Change text in ted
                pass;          #LOG and log('lines={}',(lines))
                crts= ted.get_carets()
                ted.set_text_all(c13.join(lines))
                ted.set_caret(      *crts[0])
            if 0<frst<=rsp_i['frgms']: break#for path
           #for path
        return rsp_l, rsp_i
        
    def get_prnt_path_dct(_path, tree):
#       while True:
        for i in range(25):##!! 
            if not _path:       return None
            if _path in tree:   return tree[_path]
            _path   = os.path.dirname(_path)
        return None
    tree4rsp= {}                # {path:rsp_l[?]} 
                                # (1) store dir-items, 
                                # (2) tree-parent-links in item of rsp_l to sum 'count' for dir
    if spr_dirs and 1==len(roots):    # Separate dir in rsp
        root            = roots[0]
        tree4rsp[root]  = dict(dept=0, file=root, count=0, prnt=None)
        rsp_l          += [tree4rsp[root]]
        pass;                  #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
    
    pass;                       LOG and log('?? files (== what_find={}',(what_find))
#   pass;                       t=log('?? files (==',) if FNDLOG else 0
    
    for path_n, path in enumerate(files):                       #NOTE: fif, path loop
        pass;                   FNDLOG and log('path_n, path={}',(path_n, path))
        if progressor and 0==path_n%17:
            pc  = int(100*path_n/len(files))
            progressor.set_progress( f(_('[ESC?] Search: {}% [found {} matches in {}({}) files]')
                                    , pc
                                    , rsp_i['frgms'], rsp_i['files'], len(files)))
            if progressor.need_break():
                if ESC_FULL_STOP:   return [], {}
                rsp_i['find_stopped']   = True
                progressor.prefix += f(_('(Search stopped on {}%) '), pc)
                break#for path
        
        prntdct = None
        if spr_dirs:# Separate dir in rsp
            # For dir with path need to add item in rsp_l
            #   NB! Rely to Up-Down dir sequence in files
            pathdir = os.path.dirname(path)
            pass;              #FNDLOG and log('?path,pathdir={}',(path,pathdir))
            if 1<len(roots):
                # Add root on demand
                root            = [root for root in roots if pathdir.startswith(root)][0]
                if  root not in tree4rsp:
                    tree4rsp[root]  = dict(dept=0, file=root, count=0, prnt=None)
                    rsp_l          += [tree4rsp[root]]
                    pass;      #FNDLOG and log('add root tree4rsp[{}]={}',root,prntdct)
            prntdct = tree4rsp.get(pathdir)
            if not prntdct:
                prntdct = get_prnt_path_dct(pathdir, tree4rsp)
                pass;          #FNDLOG and log('prntdct={}',prntdct)
                if not prntdct:
                    pass;      #FNDLOG and log('no prntdct',())
                if prntdct:
                    dct     = dict(dept=1+prntdct['dept'], file=pathdir, count=0, prnt=prntdct)
                    tree4rsp[pathdir]= dct
                    pass;      #FNDLOG and log('tree4rsp[{}]={}',pathdir,dct)
                    rsp_l  += [dct]
                    prntdct = dct
                pass;          #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
        dept    = 1+prntdct['dept'] if prntdct else 0
        pass;                  #FNDLOG and log('dept={}',dept)
        # Find in file
#       encd    = ''
        for enco_n, enco_s in enumerate(enco_l):
            pass;              #LOG and log('enco_s={}',(enco_s))
            if enco_s==ENCO_DETD:
                enco_s  = detect_encoding(path, detector)
                enco_l[enco_n] = enco_s
            try:
                if not cnt_b:
                    # Only path finding
                    body    = open(path, mode='r', encoding=enco_s, newline='').read()
                    count   = find_for_body(body, dept, rsp_l, rsp_i)
                else:
                    lines   = open(path, mode='r', encoding=enco_s, newline='').readlines()
                    count   = find_for_lines(lines, dept, rsp_l, rsp_i)
                    if repl_s is not None and count:
                        open(path, mode='w', encoding=enco_s, newline='').write(''.join(lines))
                    # Change text in file
                rsp_i['brow_files']     += 1
                if 0<frst<=rsp_i['frgms']:   break#for enco_n
                if not count:               break#for enco_n
                if prntdct:
        #           prntdct['count']+=count
        #           prntdct = prntdct['prnt']
                    for i in range(25):  ##!! 
                        if not prntdct:  break#for i
        #           while prntdct:
                        prntdct['count']+=count
                        prntdct  = prntdct['prnt']
                    pass;  #FNDLOG and log('tree4rsp={}',pf(tree4rsp))
                break#for enco_n
            except Exception as ex:
                pass;           FNDLOG and log('ex={}',(ex))
                if rpt_enc_fail and enco_n == len(enco_l)-1:
                    print(f(_('Cannot read "{}" (encoding={}/{}): {}'), path, enco_s, enco_l, ex))
           #for encd_n
        if 0<frst<=rsp_i['frgms']:   break#for path
       #for path
    pass;                      #t=None
    pass;                      #FNDLOG and log('rsp_l=¶{}',pf(rsp_l))
    pass;                       LOG and log('ok files ==) #rsp_i={}',rsp_i)
#   pass;                       FNDLOG and log('ok files ==) #rsp_i={}',rsp_i)
    return rsp_l, rsp_i
   #def find_in_files

def prep_filename_masks(mask:str)->(list,list):
    """ Parse file/folder quotes_mask to two lists (file_pure_masks, folder_pure_masks).
        Exaple.
            quotes_mask:    '*.txt "a b*.txt" /m? "/x y"'
            output:         (['*.txt', 'a b*.txt']
                            ,['m?', 'x y'])
    """
    mask    = mask.strip()
    if '"' in mask:
        # Temporary replace all ' ' into "" to '·'
        re_binqu= re.compile(r'"([^"]+) ([^"]+)"')
        while re_binqu.search(mask):
            mask= re_binqu.sub(r'"\1·\2"', mask) 
        masks   = mask.split(' ')
        masks   = [m.strip('"').replace('·', ' ') for m in masks if m]
    else:
        masks   = mask.split(' ')
    fi_masks= [m     for m in masks if m        and m[0]!='/']
    fo_masks= [m[1:] for m in masks if len(m)>1 and m[0]=='/']
    return (fi_masks, fo_masks)
   #def prep_filename_masks
    
def prep_quoted_folders(mask:str)->list:
    """ Parse folders quoted mask to [folder]
        Exaple.
            mask:             /   "/a b/c"   m/n
            output:         ['/', '/a b/c', 'm/n']
    """
    mask    = mask.strip()
    flds    = mask.split(' ')
    if '"' in mask:
        # Temporary replace all ' ' into "" to '·'
        re_binqu= re.compile(r'"([^"]+) ([^"]+)"')
        while re_binqu.search(mask):
            mask= re_binqu.sub(r'"\1·\2"', mask) 
        flds   = mask.split(' ')
        flds   = [f.strip('"').replace('·', ' ') for f in flds if f]
    return flds
   #def prep_quoted_folders
    
def collect_tabs(how_walk:dict)->tuple:
    """ how_walk keys:
            'file_incl'    !str
            'file_excl'     str('')
    """
    incl    = how_walk[    'file_incl'    ].strip()
    excl    = how_walk.get('file_excl', '').strip()
    incls,  \
    incls_fo= prep_filename_masks(incl)
    excls,  \
    excls_fo= prep_filename_masks(excl)
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

def collect_files(how_walk:dict, progressor=None)->tuple:       #NOTE: cllc
    """ how_walk keys:
            'roots'        ![str]
        //  'root'         !str
            'depth'         int(-1)    -1=all, 0=only root
            'file_incl'    !str
            'file_excl'     str('')
            'sort_type'     str('')     ''/'date,desc'/'date,asc'
            'age'           str('<>Nd') ''=all
            'only_frst'     int(0)      0=all
            'skip_hidn'     bool(T)
            'skip_binr'     bool(F) 
            'skip_size'     int(0)      0=all Kbyte
            'skip_unwr'     int(F)      
        Return
            [path], stoped
    """
    pass;                       t=log('>>(:)how_walk={}',how_walk) if LOG else 0 
    roots   = how_walk['roots']
#   root    = how_walk['root']
    
    if not all(map(lambda f:os.path.isdir(f), roots)):  return [], False
#   if                      os.path.isdir(root):        return [], False
    rsp     = []
    stoped  = False
    breaked = False
    incl    = how_walk[    'file_incl'    ].strip()
    excl    = how_walk.get('file_excl', '').strip()
    depth   = how_walk.get('depth', -1)
    hidn    = how_walk.get('skip_hidn', True)
    binr    = how_walk.get('skip_binr', False)
    size    = how_walk.get('skip_size', SKIP_FILE_SIZE)
    unwr    = how_walk.get('skip_unwr', False)
    age     = how_walk.get('age', '')
    frst    = how_walk.get('only_frst', 0)
    sort    = how_walk.get('sort_type', '')
    incls,  \
    incls_fo= prep_filename_masks(incl)
    excls,  \
    excls_fo= prep_filename_masks(excl)
    pass;                      #LOG and log('incls={} incls_fo={}',incls, incls_fo)
    pass;                      #LOG and log('excls={} excls_fo={}',excls, excls_fo)
    
    pass;                       log('age={}',(age))
    age_d   = []
    if age:
        age_u   = age[-1]
        age_n   = int(age[1:-1])
        age_d   = dict( now=datetime.now()
                      , how=age[0]
                      , thr=timedelta(hours=age_n)      if age_u=='h' else
                            timedelta(days =age_n)      if age_u=='d' else
                            timedelta(weeks=age_n)      if age_u=='w' else
                            timedelta(days =age_n*30)   if age_u=='m' else
                            timedelta(days =age_n*365) #if age_u=='y'
                      )
    def with_age(age_d, mtime):
        mdt = datetime.fromtimestamp(mtime)
        dt  = age_d['now'] - mdt
        pass;                  #log('age_d={}',(age_d))
        pass;                  #log('mdt,dt={}',(mdt,dt))
        return dt > age_d['thr'] \
                if  age_d['how']=='>' else \
               dt < age_d['thr']
        
    dir_n   = 0
    for root in roots:
        if stoped:  break#for root
        if breaked: break#for root
        pass;                   LOG and log('root={}',(root))
        for dirpath, dirnames, filenames in os.walk(os.path.abspath(root)):
            pass;              #LOG and log('dirpath, #filenames={}',(dirpath, len(filenames)))
            pass;              #LOG and log('dirpath, dirnames, filenames={}',(dirpath, dirnames, filenames))
            dir_n   += 1
            if progressor and 0==dir_n%13:
                progressor.set_progress(f(_('[ESC?][Found {} file(s) in {} dir(s)] Picking in: {}')
                                        , len(rsp), dir_n ,dirpath))
                if progressor.need_break():
                    if ESC_FULL_STOP:   return [], True
                    stoped  = True
                    progressor.prefix += _('(Picking stopped) ')
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
            if incls_fo:
                dir4cut = [dirname for dirname in dirnames if not any(map(lambda cl:fnmatch(dirname, cl), incls_fo))]
                for dirname in dir4cut:
                    dirnames.remove(dirname)
            if excls_fo:
                dir4cut = [dirname for dirname in dirnames if     any(map(lambda cl:fnmatch(dirname, cl), excls_fo))]
                for dirname in dir4cut:
                    dirnames.remove(dirname)
            
            walk_depth  = 0 \
                            if os.path.samefile(dirpath, root) else \
                          1 +  os.path.relpath( dirpath, root).count(os.sep)
            pass;              #LOG and log('depth,walk_depth={}',(depth,walk_depth))
            if walk_depth>depth>0:
                pass;          #LOG and log('skip root by >depth',())
                dirnames.clear()
                continue#for dirpath
            for filename in filenames:
                if not      any(map(lambda cl:fnmatch(filename, cl), incls)):   continue#for filename
                if excl and any(map(lambda cl:fnmatch(filename, cl), excls)):   continue#for filename
                path    = os.path.join(dirpath, filename)
                if          os.path.islink(path):                               continue#for filename
                if          os.path.getsize(path) == 0:                         continue#for filename
                if size and os.path.getsize(path) > size*1024:                  continue#for filename
                if          not os.access(path, os.R_OK):                       continue#for filename
                if unwr and not os.access(path, os.W_OK):                       continue#for filename
                if hidn and is_hidden_file(path):                               continue#for filename
                if binr and is_birary_file(path):                               continue#for filename
                if age_d and not with_age(age_d, os.path.getmtime(path)):       continue#for filename
                rsp    += [path]
                if  not sort and 0<frst<=len(rsp):
                    break#for filename
               #for filename
            if      not sort and 0<frst<=len(rsp):
                pass;          #LOG and log('break by >frst',())
                breaked = True
                break#for dirpath
            if depth==0:
                pass;          #LOG and log('break root by depth==0',())
#               breaked = True
                break#for dirpath
           #for dirpath
       #for root
    if sort:
        tm_pth  = [(os.path.getmtime(path),path) for path in rsp]
        pass;                  #log('tm_pth={}',(tm_pth))
        rsp     = [tp[1] for tp in sorted(tm_pth, reverse=(sort=='date,desc'))]
        pass;                  #rsp_srt = sorted(tm_pth, reverse=(sort=='date,desc'))
        pass;                  #log('rsp_srt={}',(rsp_srt))
        pass;                  #log('zip(*...)[1]={}',(list(list(zip(*rsp_srt))[1])))
        pass;                  #log('rsp         ={}',(rsp))
        pass;                  #log('rsp==zip(*...)[1] {}',(rsp==list(list(zip(*rsp_srt))[1])))
        if 0<frst<len(rsp):
            rsp = rsp[:frst]
    pass;                       LOG and log('|rsp|, stoped={}',(len(rsp), stoped))
    return rsp, stoped
   #def collect_files

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
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)

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
        self.will_break = False
        app.app_proc(app.PROC_SET_ESCAPE, '0')

    def set_progress(self, msg:str):
        msg_status(self.prefix+msg, process_messages=True)

    def need_break(self, with_request=False, process_hint=_('Stop?'))->bool:
#       was_esc = app.app_proc(app.PROC_GET_ESCAPE, '')
#       app.app_proc(app.PROC_SET_ESCAPE, '0')
#       if was_esc and with_request:
#           if app.ID_YES == app.msg_box(process_hint, app.MB_YESNO+app.MB_ICONQUESTION):
#               return True
#           was_esc = False
#       return was_esc
        if self.will_break and with_request:
            if app.ID_YES == app.msg_box(process_hint, app.MB_YESNO+app.MB_ICONQUESTION):
                return True
            self.will_break = False
        return self.will_break
   #class ProgressAndBreak

def detect_encoding(_path, _detector):
    _detector.reset()
    pass;                  #LOG and log('_path={}',(_path))
    try:
        with open(_path, 'rb') as h_path:
            line    = h_path.readline()
            _lines  = 1
            _bytes  = len(line)
            while line:
                _detector.feed(line)
                if _detector.done:
                    pass;  #LOG and log('done. _detector.result={}',(_detector.result))
                    break
                line    = h_path.readline()
                _lines += 1
                _bytes += len(line)
        _detector.close()
        pass;              #LOG and log('_lines={}, _bytes={} _detector.done={}, _detector.result={}'
                               #        ,_lines,    _bytes,   _detector.done,    _detector.result)
        encoding    = _detector.result['encoding'] if _detector.done else locale.getpreferredencoding()
    except Exception:# as ex:
        pass;              #LOG and log('ex={}',(ex))
        return locale.getpreferredencoding()
    pass;                  #LOG and log('_lines,encoding={}',(_lines,encoding))
    return encoding
   #def detect_encoding

#def undo_by_report():
#   """ Use data from fif-report to undo replacements in files
#   """
#   lxr  = ed.get_prop(app.PROP_LEXER_FILE, '')
#   if lxr.upper() not in lexers_l:         return msg_status(  _('Undo must start from tab with Results of Replace'))
#   line0= ed.get_text_line(0)
#   if not line0.startswith(RPT_REPL_SIGN): return msg_status(f(_('Undo must start from tab with text "{}"'), RPT_REPL_SIGN))
#   if app.ID_YES != app.msg_box(
#                       'Do you want execute undo for all replacements:'
#                  +c13+line0
#                   , app.MB_YESNO+app.MB_ICONQUESTION):        return
#   in_tabs = IN_OPEN_FILES in line0
#   rpt_ed  = ed
#   path    = ''
#   for rpt_n in range(1, rpt_ed.get_line_count()):
#       rpt_s  = rpt_ed.get_text_line(rpt_n)
#  #def undo_by_report

# if __name__ == '__main__' :     # Tests
#     Command().show_dlg()    #??
        
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
[+][a1-kv][10may16] Replace in files
[+][at-kv][10may16] Checks for preset
[+][kv-kv][11may16] Try to save last active control
[-][kv-kv][13may16] Set empty Exclude if hidden
[?][kv-kv][13may16] Custom: hide Append+Firsts
[-][kv-kv][13may16] UnDo for ReplaceInFiles by report
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
[ ][kv-kv][20dec16] Ленивый обход
'''
