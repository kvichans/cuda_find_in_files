''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '3.1.21 2020-03-16'
ToDo: (see end of file)
'''

import  re, os, sys, time, itertools, locale, json, collections, copy

import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
from    cudatext_keys   import *
import  cudax_lib           as apx

from    .cd_plug_lib        import *
from    .cd_fif_api         import *
from    .chardet.universaldetector import UniversalDetector
from    .encodings          import *

odict   = collections.OrderedDict
d       = dict
def first_true(iterable, default=False, pred=None):return next(filter(pred, iterable), default) # 10.1.2. Itertools Recipes

MIN_API_VER     = '1.0.178'
MIN_API_VER     = '1.0.180' # panel group p
MIN_API_VER     = '1.0.183' # on_change
MIN_API_VER     = '1.0.216' # STATUSBAR_SET_AUTOSTRETCH
MIN_API_VER     = '1.0.246' # events for control 'editor'
#MIN_API_VER     = '1.0.249' # on_menu in 'editor', 'val' in 'pages'

pass;                          #Tr.tr   = Tr(get_opt('fif_log_file', '')) if get_opt('fif_log_file', '') else Tr.tr
pass;                          #LOG     = (-9== 9)         or get_opt('fif_LOG'   , False) # Do or dont logging.
pass;                          #from pprint import pformat
pass;                          #pf=lambda d:pformat(d,width=150)
pass;                           ##!! "waits correction"
pass;                          #log('ok',())

_   = get_translation(__file__) # I18N

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

MAX_HIST= apx.get_opt('ui_max_history_edits', 20)
MENU_CENTERED   = app.MENU_CENTERED if app.app_api_version()>='1.0.27' else 0

CFG_PATH= app.app_path(app.APP_DIR_SETTINGS)+os.sep+CFG_FILE

CLOSE_AFTER_GOOD= get_opt('fif_hide_if_success'         , False)
USE_EDFIND_OPS  = get_opt('fif_use_edfind_opt_on_start' , False)
DEF_LOC_ENCO    = 'cp1252' if sys.platform=='linux' else locale.getpreferredencoding()
loc_enco        = get_opt('fif_locale_encoding', DEF_LOC_ENCO)

totb_l          = [TOTB_NEW_TAB, TOTB_USED_TAB]
shtp_l          = [SHTP_SHORT_R, SHTP_SHORT_RCL
                  ,SHTP_MIDDL_R, SHTP_MIDDL_RCL
                  ,SHTP_SPARS_R, SHTP_SPARS_RCL
                  ,SHTP_SHRTS_R, SHTP_SHRTS_RCL
                  ]
dept_l          = [_('+All'), _('Only'), _('+1 level'), _('+2 levels'), _('+3 levels'), _('+4 levels'), _('+5 levels')]
skip_l          = [_("Don't skip"), _('-Hidden'), _('-Binary'), _('-Hidden, -Binary')]
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

TOTB_L          = totb_l
SHTP_L          = shtp_l
DEPT_L          = dept_l
SKIP_L          = skip_l
SORT_L          = sort_l
ENCO_L          = enco_l

def reload_opts():
    api_reload_opts()
    
    global CLOSE_AFTER_GOOD,USE_EDFIND_OPS, loc_enco, enco_l
    CLOSE_AFTER_GOOD= get_opt('fif_hide_if_success'         , False)
    USE_EDFIND_OPS  = get_opt('fif_use_edfind_opt_on_start' , False)
    loc_enco        = get_opt('fif_locale_encoding', DEF_LOC_ENCO)
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
   #def reload_opts()

def limit_len(text, max_len, div='..'):
    if len(text)<=max_len:  return text
    part_len    = int((max_len-2)/2)
    return text[:part_len] + div + text[-part_len:]

class Command:
    def find_in_ed(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        filename= ed.get_filename()
        incl_s  = os.path.basename(filename) if filename else ed.get_prop(app.PROP_TAB_TITLE)
        incl_s  = '"'+incl_s+'"' if ' ' in incl_s else incl_s
        return dlg_fif(what='', opts=dict(
             incl = incl_s
            ,fold = IN_OPEN_FILES
            ))
       #def find_in_ed

    def find_in_tabs(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        return dlg_fif(what='', opts=dict(
             incl = '*'
            ,fold = IN_OPEN_FILES
            ))
       #def find_in_ed

    def repeat_find_by_rpt(self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        if ed.get_prop(app.PROP_LEXER_FILE).upper() not in lexers_l:
            return app.msg_status(_('The command works only with reports of FindInFiles plugin'))
        req_opts  = report_extract_request(ed)
        if not req_opts:
            return app.msg_status(_('No info to repeat search'))
        req_opts= json.loads(req_opts)
        what    = req_opts.pop('what', '')
        return dlg_fif(what=what, opts=req_opts)
       #def repeat_find_by_rpt

    def show_dlg(self, what='', opts={}):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        return dlg_fif(what, opts)

    def _nav_to_src(self, where:str, how_act='move'):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        return nav_to_src(where, how_act)
    def _jump_to(self, drct:str, what:str):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        return jump_to(drct, what)
    def on_goto_def(self, ed_self):
        if app.app_api_version()<MIN_API_VER: return app.msg_status(_('Must update the application'))
        if ed_self.get_prop(app.PROP_LEXER_FILE).upper() in lexers_l:
            self._nav_to_src('same', 'move')
            return True
    def on_click_dbl(self, ed_self, scam):
        dcls    = Command.get_dcls()
        dcl     = dcls.get(scam, '')
        pass;                  #LOG and log('scam, dcl={}',(scam, dcl))
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
            stores  = json.loads(re.sub(r',\s*}', r'}', open(CFG_PATH).read()), object_pairs_hook=odict) \
                        if os.path.exists(CFG_PATH) and os.path.getsize(CFG_PATH) != 0 else \
                      odict()
            Command.dcls    = stores.get('dcls', Command.dcls_def)
        return Command.dcls
       #def get_dcls
    
    def dlg_nav_by_dclick(self):
        dlg_nav_by_dclick()

    def dlg_fif_opts(self):
        return dlg_fif_opts()
   #class Command

FIF_META_OPTS=[
    {   "cmt": re.sub(r'  +', r'', _(
               """Option allows to save separate search settings
                (search text, source folder, files mask etc)
                per each mentioned session or project.
                Each item in the option is RegEx,
                which is compared with the full path of session (project).
                First matched item is used.""")),
        "def": [],
        "frm": "json",
        "opt": "fif_sep_hist_for_sess_proj",
        "chp": _("History"),
        "tgs": []
    },

    {   "cmt": _("Copy options [.*], [aA], [\"w\"] from CudaText dialog to plugin's dialog."),
        "def": False,
        "frm": "bool",
        "opt": "fif_use_edfind_opt_on_start",
        "chp": _("Start"),
        "tgs": ["start", "settings"]
    },
    {   "cmt": _("Use selection text from current file when dialog opens."),
        "def": False,
        "frm": "bool",
        "opt": "fif_use_selection_on_start",
        "chp": _("Start"),
        "tgs": ["start"]
    },
    {   "cmt": _("Store Results between dialog call if setting is \"[ ]Send\"."),
        "def": True,
        "frm": "bool",
        "opt": "fif_store_prev_results",
        "chp": _("Start"),
        "tgs": ["start"]
    },

    {   "cmt": re.sub(r'  +', r'', _(
               """List of lexer names to use for report file.
                  First available lexer is used.""")),
        "def": [
            "Search results",
            "FiF"
        ],
        "frm": "json",
        "opt": "fif_lexers",
        "chp": _("Report"),
        "tgs": ["lexer", "report"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Auto-write 'tab_size' to report's lexer-specific config,
               if no such setting. Use 0 to skip.""")),
        "def": 2,
        "frm": "int",
        "opt": "fif_lexer_auto_tab_size",
        "chp": _("Report"),
        "tgs": ["lexer", "report"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Allows Esc key to stop all stages of current search.
                If false, Esc stops only the current stage.""")),
        "def": False,
        "frm": "bool",
        "opt": "fif_esc_full_stop",
        "chp": _("Searching"),
        "tgs": ["searching", "stop"]
    },

    {   "cmt": _("Show report even if nothing found."),
        "def": False,
        "frm": "bool",
        "opt": "fif_report_no_matches",
        "chp": _("Report"),
        "tgs": ["report", "comfort"]
    },
    {   "cmt": _("[x]Append: Need to fold previous results."),
        "def": False,
        "frm": "bool",
        "opt": "fif_fold_prev_res",
        "chp": _("Report"),
        "tgs": ["report", "append", "comfort"]
    },
    {   "cmt": _("Close dialog if search has found matches."),
        "def": False,
        "frm": "bool",
        "opt": "fif_hide_if_success",
        "chp": "",
        "tgs": ["comfort"]
    },
    {   "cmt": _("Length of substring (from field \"Find\"), which appears in the report document title."),
        "def": 10,
        "frm": "int",
        "opt": "fif_len_target_in_title",
        "chp": _("Report"),
        "tgs": ["report", "comfort"]
    },
    {   "cmt": _("If report document has a filename, save report after filling it."),
        "def": False,
        "frm": "bool",
        "opt": "fif_auto_save_if_file",
        "chp": _("Report"),
        "tgs": ["report", "file"]
    },
    {   "cmt": _("Activate document with report after filling it."),
        "def": True,
        "frm": "bool",
        "opt": "fif_focus_to_rpt",
        "chp": _("Report"),
        "tgs": ["report", "comfort"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Save search details (\"Find\", \"In folder\", …) in the first line of report.
                The info will be used in command \"Repeat search for this report-tab\".""")),
        "def": False,
        "frm": "bool",
        "opt": "fif_save_request_to_rpt",
        "chp": _("Report"),
        "tgs": ["report", "comfort"]
    },

    {   "cmt": _("Append specified string to the field 'Not in files'."),
        "def": "/.svn /.git /.hg /.idea",
        "frm": "str",
        "opt": "fif_always_not_in_files",
        "chp": _("Searching"),
        "tgs": ["searching"]
    },
    {   "cmt": _("Size of buffer (at file start) to detect binary files."),
        "def": 1024,
        "frm": "int",
        "opt": "fif_read_head_size(bytes)",
        "chp": _("Searching"),
        "tgs": ["searching", "internal"]
    },
    {   "cmt": _("If value>0, skip all files, which sizes are bigger than this value (in Kb)."),
        "def": 0,
        "frm": "int",
        "opt": "fif_skip_file_size_more_Kb",
        "chp": _("Searching"),
        "tgs": ["searching", "scope"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Default encoding to read files.
                If value is empty, then the following is used:
                  cp1252 for Linux,
                  preferred encoding from locale for others (Win, macOS, …).""")),  #! Shift uses chr(160)
        "def": "",
        "frm": "str",
        "opt": "fif_locale_encoding",
        "chp": _("Searching"),
        "tgs": ["searching", "internal", "encoding"]
    },

    {   "cmt": re.sub(r'  +', r'', _(
               """Style to mark found fragment in report.
                Full form:
                   "fif_mark_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave" """)),  #! Shift uses chr(160)
        "def": {"borders": {"bottom": "dotted"}},
        "frm": "json",
        "opt": "fif_mark_style",
        "chp": _("Report"),
        "tgs": ["report", "mark"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Style to mark replaced fragment in report (unique in line).
                Full form:
                   "fif_mark_true_replace_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave" """)),  #! Shift uses chr(160)
        "def": {"borders": {"bottom": "solid"}},
        "frm": "json",
        "opt": "fif_mark_true_replace_style",
        "chp": _("Report"),
        "tgs": ["report", "mark"]
    },
    {   "cmt": re.sub(r'  +', r'', _(
               """Style to mark replaced fragment in report (not unique in line).
                Full form:
                   "fif_mark_false_replace_style":{
                     "color_back":"", 
                     "color_font":"",
                     "font_bold":false, 
                     "font_italic":false,
                     "color_border":"", 
                     "borders":{"left":"","right":"","bottom":"","top":""}
                   },
                Color values: "" - skip, "#RRGGBB" - hex-digits
                Values for border sides: "solid", "dash", "2px", "dotted", "rounded", "wave" """)),  #! Shift uses chr(160)
        "def": {"borders": {"bottom":"wave"},"color_border":"#777"},
        "frm": "json",
        "opt": "fif_mark_false_replace_style",
        "chp": _("Report"),
        "tgs": ["report", "mark"]
    },

    {   "cmt": "Allows logging for all search stages.",
        "def": False,
        "frm": "bool",
        "opt": "fif_LOG",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Allows logging for searching stage.",
        "def": False,
        "frm": "bool",
        "opt": "fif_FNDLOG",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Allows logging for reporting stage.",
        "def": False,
        "frm": "bool",
        "opt": "fif_RPTLOG",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Allows logging for navigation stage.",
        "def": False,
        "frm": "bool",
        "opt": "fif_NAVLOG",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Append internal debug data to report.",
        "def": False,
        "frm": "bool",
        "opt": "fif_DBG_data_to_report",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Specifies filename of log file.",
        "def": "",
        "frm": "file",
        "opt": "fif_log_file",
        "chp": "Logging",
        "tgs": ["log", "internal"]
    },
    {   "cmt": "Allows logging about failed file reads (encoding errors).",
        "def": False,
        "frm": "bool",
        "opt": "fif_log_encoding_fail",
        "chp": "Logging",
        "tgs": ["log", "internal", "encoding"]
    }
    ]

#]   + ([] if app.app_api_version()<'1.0.289' else[  # Editor.action() with EDACTION_CODETREE_FILL and EDACTION_LEXER_SCAN
#   {   "cmt": re.sub(r'  +', r'', _(
#              """For these lexers to show in dialog statusbar
#                 path into CodeTree to current fragment in Source panel.""")),
#       "def": [
#           "Python",
#       ],
#       "frm": "json",
#       "opt": "fif_codetree_path_in_status",
#       "chp": _("Report"),
#       "tgs": ["lexer", "report"]
#   }
#   ])
def dlg_fif_opts(dlg=None):
    try:
        import cuda_options_editor as op_ed
    except:
        return app.msg_box(_('To view/edit options install plugin "Options Editor"'),app.MB_OK)

    dlg.store(what='save') if dlg else 0
    # Transfer options from "user.json" to CFG_FILE
    for opt_d in FIF_META_OPTS:
        opt = opt_d['opt']
        if 'no-no-no'!=apx.get_opt(opt, 'no-no-no', user_json=CFG_FILE):    continue    # Already transfered
        opt_val_user = apx.get_opt(opt)
        if opt_val_user is None:                                            continue    # Nothing to transfer
        pass;                  #log("trans: opt,opt_val_user={}",(opt,opt_val_user))
        apx.set_opt(opt, opt_val_user, user_json=CFG_FILE)

    try:
        op_ed.OptEdD(
          path_keys_info=FIF_META_OPTS
#         path_keys_info=os.path.dirname(__file__)+os.sep+'fif_opts_def.json'
        , subset        ='fif-df.'
#       , how           =dict(only_for_ul=True, only_with_def=True)
#       , how           =dict(only_for_ul=True, only_with_def=True, hide_fil=True)
        , how           =dict(only_for_ul=True, only_with_def=True, hide_fil=True, stor_json=CFG_FILE)
        ).show(_('"Find in Files" options'))
    except Exception as ex:
        pass;                   log('ex={}',(ex))
#       FIF_OPTS    = os.path.dirname(__file__)+os.sep+'fif_options.json'
#       fif_opts    = json.loads(open(FIF_OPTS).read())
#       op_ed.dlg_opt_editor('FiF options', fif_opts, subset='fif.')

    dlg.store(what='load') if dlg else 0
    reload_opts()
   #def dlg_fif_opts

class PresetD:
    keys_l  = ['reex','case','word'
              ,'incl','excl'
              ,'fold','dept'
              ,'skip','sort','olde','frst','enco'
                     ,'send'
                     ,'totb','join','shtp','algn'
                     ,'cntx','cntb','cnta']
    caps_l  = ['.*','aA','"w"'
              ,'In files','Not in files'
              ,'In folder','Subfolders'
              ,'Skip files','Sort file list','Age','Firsts','Encodings'
                     ,'[Report] Send to tab/file'
                     ,'[Report] Show in','[Report] Append results','[Report] Tree type','[Report] Align'
                     ,'[Report] Show context','[Report] Context "before"','[Report] Context "after"']
    yn01    = {'0':_('No'), '1':_('Yes'), _('No'):'0', _('Yes'):'1'}
    
    @staticmethod
    def desc_fif_val(fifkey, val=None):
        pass;                      #LOG and log('fifkey, val={}',(fifkey, val))
        if val is None: return ''
        if False:pass
        elif fifkey in ('incl','excl','fold','frst','cntb','cnta'):   return val
        elif fifkey in ('reex','case','word'
                       ,'send','join','algn','cntx'):   return PresetD.yn01[val] #_('Yes') if val=='1' else _('No')
        elif fifkey=='totb':    return totb_l[int(val)] if val in ('0', '1') else val
        elif fifkey=='olde':    return ('<'+val).replace('<<', '<').replace('<>', '>').replace('/', '')
        pass;                      #log('fifkey, val={}',(fifkey, val))
        val = int(val)
        if False:pass
        elif fifkey=='dept':    return dept_l[val] if 0<=val<len(dept_l) else ''
        elif fifkey=='skip':    return skip_l[val] if 0<=val<len(skip_l) else ''
        elif fifkey=='sort':    return sort_l[val] if 0<=val<len(sort_l) else ''
        elif fifkey=='enco':    return enco_l[val] if 0<=val<len(enco_l) else ''
        elif fifkey=='shtp':    return shtp_l[val] if 0<=val<len(shtp_l) else ''
       #def desc_fif_val

    def __init__(self, fif):
        self.fif    = fif
       #def PresetD.__init__

    def config(self):
        M,m     = self.__class__,self
        pset_l  = copy.deepcopy(m.fif.stores.get('pset', []))
        if not pset_l:  return msg_status(_('No preset to config'))
        for ps in pset_l:
            M.upgrd(ps)

        def save_close(cid, ag, data=''):
            if pset_l:
                ps_ind      = ag.cval('prss')
                ps          = pset_l[ps_ind]
                ps['name']  = ag.cval('name')
                self._restore(ps)
                msg_status(_('Options is restored from preset')+': '+ps['name'])
            m.fif.stores['pset']    = pset_l    #stores_main.update(stores)
            open(CFG_PATH, 'w').write(json.dumps(m.fif.stores, indent=4))
            return None
           #def save_close
            
        def acts(cid, ag, data=''):
            if not pset_l:  return {}
            ps_ind      = ag.cval('prss')
            ps          = pset_l[ps_ind]
            new_name    = ag.cval('name')
            prss_nms    = []
            if ps['name'] != new_name:
                ps['name']  = new_name
            if False:pass
            elif cid=='what':
                pass;          #log('ps={}',(ps))
                pass;          #log('what.val={}',(ag.cval('what')))
                ps_vls  = ag.cval('what')[1]
                pass;          #log('ps_vls={}',(ps_vls))
                for i,k in enumerate(M.keys_l):
                    ps['_'+k]   = 'x' if ps_vls[i]=='1' else '-'
                pass;          #log('ps={}',(ps))
            elif cid=='mvup' and ps_ind>0 \
            or   cid=='mvdn' and ps_ind<len(pset_l)-1:
                mv_ind  = ps_ind + (-1 if cid=='mvup' else 1)
                pset_l[mv_ind], \
                pset_l[ps_ind]  = pset_l[ps_ind], \
                                  pset_l[mv_ind]
                ps_ind  = mv_ind
                ps_mns  = [ps['name'] for ps in pset_l]
                return dict(
                    ctrls=[('prss',dict(items=ps_mns, val=ps_ind)   )
                          ,('mvup',dict(en=ps_ind>0)                )
                          ,('mvdn',dict(en=ps_ind<(len(pset_l)-1))  )
                          ]
                   ,fid='prss')
            elif cid=='delt':
                pset_l.pop(ps_ind)
                ps_ind  = min(ps_ind, len(pset_l)-1)
                ps      = pset_l[ps_ind]                                                            if pset_l else {}
                pass;              #LOG and log('ps={}',(ps))
                ps_mns  = [ps['name'] for ps in pset_l]
                ps_its  = [f('{}', M.caps_l[i]                  ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
                ps_vas  = [f('{}', M.desc_fif_val(k, ps.get(k)) ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
                ps_vls  = [('1' if ps['_'+k]=='x' else '0'      ) for    k in           M.keys_l ]  if pset_l else ['0']
                return dict(
                    ctrls=[('prss',dict(items=ps_mns, val=ps_ind)                   )
                          ,('name',dict(              val=ps['name'])               )
                          ,('what',dict(items=ps_its, val=(-1,ps_vls))              )
                          ,('vals',dict(items=ps_vas, val=(-1,ps_vls))  )
                          ,('mvup',dict(en=len(pset_l)>0 and ps_ind>0)              )
                          ,('mvdn',dict(en=len(pset_l)>0 and ps_ind<(len(pset_l)-1)))
                          ,('clon',dict(en=len(pset_l)>0)                           )
                          ,('delt',dict(en=len(pset_l)>0)                           )
                          ]
                   ,fid='prss')
            elif cid=='clon':
                ps  = pset_l[ps_ind]
                psd = {k:v for k,v in ps.items()}
                pset_l.insert(ps_ind, psd)
                ps_mns  = [ps['name'] for ps in pset_l]
                return dict(
                    ctrls=[('prss',dict(items=ps_mns, val=ps_ind)   )
                          ,('mvup',dict(en=ps_ind>0)                )
                          ,('mvdn',dict(en=ps_ind<(len(pset_l)-1))  )
                          ]
                   ,fid='prss')
            
            pass;               LOG and log('no act: cid,ps_ind={}',(cid,ps_ind))
            return {'fid':'prss'}
           #def acts
        
        def fill_what(cid, ag, data=''):
            ps_ind  = ag.cval('prss')
            prss_nms= [('prss',dict(val=ps_ind))]
            if pset_l:
                ps_ind_p    = ag.cval('prss', live=False)
                pass;          #LOG and log('ps_ind,ps_ind_p={}',(ps_ind,ps_ind_p))
                ps_p        = pset_l[ps_ind_p]
                if ps_p['name']!= ag.cval('name'):
                    ps_p['name']= ag.cval('name')
                    ps_mns      = [ps['name'] for ps in pset_l]
                    prss_nms    = [('prss',dict(items=ps_mns, val=ps_ind))]
            pass;              #LOG and log('ps_ind={}',(ps_ind))
            ps      = pset_l[ps_ind]                                                            if pset_l else {}
            pass;              #LOG and log('ps={}',(ps))
            ps_its  = [f('{}', M.caps_l[i]                  ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
            ps_vas  = [f('{}', M.desc_fif_val(k, ps.get(k)) ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
            ps_vls  = [('1' if ps['_'+k]=='x' else '0'      ) for    k in           M.keys_l ]  if pset_l else ['0']
            return dict(
                ctrls=[('what',dict(items=ps_its, val=(-1,ps_vls))  )
                      ,('vals',dict(items=ps_vas, val=(-1,ps_vls))  )
                      ,('name',dict(              val=ps['name'])   )
                      ,('mvup',dict(en=ps_ind>0)                    )
                      ,('mvdn',dict(en=ps_ind<(len(pset_l)-1))      )
                      ]+prss_nms
               ,fid='prss')
           #def fill_what

        ps_ind      = 0
        ps          = pset_l[ps_ind]                                                            if pset_l else {}
        DLG_W       = 5*4+245+400
        ps_mns      = [ps['name'] for ps in pset_l]                                             if pset_l else [' ']
        ps_its      = [f('{}', M.caps_l[i]                  ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
        ps_vas      = [f('{}', M.desc_fif_val(k, ps.get(k)) ) for i, k in enumerate(M.keys_l)]  if pset_l else [' ']
        ps_vls      = [('1' if ps['_'+k]=='x' else '0'      ) for    k in           M.keys_l ]  if pset_l else ['0']
        pass;              #LOG and log('ps_mns={}',(ps_mns))
        pass;              #LOG and log('ps_its={}',(ps_its))
        ctrls   = [0
                 ,('lprs',dict(tp='lb'  ,t=5            ,l=5        ,w=245  ,cap=_('&Presets:')                                                     )) # &p
                 ,('prss',dict(tp='lbx' ,t=5+20,h=345   ,l=5        ,w=245  ,items=ps_mns       ,en=(len(pset_l)>0)  ,val=ps_ind    ,call=fill_what )) #
                  # Content
                 ,('lnam',dict(tp='lb'  ,t=5+20+345+10  ,l=5        ,w=245  ,cap=_('&Name:')                                                        )) # &n
                 ,('name',dict(tp='ed'  ,t=5+20+345+30  ,l=5        ,w=245                      ,en=(len(pset_l)>0)  ,val=ps.get('name', '')        )) # 
                  # Acts
                 ,('mvup',dict(tp='bt'  ,t=435          ,l=5        ,w=120  ,cap=_('Move &up')  ,en=(len(pset_l)>1) and ps_ind>0    ,call=acts      )) # &u
                 ,('mvdn',dict(tp='bt'  ,t=460          ,l=5        ,w=120  ,cap=_('Move &down'),en=(len(pset_l)>1)                 ,call=acts      )) # &d
                 ,('clon',dict(tp='bt'  ,t=435          ,l=5*2+120  ,w=120  ,cap=_('Clon&e')    ,en=(len(pset_l)>0)                 ,call=acts      )) # &e
                 ,('delt',dict(tp='bt'  ,t=460          ,l=5*2+120  ,w=120  ,cap=_('Dele&te')   ,en=(len(pset_l)>0)                 ,call=acts      )) # &t
                  #
                 ,('lwha',dict(tp='lb'  ,t=5            ,l=260      ,w=180  ,cap=_('&What to restore:')                                             )) # &w
                 ,('what',dict(tp='clx' ,t=5+20,h=400   ,l=260      ,w=180  ,items=ps_its       ,en=T               ,val=(-1,ps_vls),call=acts      ))
                 ,('lval',dict(tp='lb'  ,t=5            ,l=260+180+1,w=220-1,cap=_('With values:')                                                  )) # &
                 ,('vals',dict(tp='clx' ,t=5+20,h=400   ,l=260+180+1,w=220-1,items=ps_vas       ,en=F               ,val=(-1,ps_vls)                ))
                  #
                 ,('!'   ,dict(tp='bt'  ,t=435          ,l=DLG_W-5-100,w=100,cap=_('Apply')     ,def_bt=True                        ,call=save_close)) # &
                 ,('-'   ,dict(tp='bt'  ,t=460          ,l=DLG_W-5-100,w=100,cap=_('Cancel')                                        ,call=LMBD_HIDE ))
                 ][1:]
        DlgAgent(form   =dict(cap=_('Presets'), w=DLG_W, h=490)
                ,ctrls  =ctrls
                ,fid    ='prss'
                              #,options={'gen_repro_to_file':'repro_prs_config.py'}
        ).show()
        return None
       #def config

    def save(self):
        M,m     = self.__class__,self
        m.fif.copy_vals(m.fif.ag)
        pset_l  = m.fif.stores.get('pset', [])
        totb_i  = m.fif.totb_i if 0<m.fif.totb_i<4+len(m.fif.stores.get('tofx', [])) else 1   # "tab:" skiped
        totb_v  = m.fif.totb_l[totb_i]
        invl_l  = (m.fif.reex01,m.fif.case01,m.fif.word01,
                   m.fif.incl_s,m.fif.excl_s,
                   m.fif.fold_s,m.fif.dept_n,
                   m.fif.skip_s,m.fif.sort_s,m.fif.olde_s,m.fif.frst_s,m.fif.enco_s,
                   m.fif.send_s,
                   totb_v,m.fif.join_s,m.fif.shtp_s,m.fif.algn_s,m.fif.cntx_s,m.fif.cntx_b,m.fif.cntx_a)

        ps_its  = [f('{}', M.caps_l[i]                  ) for i, k in enumerate(M.keys_l)]
        ps_vas  = [f('{}', M.desc_fif_val(k, invl_l[i]) ) for i, k in enumerate(M.keys_l)]
        send_i  = M.keys_l.index('send')
        what_vs = ['1']*len(M.keys_l) 
        if m.fif.send_s=='0':
            what_vs[send_i+1:]   = ['0']*(len(what_vs)-send_i-1)
        if not  m.fif.incl_s:   what_vs[M.keys_l.index('incl')]   = '0'
        if not  m.fif.excl_s:   what_vs[M.keys_l.index('excl')]   = '0'
        if not  m.fif.fold_s:   what_vs[M.keys_l.index('fold')]   = '0'
        if '0'==m.fif.frst_s:   what_vs[M.keys_l.index('frst')]   = '0'
        btn,vals,*_t   = dlg_wrapper(_('Save preset'), GAP+400+GAP,GAP+500+GAP,     #NOTE: dlg-pres-new
             [dict(           tp='lb'   ,t=GAP              ,l=GAP          ,w=300  ,cap=_('&Name:')            ) # &n
             ,dict(cid='name',tp='ed'   ,t=GAP+20           ,l=GAP          ,w=400                              ) # 
             ,dict(           tp='lb'   ,t=GAP+55           ,l=GAP          ,w=300  ,cap=_('&What to save:')    ) # &w
             ,dict(cid='what',tp='clx'  ,t=GAP+75,h=390     ,l=GAP          ,w=180  ,items=ps_its               )
             ,dict(           tp='lb'   ,t=GAP+55           ,l=GAP+180+1    ,w=220-1,cap=_('With values:')      ) # &
             ,dict(cid='vals',tp='clx'  ,t=GAP+75,h=390     ,l=GAP+180+1    ,w=220-1,items=ps_vas   ,en=F       )
             ,dict(cid='!'   ,tp='bt'   ,t=GAP+500-28       ,l=GAP+400-170  ,w=80   ,cap=_('OK')    ,def_bt=True) # &
             ,dict(cid='-'   ,tp='bt'   ,t=GAP+500-28       ,l=GAP+400-80   ,w=80   ,cap=_('Cancel')            )
             ],    dict(name=f(_('#{}: "{}" in "{}"'), 1+len(pset_l), m.fif.incl_s, m.fif.fold_s)
                       ,what=(0 ,what_vs)
                       ,vals=(-1,what_vs)), focus_cid='name')
        pass;                  #LOG and log('vals={}',vals)
        if btn is None or btn=='-': return None
        ps_name = vals['name']
        sl,vals = vals['what']
        pass;                  #LOG and log('vals={}',vals)
        ps      = odict([('name',ps_name)])
        for i, k in enumerate(M.keys_l):
            if vals[i]=='1':
                ps['_'+k] = 'x'
                ps[    k] = invl_l[i]
            else:
                ps['_'+k] = '-'
        pass;                  #LOG and log('ps={}',(ps))
        pset_l += [ps]
        m.fif.stores['pset']    = pset_l    #stores_main.update(stores)
        open(CFG_PATH, 'w').write(json.dumps(m.fif.stores, indent=4))
        msg_status(_('Options is saved to preset: ')+ps['name'])
        return None
       #def save

    def _restore(self, ps):
        M,m     = self.__class__,self
        for i, k in enumerate(M.keys_l):
            if ps.get('_'+k, '')!='x':  continue
            if 0:pass
            elif k=='reex':     m.fif.reex01 = ps[k]
            elif k=='case':     m.fif.case01 = ps[k]
            elif k=='word':     m.fif.word01 = ps[k]
            elif k=='incl':     m.fif.incl_s = ps[k]
            elif k=='excl':     m.fif.excl_s = ps[k]
            elif k=='fold':     m.fif.fold_s = ps[k]
            elif k=='dept':     m.fif.dept_n = ps[k]
            elif k=='skip':     m.fif.skip_s = ps[k]
            elif k=='sort':     m.fif.sort_s = ps[k]
            elif k=='olde':     m.fif.olde_s = ps[k]
            elif k=='frst':     m.fif.frst_s = ps[k]
            elif k=='enco':     m.fif.enco_s = ps[k]
            elif k=='send':     m.fif.send_s = ps[k]
            elif k=='join':     m.fif.join_s = ps[k]
            elif k=='shtp':     m.fif.shtp_s = ps[k]
            elif k=='algn':     m.fif.algn_s = ps[k]
            elif k=='cntx':     m.fif.cntx_s = ps[k]
            elif k=='cntb':     m.fif.cntx_b = ps[k]
            elif k=='cnta':     m.fif.cntx_a = ps[k]
            elif k=='totb':
                totb_v       = ps[k]
                m.fif.totb_i = m.fif.totb_l.index(totb_v) if totb_v in m.fif.totb_l else \
                               totb_v                     if totb_v in (0, 1)       else \
                               1
       #def _restore

    def ind4rest(self, ps_ind):
        M,m     = self.__class__,self
        m.fif.copy_vals(m.fif.ag)
        pset_l  = m.fif.stores.get('pset', [])
        if ps_ind>=len(pset_l):     return None
        ps      = M.upgrd(pset_l[ps_ind])
        m._restore(ps)
        m.fif.store()
        msg_status(_('Options is restored from preset: ')+ps['name'])
        return True
       #def ind4rest

    @staticmethod
    def upgrd(ps:list)->list:
        if 'olde' not in ps:  
            ps['olde']  = '0/d'
            ps['_olde'] = 'x'
        if 'cntb' not in ps:  
            ps['cntb']  = 1
            ps['_cntb'] = 'x'
            ps['cnta']  = 1
            ps['_cnta'] = 'x'
        if 'send' not in ps:  
            ps['send']  = '1'
            ps['_send'] = 'x'
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
        ps['_totb'] = 'x' if _rp else '-'
        ps['_join'] = 'x' if _rp else '-'
        ps['_shtp'] = 'x' if _rp else '-'
        ps['_algn'] = 'x' if _rp else '-'
        ps['_cntx'] = 'x' if _rp else '-'
        return ps
       #def upgrd
   #class PresetD


_TREE_BODY  = _(r'''
If report will be sent to tab 
    [x] Send
then option "Tree type" in dialog "{morp}" allows to set:
 
{shtp}
''')
#_KEYS_TABLE = open(os.path.dirname(__file__)+os.sep+r'readme'+os.sep+f('help hotkeys.txt')  , encoding='utf-8').read()
_KEYS_TABLE = _(r'''
┌────────────────────────────┬──────────────┬────────────────────────────┬───────────────────────────────────────────┐
│          Command           │    Hotkey    │           Trick            │                  Comment                  │
╞════════════════════════════╪══════════════╪════════════════════════════╪═══════════════════════════════════════════╡
│ Find                       │        Enter │                            │ If focus not in Results/Source            │
│ Count matches              │        Alt+T │                            │                                           │
│ Find filenames             │       Ctrl+T │                            │                                           │
├────────────────────────────┼──────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ Focus to Results           │   Ctrl+Enter │                            │ If focus not in Results/Source            │
│ Open found fragment        │        Enter │                            │ If focus in Results. Selects the fragment │
│ Close and go to found      │   Ctrl+Enter │                            │ If focus in Results. Selects the fragment │
│ Close and go to found      │   Ctrl+Enter │                            │ If focus in Source. Restores selection    │
│ Fold Results branch        │       Ctrl+= │                            │ If focus in Results                       │
├────────────────────────────┼──────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ In current file            │ Ctrl+Shift+C │      Shift+Сlick "Current" │                                           │
│ In all tabs                │              │ Ctrl      +Сlick "Current" │                                           │
│ In current tab             │              │ Ctrl+Shift+Сlick "Current" │                                           │
│ Choose file                │       Ctrl+B │      Shift+Сlick  "Browse" │                                           │
│ Depth "Only"               │        Alt+Y │                  Ctrl+Num0 │                                           │
│ Depth "+1 level"           │        Alt+! │                  Ctrl+Num1 │                                           │
│ Depth "All"                │        Alt+L │                  Ctrl+Num9 │                                           │
├────────────────────────────┼──────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ Save values as preset      │       Ctrl+S │                            │                                           │
│ Presets dialog             │   Ctrl+Alt+S │                            │                                           │
│ Use Preset #1(..#5)        │  Ctrl+1(..5) │                            │ Others from menu/dialog                   │
│ Use Layout #1(..#5)        │   Alt+1(..5) │                            │ Others from menu                          │
├────────────────────────────┼──────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ ±"Not in"/±"Replace"       │        Alt+V │                            │ 4-states loop to show/hide                │
│ Engine options             │       Ctrl+E │                            │                                           │
│ Configure vert. alignments │              │             Ctrl+Сlick "=" │                                           │
├────────────────────────────┼──────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ Call CudaText's "Find"     │       Ctrl+F │                            │ With transfer patern/.*/aA/"w"            │
│ Call CudaText's "Replace"  │       Ctrl+R │                            │ With transfer paterns/.*/aA/"w"           │
│ Dialog "Help"              │        Alt+H │                            │                                           │
└────────────────────────────┴──────────────┴────────────────────────────┴───────────────────────────────────────────┘
''')
#_TIPS_BODY  = open(os.path.dirname(__file__)+os.sep+r'readme'+os.sep+f('help hints.txt')    , encoding='utf-8').read()
_TIPS_BODY  = _(r'''
• ".*" - Option "Regular Expression". 
It allows to use in field "Find what" special symbols:
    .   any character
    \d  digit character (0..9)
    \w  word-like character (digits, letters, "_")
In field "Replace with":
    \1  to insert first found group,
    \2  to insert second found group, ... 
See full documentation on page
    docs.python.org/3/library/re.html
 
• "w" - {word}
 
—————————————————————————————————————————————— 
 
• Values in fields "{incl}" and "{excl}" can contain
    ?       for any single char,
    *       for any substring (may be empty),
    [seq]   any character in seq,
    [!seq]  any character not in seq. 
Note: 
    *       matches all names, 
    *.*     doesn't match all.
 
• Values in fields "{incl}" and "{excl}" can filter subfolder names 
if they start with "/".
Example.
    {incl:12}: /a*  *.txt
    {excl:12}: /ab*
    {fold:12}: c:/root
    Depth       : All
    Search will consider all *.txt files in folder c:/root
    and in all subfolders a* except ab*.
 
• Set special value "{tags}" (in short <t> or <Tabs>) for field "{fold}" to search in opened documents.
Fields "{incl}" and "{excl}" will be used to filter tab titles, in this case.
To search in all tabs, use mask "*" in field "{incl}".
See also: menu items under button "=", "Scope".
 
• Set special value "{proj}" (in short <p>) for field "{fold}" to search in project files.
See also: menu items under button "=", "Scope".
 
—————————————————————————————————————————————— 
 
• "Age" (advanced search options).
    {olde}
 
• "First" (advanced search options).
    {frst}
 
—————————————————————————————————————————————— 
 
• Long-term searches can be interrupted by ESC.
Search has three stages: 
    picking files, 
    finding fragments, 
    reporting.
ESC stops any stage. 
When picking and finding, ESC stops only this stage, so next stage begins.
 
—————————————————————————————————————————————— 
 
• Use right click or Context keyboard button 
to see context menu over these elements
    "Find", "Replace", "Current", "Browse", Depth combobox
 
—————————————————————————————————————————————— 
You are welcome to plugin forum. See bottom link.
''')
RE_DOC_URL  = 'https://docs.python.org/3/library/re.html'
GH_ISU_URL  = 'https://github.com/kvichans/cuda_find_in_files/issues'

def dlg_fif_help(fif, stores=None):
    stores      = {} if stores is None else stores
    TIPS_BODY   =_TIPS_BODY.strip().format(
                    word=word_h
                  , incl=fif.caps['incl']
                  , excl=fif.caps['excl']
                  , fold=fif.caps['fold']
                  , olde=olde_h
                  , frst=frst_h
                  , tags=IN_OPEN_FILES
                  , proj=IN_PROJ_FOLDS)
    TREE_BODY   =_TREE_BODY.strip().format(
                    morp=morp_h
                  , shtp=shtp_h)
    KEYS_TABLE  = _KEYS_TABLE.strip('\n\r')
    c2m         = 'mac'==get_desktop_environment() #or True
    KEYS_TABLE  = _KEYS_TABLE.strip('\n\r').replace('Ctrl+', 'Meta+') if c2m else KEYS_TABLE
    page        = stores.get('page', 0)
    ag_hlp      = DlgAgent(
              form  =dict( cap      =_('"Find in Files" help')
                          ,w        = 960+10
                          ,h        = 580+10
                          ,resize   = True
                          )
            , ctrls = [0
                ,('tabs',dict(tp='pgs'  ,l=5,w=960  
                                        ,t=5,h=580  ,a='lRtB'   ,items=[_('Hotkeys+Tricks')
                                                                       ,_('Hints')
                                                                       ,_('Tree types')]        ,val=page       ))
#                                       ,t=5,h=580  ,a='lRtB'   ,items='Hotkeys+Tricks\tHints\tTree types'      ,val=page       ))
                ,('keys',dict(tp='me'   ,p='tabs.0' ,ali=ALI_CL ,ro_mono_brd='1,1,1'            ,val=KEYS_TABLE ))
                ,('tips',dict(tp='me'   ,p='tabs.1' ,ali=ALI_CL ,ro_mono_brd='1,1,1'            ,val=TIPS_BODY  ))
#               ,('porg',dict(tp='llb'  ,p='tabs.1' ,ali=ALI_BT ,cap=_('Reg.ex. on python.org') ,url=RE_DOC_URL ))
                ,('tree',dict(tp='me'   ,p='tabs.2' ,ali=ALI_CL ,ro_mono_brd='1,1,1'            ,val=TREE_BODY  ))
                ,('porg',dict(tp='llb'  ,p='tabs.1' ,ali=ALI_BT ,cap=_('Plugin forum')          ,url=GH_ISU_URL ))
                    ][1:]
            , fid   = 'tabs'
                               #,options={'gen_repro_to_file':'repro_dlg_fif_help.py'}
        )
    def do_exit(ag):
        pass
#       page = 0 if ag.cattr('keys', 'vis') else 1 if ag.cattr('tips', 'vis') else 2
        page = ag.cval('tabs')
        stores['page']  = page
    try:
        ag_hlp.show(callbk_on_exit=lambda ag: do_exit(ag))    #NOTE: dlg_fif_help
    except:pass
    return stores
   #def dlg_fif_help

def dlg_nav_by_dclick():
    pass;                      #LOG and log('ok',())
    dcls    = Command.get_dcls()
    godef   = apx.get_opt('mouse_goto_definition', 'a')
    hint    = _('See "mouse_goto_definition" in default.json and user.json')
    acts_l  = [_("<no action>")
              ,_('Navigate to same group')
              ,_('Navigate to next group')
              ,_('Navigate to prev group')
              ,_('Navigate to next group, activate')
              ,_('Navigate to prev group, activate')
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
    pass;                      #LOG and log('vals={}',vals)
    if aid is None or aid=='-': return
    for nnn in ('nnn', 'snn', 'ncn', 'scn', 'nna', 'sna', 'nca', 'sca'):
        sca = nnn.replace('n', '')
        if 0==vals[nnn]:
            dcls.pop(sca, None)
        else:
            dcls[sca]   = sgns_l[vals[nnn]]
    Command.dcls    = dcls
    stores  = json.loads(re.sub(r',\s*}', r'}', open(CFG_PATH).read()), object_pairs_hook=odict) \
                if os.path.exists(CFG_PATH) and os.path.getsize(CFG_PATH) != 0 else \
              odict()
    stores['dcls']  = dcls
    open(CFG_PATH, 'w').write(json.dumps(stores, indent=4))
   #def dlg_nav_by_dclick

mask_h  = _('Space-separated file or folder masks.'
            '\nFolder mask starts with "/".'
            '\nDouble-quote mask, which needs space-char.'
            '\nUse ? for any character and * for any fragment.'
            '\nNote: "*" matchs all names, "*.*" doesnt match all.')
excl_h  = mask_h+f(_(''
            '\n '
            '\nAlways excluded: {}'
            '\nSee option "fif_always_not_in_files" to change.'
            ), ALWAYS_EXCL)
reex_h  = _('Regular expression'
            '\nFormat for found groups in Replace: \\1'
            )
case_h  = _('Case sensitive')
word_h  = _('Option "Whole words". It is ignored when:'
            '\n  Regular expression (".*") is turned on,'
            '\n  "Find what" contains not only letters, digits and "_".'
            )
brow_h  = _('Choose folder.'
            '\nShift+Click or Ctrl+B - Choose file to find in it.'
            )
fold_h  = f(_('Start folder(s).'
            '\nSpace-separated folders.'
            '\nDouble-quote folder, which needs space-char.'
            '\n~ is user Home folder.'
            '\n$VAR or ${{VAR}} is environment variable.'
            '\n{} to search in tabs (in short <Tabs> or <t>).'
            '\n{} to search in project folders (in short <p>).'
            ), IN_OPEN_FILES, IN_PROJ_FOLDS)
dept_h  = _('Which subfolders will be searched.'
            '\nAlt+Y or Ctrl+Num0 - Apply "Only".'
            '\nAlt+! or Ctrl+Num1 - Apply "+1 level".'
            '\nAlt+L or Ctrl+Num9 - Apply "+All" subfolders.'
            )
cfld_h  = _('Use folder of current file.'
            '\nShift+Click or Ctrl+Shift+C - Prepare search in the current file.'
            '\nCtrl+Click   - Prepare search in all tabs.'
            '\nShift+Ctrl+Click - Prepare search in the current tab.'
            )
mofi_h  = _('Advanced search options')
send_h  = _('Output report to tab/file')
morp_h  = _('Advanced tab report options')
menu_h  = _('Local menu'
            '\nCtrl+Click - Adjust vertical alignments...'
            )
#more_h  = _('Show/Hide advanced options'
#           '\nCtrl+Click   - Show/Hide "Not in files".'
#           '\nShift+Click - Show/Hide "Replace".'
#           '\n '
#           '\nAlt+V - Toggle visibility on cycle'
#           '\n   hidden "Not in files", hidden  "Replace"'
#           '\n   visible  "Not in files", hidden  "Replace"'
#           '\n   visible  "Not in files", visible   "Replace"'
#           '\n   hidden "Not in files", visible   "Replace"'
#           )
frst_h  = _('M[, F]'
            '\nStop after M fragments will be found.'
            '\nSearch only inside F first proper files.'
            '\n    Note: If Sort is on then steps are'
            '\n     - Collect all proper files'
            '\n     - Sort the list'
            '\n     - Use first F files to search'
            )
OLDE_U0 = ['h', 'd', 'w', 'm', 'y']
OLDE_U  = [_('hour(s)'), _('day(s)'), _('week(s)'), _('month(s)'), _('year(s)')]
olde_h  = _('"N" or "<N" or ">N".'
            '\nSkip files if the age less or more then N.'
            '\n"N" and "<N" are equal.'
            '\n"0" to all ages.'
            )
shtp_h  = f(_(  'Format of the reported tree structure.'
            '\nCompact - report all found line with full file info:'
            '\n    path(r[:c:l]):line'
            '\n    path/(r[:c:l]):line'
            '\n  Tree schemes'
            '\n    +Search for "*"'
            '\n      <full_path(row[:col:len])>: line with ALL marked fragments'
            '\n    +Search for "*"'
            '\n      <full_path>: #count'
            '\n         <(row[:col:len])>: line with ALL marked fragments'
            '\nSparse - report separated folders and fragments:'
            '\n    dir/file(r[:c:l]):line'
            '\n    dir/file/(r[:c:l]):line'
            '\n  Tree schemes'
            '\n    +Search for "*"'
            '\n      <root>: #count'
            '\n        <dir>: #count'
            '\n          <file.ext(row[:col:len])>: line with ONE marked fragment'
            '\n    +Search for "*"'
            '\n      <root>: #count'
            '\n        <dir>: #count'
            '\n          <file.ext>: #count'
            '\n            <(row[:col:len])>: line with ONE marked fragment'
            '\nFor '
            '\n  sorted files'
            '\nand for search in tabs'
            '\n  In folder={}'
            '\nonly Compact options are used.'
            '\nWhen a conflict occurs, "Tree type" is automatically changed.'
           ),IN_OPEN_FILES)
#NOTE: hints
cntx_c  = _('Conte&xt -{}+{}')
cntx_h  = _('Show result line and both its nearest lines, above and below result.')
algn_h  = _("Align columns (filenames/numbers) by widest cell width")
find_h  = f(_('Start search.'
            '\nShift+Click  - Put report to new tab.'
            '\n   It is like pressing Find with option "Show in: {}".'
            '\nCtrl+Click  - Append result to existing report.'
            '\n   It is like pressing Find with option "[x]Append results".'
            ), TOTB_NEW_TAB)
repl_h  = _('Start search and replacement.'
            '\nShift+Click  - Run without question'
            '\n   "Do you want to replace...?"'
            )
coun_h  = _('Count matches only.'
            '\nShift+Click or Ctrl+T - Find file names only.'
            '\n '
            '\nNote: Alt+T and Ctrl+T works if button is hidden.'
            )
pset_h  = _('Save options for future. Restore saved options.'
            '\nShift+Click - Show presets list in applying history order.'
            '\nCtrl+Click   - Apply last used preset.'
            '\n '
            '\nNote: Alt+S works if button is hidden.'
            '\nCtrl+1 - Apply first preset.'
            '\nCtrl+2 - Apply second preset.'
            '\nCtrl+3 - Apply third preset.'
            )
    
enco_h  = f(_('In which encodings try to read files.'
            '\nFirst suitable will be used.'
            '\n"{}" is slow.'
            '\n '
            '\nDefault encoding: {}'), ENCO_DETD, loc_enco)

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
    
def dlg_fif(what='', opts={}):
    return FifD(what, opts).show()

def prefix_to_sep_stores(def_prefix=''):
    sprd_res    = get_opt('fif_sep_hist_for_sess_proj', [])
    sess_path   = app.app_path(app.APP_FILE_SESSION)
    pass;                      #log('sprd_res={}',(sprd_res))
    pass;                      #log('sess_path={}',(sess_path))
    proj_path   = ''
    try:
        import cuda_project_man
        proj_vars   = cuda_project_man.project_variables()
        pass;                  #log('global_project_info={}',(cuda_project_man.global_project_info))
        pass;                  #log('proj_vars={}',(proj_vars))
        proj_path   = proj_vars.get('ProjMainFile', '')
    except:pass
    pass;                      #log('proj_path={}',(proj_path))
    for sprd_re in sprd_res:
        if re.search(sprd_re, sess_path) or re.search(sprd_re, proj_path):
            pass;              #log('prefix={}',(sprd_re+':'))
            return sprd_re+':'
    pass;                      #log('prefix={}',(def_prefix))
    return def_prefix
   #def prefix_to_sep_stores

class FifD:
    status_s  = ''
    
#   @staticmethod
#   def scam_pair(aid):
#       scam        = app.app_proc(app.PROC_GET_KEYSTATE, '')
#       return aid, scam + '/' + aid if scam and scam!='a' else aid   # smth == a/smth

    @staticmethod
    def upgrade(dct):
        if 'totb' in dct and type(dct['totb'])==str:
            dct['totb']  = int(dct['totb']) if re.match(r'^\d+$', dct['totb']) else 0

    @staticmethod
    def get_totb_l(fxs):
        tofx_l      = [f('file:{1}'+' '*100+'{0}'
                        , *os.path.split(fx)) 
                      for fx in fxs if os.path.isfile(fx) ]    # ' '*100 to hide folder in list-/combo-boxes
        return        TOTB_L                    \
                    + [_('[Clear fixed files]')
                      ,_('[Add fixed file]')]   \
                    + tofx_l                    \
                    + get_live_fiftabs(fxs)

    WIN_MAC     = (get_desktop_environment() in ('win', 'mac'))
    EG0,EG1,EG2,EG3,EG4,EG5,EG6,EG7,EG8,EG9,EG10 = [0]*11 if WIN_MAC else [5*i for i in range(11)]
    DLG_W0,     \
    DLG_H0      = (700, 140)
    DEF_WD_TXTS = 330
    DEF_WD_BTNS = 110

    TXT_W       = DEF_WD_TXTS
    BTN_W       = DEF_WD_BTNS
    LBL_L       = GAP+38*3+GAP#+25
    CMB_L       = LBL_L+100
    TL2_L       = LBL_L+250-85
    TBN_L       = CMB_L+TXT_W+GAP
    
    RSLT_W      = 300       # Min width of 'rslt'
    RSLT_H      =  60       # Min heght of 'rslt'
    SRCF_W      = 300       # Min width of 'srcf'
    SRCF_H      = 100       # Min heght of 'srcf'

    DEF_RSLT_BODY   = _('(no results)')
    rslt_body   = DEF_RSLT_BODY
    rslt_body_r = -1
    def show(self):
        M,m     = self.__class__,self

        self.hip= prefix_to_sep_stores()
        self.pre_cnts()
        self.ag = DlgAgent(
            form =dict(cap     = f(_('Find in Files ({})'), VERSION_V)
                      ,resize  = True
                      ,w       = self.dlg_w
                      ,h       = self.dlg_h     ,h_max=self.dlg_h if '1'==self.send_s else 0
                      ,on_show       = lambda idd, idc, data: m.do_resize(m.ag)
                      ,on_resize     = m.do_resize
                      ,on_key_down   = m.do_key_down
                      ,on_close_query= lambda idd, idc, data: not self.is_working_stop()
                      )
        ,   ctrls=self.get_fif_cnts()
        ,   vals =self.get_fif_vals()
        ,   fid  ='what'
        ,   options = {'bindof':self
                               ,'gen_repro_to_file':get_opt('fif_repro_to_file', '')    #NOTE: fif_repro
                              #,'gen_repro_to_file':'repro_dlg_fif.py'
                   #,   'ctrl_to_meta':'need'                       # 'by_os' is default
                    }
        )
        self.rslt = app.Editor(self.ag.handle('rslt'))              #NOTE: app.Editor
        self.rslt.set_prop(app.PROP_GUTTER_ALL          , True)
        self.rslt.set_prop(app.PROP_GUTTER_NUM          , False)
        self.rslt.set_prop(app.PROP_GUTTER_STATES       , False)
        self.rslt.set_prop(app.PROP_GUTTER_FOLD         , True)
        self.rslt.set_prop(app.PROP_GUTTER_BM           , False)
        self.rslt.set_prop(app.PROP_MINIMAP             , False)
        self.rslt.set_prop(app.PROP_MICROMAP            , False)
        self.rslt.set_prop(app.PROP_LAST_LINE_ON_TOP    , False)
        self.rslt.set_prop(app.PROP_MARGIN              , 2000)
        self.rslt.set_prop(app.PROP_LEXER_FILE          , FIF_LEXER)  ##!!
        self.rslt.set_prop(app.PROP_TAB_SIZE            , 1)
        self.rslt.set_text_all(M.DEF_RSLT_BODY)
        self.rslt.set_prop(app.PROP_RO                  , True)
        
        self.srcf = app.Editor(self.ag.handle('srcf'))
        self.srcf.set_prop(app.PROP_GUTTER_ALL          , False)
        self.srcf.set_prop(app.PROP_MINIMAP             , False)
        self.srcf.set_prop(app.PROP_MICROMAP            , False)
        self.srcf.set_prop(app.PROP_LAST_LINE_ON_TOP    , False)
        self.srcf.set_prop(app.PROP_MARGIN              , 2000)
        self.srcf.set_prop(app.PROP_GUTTER_ALL          , True)
        self.srcf.set_prop(app.PROP_GUTTER_NUM          , True)
        self.srcf.set_prop(app.PROP_GUTTER_STATES       , False)
        self.srcf.set_prop(app.PROP_GUTTER_FOLD         , False)
        self.srcf.set_prop(app.PROP_GUTTER_BM           , False)
        self.srcf_acts('set-no-src')

        statusbar   = self.ag.handle('stbr')
        app.statusbar_proc(statusbar, app.STATUSBAR_ADD_CELL            , tag=1)
        app.statusbar_proc(statusbar, app.STATUSBAR_SET_CELL_AUTOSTRETCH, tag=1, value=True)
        use_statusbar(statusbar)
        self.upd_def_status(True)
        pass;                  #msg_status('ok')
        if '0'==self.send_s and self.ag.cval('what') and self.ag.cval('fold')==IN_OPEN_FILES:
            # Run search at start
            self.do_work('!fnd', self.ag)
            self.ag.update(focused='rslt')
        elif '0'==self.send_s and M.rslt_body:
            self.rslt.set_prop(app.PROP_RO                  , False)
            self.rslt.set_text_all(M.rslt_body)
#           if -1!=M.rslt_body_r:
#               self.rslt.set_caret(0, M.rslt_body_r) 
#               self.do_rslt_click('rslt', self.ag)
            self.rslt.set_prop(app.PROP_RO                  , True)
        self.ag.show(callbk_on_exit=lambda ag: self.do_exit('', ag))
        self.store()
        pass;                  #Tr.tr=None if Tr.to_file else Tr.tr # Free log file
       #def show

    def __init__(self, what='', opts={}):
        M,m     = self.__class__,self
        pass
        pass;                  #LOG and log('FifD.DEF_WD_TXTS={}',(FifD.DEF_WD_TXTS))
        self.store(what='load')
        FifD.upgrade(self.stores)     # Upgrade types

        self.hip    = prefix_to_sep_stores()        # HIstory Prefix. To store separated history for some sessions
        hp          = self.hip
    
        self.what_s  = what if what else ed.get_text_sel() if USE_SEL_ON_START else ''
        self.what_s  = self.what_s.splitlines()[0] if self.what_s else ''
        self.repl_s  = opts.get('repl', '')
        self.reex01  = opts.get('reex', self.stores.get('reex', '0'))
        self.case01  = opts.get('case', self.stores.get('case', '0'))
        self.word01  = opts.get('word', self.stores.get('word', '0'))
        if USE_EDFIND_OPS:
            if app.app_api_version()>='1.0.248':
                fpr     = app.app_proc(app.PROC_GET_FINDER_PROP, '')
                self.reex01  = '1' if ('op_regex_d' in fpr and fpr['op_regex_d'] or fpr['op_regex']) else '0'
                self.case01  = '1' if ('op_case_d'  in fpr and fpr['op_case_d']  or fpr['op_case'] ) else '0'
                self.word01  = '1' if ('op_word_d'  in fpr and fpr['op_word_d']  or fpr['op_word'] ) else '0'
            else:
                ed_opt  = app.app_proc(app.PROC_GET_FIND_OPTIONS, '')   # Deprecated
                # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrap
                self.reex01  = '1' if 'r' in ed_opt else '0'
                self.case01  = '1' if 'c' in ed_opt else '0'
                self.word01  = '1' if 'w' in ed_opt else '0'
        self.incl_s  = opts.get('incl', self.stores.get(hp+'incl',  [''])[0])
        self.excl_s  = opts.get('excl', self.stores.get(hp+'excl',  [''])[0])
        self.fold_s  = opts.get('fold', self.stores.get(hp+'fold',  [''])[0])
        self.dept_n  = opts.get('dept', self.stores.get('dept',  0)-1)+1
        self.send_s  = opts.get('send', self.stores.get('send', '0'))
        self.join_s  = opts.get('join', self.stores.get('join', '0'))
        self.totb_i  = opts.get('totb', self.stores.get('totb',  0 ));  self.totb_i =  1  if self.totb_i== 0  else self.totb_i
        self.shtp_s  = opts.get('shtp', self.stores.get('shtp', '0'))
        self.cntx_s  = opts.get('cntx', self.stores.get('cntx', '0'))
        nBf     = get_opt('fif_context_width_before', get_opt('fif_context_width', 1))  # old storing in user.json
        nAf     = get_opt('fif_context_width_after' , get_opt('fif_context_width', 1))  # old storing in user.json
        self.cntx_b  = opts.get('cntb', self.stores.get('cntb', nBf))
        self.cntx_a  = opts.get('cnta', self.stores.get('cnta', nAf))
        pass;                  #log("self.cntx_b,self.cntx_a={}",(self.cntx_b,self.cntx_a))
        self.algn_s  = opts.get('algn', self.stores.get('algn', '0'))
        self.skip_s  = opts.get('skip', self.stores.get('skip', '0'))
        self.sort_s  = opts.get('sort', self.stores.get('sort', '0'))
        self.olde_s  = opts.get('olde', self.stores.get('olde', '0/d'))
        self.frst_s  = opts.get('frst', self.stores.get('frst', '0'));  self.frst_s  = '0' if not self.frst_s else self.frst_s
        self.enco_s  = opts.get('enco', self.stores.get('enco', '0'))

        self.wo_excl= self.stores.get('wo_excl', True)
        self.wo_repl= self.stores.get('wo_repl', True)

        self.rslt_va= self.stores.get('rslt_va', True)
        self.rslt_w = self.stores.get('rslt_w', M.RSLT_W)   if not self.rslt_va else M.RSLT_W
        self.rslt_h = self.stores.get('rslt_h', M.RSLT_H)   if     self.rslt_va else M.RSLT_H
        
        self.enc_srcf=self.stores.get('enc_srcf', '')

        self.caps    = None     # Will be filled in get_fif_cnts

        self.what_l  = None     # Will be filled in pre_cnts
        self.incl_l  = None     # Will be filled in pre_cnts
        self.excl_l  = None     # Will be filled in pre_cnts
        self.fold_l  = None     # Will be filled in pre_cnts
        self.repl_l  = None     # Will be filled in pre_cnts
        self.totb_l  = None     # Will be filled in pre_cnts
        self.gap1    = None     # Will be filled in pre_cnts
        self.gap2    = None     # Will be filled in pre_cnts
        self.dlg_w   = None     # Will be filled in pre_cnts
        self.dlg_h   = None     # Will be filled in pre_cnts

        self.ag         = None
        self.progressor = None  # For lock dlg-hiding while search
        self.locked_cids= None  # Locked controls while working
       #def __init__
    
    def do_resize(self, ag):
        pass;                  #return []
        M,m     = self.__class__,self
        def fix_wh(hw_c, hw_min):
            pbot_v  = ag.cattr('pb'  , hw_c)
            rslt_v  = ag.cattr('rslt', hw_c)
            sptr_v  = ag.cattr('sptr', hw_c)
            srcf_v  = ag.cattr('srcf', hw_c)
            rslt_v_n= hw_min \
                        if  rslt_v                  >= pbot_v else \
                      hw_min \
                        if (rslt_v+sptr_v+hw_min)   >= pbot_v else \
                      rslt_v
            pass;              #log('###pbot_v, srcf_v, rslt_v, rslt_v_n={}',(pbot_v, srcf_v, rslt_v, rslt_v_n))
            pass;              #return []
            if rslt_v==rslt_v_n:    # no hidden
                return []
            return d(ctrls=[('rslt',{hw_c:rslt_v_n})])
           #def fix_wh
        return fix_wh('h', M.RSLT_H) if m.rslt_va else \
               fix_wh('w', M.RSLT_W)
       #def do_resize
    
    def is_working_stop(self):
        pass;                  #log('?? is_working_stop={}',(self.progressor))
        if self.progressor:
            self.progressor.will_break = True
        return bool(self.progressor)
       #def is_working_stop
    
    def copy_vals(self, ag):
        self.reex01     = ag.cval('reex')
        self.case01     = ag.cval('case')
        self.word01     = ag.cval('word')
        self.what_s     = ag.cval('what')
        self.incl_s     = ag.cval('incl')
        self.excl_s     = ag.cval('excl') if not self.wo_excl else ''
        self.fold_s     = ag.cval('fold')
        self.dept_n     = ag.cval('dept')
        self.repl_s     = ag.cval('repl') if not self.wo_repl else self.repl_s
        self.send_s     = ag.cval('send')
        if '0'==self.send_s:
            self.rslt_w = ag.cattr('rslt', 'w') if not self.rslt_va else self.rslt_w
            self.rslt_h = ag.cattr('rslt', 'h') if     self.rslt_va else self.rslt_h
       #def copy_vals
    
    def store(self, what='save'):#, set=''):
        if what=='load':
            self.stores = json.loads(re.sub(r',\s*}', r'}', open(CFG_PATH).read()), object_pairs_hook=odict) \
                            if os.path.exists(CFG_PATH) and os.path.getsize(CFG_PATH) != 0 else \
                           odict()
        if what=='save':
            hp  = self.hip
            self.stores['wo_excl']  = self.wo_excl
            self.stores['wo_repl']  = self.wo_repl
            self.stores['reex']     = self.reex01
            self.stores['case']     = self.case01
            self.stores['word']     = self.word01
            self.stores[hp+'what']  = add_to_history(self.what_s, self.stores.get(hp+'what', []), MAX_HIST, unicase=False)
            self.stores[hp+'incl']  = add_to_history(self.incl_s, self.stores.get(hp+'incl', []), MAX_HIST, unicase=(os.name=='nt'))
            self.stores[hp+'excl']  = add_to_history(self.excl_s, self.stores.get(hp+'excl', []), MAX_HIST, unicase=(os.name=='nt'))
            self.stores[hp+'fold']  = add_to_history(self.fold_s, self.stores.get(hp+'fold', []), MAX_HIST, unicase=(os.name=='nt'))
            self.stores[hp+'repl']  = add_to_history(self.repl_s, self.stores.get(hp+'repl', []), MAX_HIST, unicase=False)
            self.stores['dept']     = self.dept_n
            self.stores['send']     = self.send_s
            self.stores['join']     = self.join_s
            self.stores['totb']     = 1 if self.totb_i==0 else self.totb_i
            self.stores['shtp']     = self.shtp_s
            self.stores['cntx']     = self.cntx_s
            self.stores['cntb']     = self.cntx_b
            self.stores['cnta']     = self.cntx_a
            self.stores['algn']     = self.algn_s
            self.stores['skip']     = self.skip_s
            self.stores['sort']     = self.sort_s
            self.stores['olde']     = self.olde_s
            self.stores['frst']     = self.frst_s
            self.stores['enco']     = self.enco_s
            self.stores['rslt_va']  = self.rslt_va
            self.stores['rslt_w']   = self.rslt_w
            self.stores['rslt_h']   = self.rslt_h
            open(CFG_PATH, 'w').write(json.dumps(self.stores, indent=4))
       #def store
    
    def upd_def_status(self, do_out=False):
        info_fi     = []
        info_fi    += [(SKIP_L[int(self.skip_s)]    )]  if self.skip_s!='0' else []
        info_fi    += [(_('sorted')                 )]  if self.sort_s!='0' else []
        age         = ('<'+self.olde_s).replace('<<', '<').replace('<>', '>').replace('/', '')
        info_fi    += [(_('age')+age)]                  if age[1]!='0'      else []
        info_fi    += [(_('first "')+self.frst_s+'"')]  if self.frst_s!='0' else []
            
        info_rp     = []
        if '1'==self.send_s:
            s100    = ' '*100       # See get_totb_l
            totb_it = self.totb_l[self.totb_i]
            totb_it = totb_it if totb_it[0]=='<'    else '"'+re.search(r'file:(.+)'+s100, totb_it).group(1)+'"'
            totb_it = totb_it if self.join_s!='1'   else _('append to ')+totb_it
            info_rp+= [(_('Report: ')+totb_it       )]  
            info_rp+= [(SHTP_L[int(self.shtp_s)]    )]  
            info_rp+= [(_('aligned')                )]  if self.algn_s=='1' else []
            info_rp+= [(f(_('context-{}+{}'), self.cntx_b, self.cntx_a)
                                                    )]  if self.cntx_s=='1' else []
        
        cap_fi  = (_('Search: ') + ', '.join(info_fi)) if info_fi else ''
        cap_rp  =                  ', '.join(info_rp)  if info_rp else ''
        self.status_s   = '; '.join([cap_fi, cap_rp]).strip('; ') if cap_fi or cap_rp else ''
        msg_status(self.status_s) if do_out else 0
       #def upd_def_status

    def do_focus(self,aid,ag, store=True):
        self.store() if store else None
        aid_ed  = ag.cattr(aid, 'type') in ('edit', 'combo') if aid[0]!='!' else False
        fid     = ag.fattr('focused')
        fid_ed  = ag.cattr(fid, 'type') in ('edit', 'combo') if fid else None
        fid     = aid    if aid_ed                                  else \
                  fid    if fid_ed                                  else \
                  'what' if aid in ('brow', 'cfld')                 else \
                  'what'
        return {'fid':fid}
       #def do_focus
    
    def do_pres(self, aid, ag, btn_m=''):
        msg_status(self.status_s)
#       btn_p,btn_m = FifD.scam_pair(aid)       if not btn_m else   (aid, btn_m)
        btn_p,btn_m = ag.scam_pair(aid)         if not btn_m else   (aid, btn_m)
        
        self.what_s = ag.cval('what')
        if not self.wo_repl:     
            self.repl_s = ag.cval('repl')
        
        if btn_p == 'save':
            PresetD(self).save()
        if btn_p == 'conf':
            PresetD(self).config()
        if btn_p in ('prs1', 'prs2', 'prs3', 'prs4', 'prs5'):
            PresetD(self).ind4rest(int(btn_p[3])-1)

#       self.store() # in do_focus
        return (dict(vals=self.get_fif_vals()
                    )
               ,self.do_focus('what',ag)
               )
       #def do_pres

    def do_fold(self, aid, ag, btn_m=''):
        msg_status(self.status_s)
        self.copy_vals(ag)
#       ag.bind_do()
#       ag.bind_do(['excl','fold','dept'])
#       btn_p,btn_m = FifD.scam_pair(aid)       if not btn_m else   (aid, btn_m)
        btn_p,btn_m = ag.scam_pair(aid)         if not btn_m else   (aid, btn_m)

        if False:pass
        elif btn_m=='brow':     # BroDir
            path        = app.dlg_dir(os.path.expanduser(self.fold_s))
            if not path: return self.do_focus(aid,ag)   #continue#while_fif
            self.fold_s = path
            self.fold_s = self.fold_s.replace(os.path.expanduser('~'), '~', 1)      \
                            if self.fold_s.startswith(os.path.expanduser('~')) else \
                          self.fold_s
            self.fold_s = '"'+self.fold_s+'"' if ' ' in self.fold_s else self.fold_s;
#           self.focused= 'fold'
        elif btn_m=='s/brow':   # [Shift+]BroDir = BroFile
            fn          = app.dlg_file(True, '', os.path.expanduser(self.fold_s), '')
            if not fn or not os.path.isfile(fn):    return self.do_focus(aid,ag)   #continue#while_fif
            self.incl_s = os.path.basename(fn)
            self.fold_s = os.path.dirname(fn)
            self.fold_s = self.fold_s.replace(os.path.expanduser('~'), '~', 1)      \
                            if self.fold_s.startswith(os.path.expanduser('~')) else \
                          self.fold_s
            self.fold_s = '"'+self.fold_s+'"' if ' ' in self.fold_s else self.fold_s;
            self.dept_n = 1
        elif btn_m=='cfld' and ed.get_filename():
            self.fold_s = os.path.dirname(ed.get_filename())
            self.fold_s = self.fold_s.replace(os.path.expanduser('~'), '~', 1)      \
                            if self.fold_s.startswith(os.path.expanduser('~')) else \
                          self.fold_s
            self.fold_s = '"'+self.fold_s+'"' if ' ' in self.fold_s else self.fold_s;
        elif btn_m=='s/cfld':   # [Shift+]CurDir = CurFile
            if not os.path.isfile(     ed.get_filename()):   return self.do_focus(aid,ag)   #continue#while_fif
            self.incl_s = os.path.basename(ed.get_filename())
            self.fold_s = os.path.dirname( ed.get_filename())
            self.fold_s = self.fold_s.replace(os.path.expanduser('~'), '~', 1)      \
                            if self.fold_s.startswith(os.path.expanduser('~')) else \
                          self.fold_s
            self.fold_s = '"'+self.fold_s+'"' if ' ' in self.fold_s else self.fold_s;
            self.dept_n = 1
            self.excl_s = ''
        elif btn_m=='c/cfld':   # [Ctrl+]CurDir  = InTabs
            self.incl_s = '*'
            self.fold_s = IN_OPEN_FILES
        elif btn_m=='sc/cfld':  # [Ctrl+Shift+]CurDir = CurTab
            self.incl_s = ed.get_prop(app.PROP_TAB_TITLE)   ##!! need tab-id?
            self.fold_s = IN_OPEN_FILES
            self.excl_s = ''

#       self.store() # in do_focus
        return (dict(vals=self.get_fif_vals())
               ,self.do_focus(aid,ag)
               )
       #def do_fold
       
    def do_dept(self, aid, ag, data=''):
        msg_status(self.status_s)
        pass;                  #LOG and log('self.dept_n={}',(repr(self.dept_n)))
        self.copy_vals(ag)
#       ag.bind_do(['dept'])
        self.dept_n = 0 if aid=='depa' else \
                      1 if aid=='depo' else \
                      2 if aid=='dep1' else \
                      self.dept_n
        pass;                  #LOG and log('self.dept_n={}',(repr(self.dept_n)))
#       self.store() # in do_focus
        return (dict(vals={'dept':self.dept_n})
               ,self.do_focus(aid,ag)
               )
       #def do_dept
    
    def do_mofi(self, aid, ag, data=''):
        msg_status(self.status_s)
        pass;                  #log('self.skip_s={}',(self.skip_s))
        olde_n, \
        olde_u  = self.olde_s.split('/')
        olde_ui = {U[0]:i for i,U in enumerate(OLDE_U0)}[olde_u]
        ag_mofi = DlgAgent(form   =dict(cap=mofi_h, w=340, h=120+33+30)                                     #NOTE: ag_mofi Search opts
                ,ctrls  =[0
                ,('ski_',d(tp='lb'  ,tid='skip' ,l=5    ,w=120-5,cap='>'+_('S&kip files:')                  ))# &k
                ,('skip',d(tp='cb-r',t=5        ,l=5+120,w=200  ,items=SKIP_L                               ))# 
                ,('sor_',d(tp='lb'  ,tid='sort' ,l=5    ,w=120-5,cap='>'+_('S&ort file list:')              ))# &o
                ,('sort',d(tp='cb-r',t=5+29*1   ,l=5+120,w=200  ,items=SORT_L                               ))# 
                ,('old_',d(tp='lb'  ,tid='olde' ,l=5    ,w=120-5,cap='>'+_('A&ge (0=all):')     ,hint=olde_h))# &g
                ,('olde',d(tp='ed'  ,t=5+29*2   ,l=5+120,w= 75                                              ))# 
                ,('oldu',d(tp='cb-r',tid='olde' ,l=5+200,w=120  ,items=OLDE_U                               ))# 
                ,('frs_',d(tp='lb'  ,tid='frst' ,l=5    ,w=120-5,cap='>'+_('&Firsts (0=all):')   ,hint=frst_h))# &f
                ,('frst',d(tp='ed'  ,t=5+29*3   ,l=5+120,w=200                                              ))# 
                ,('enc_',d(tp='lb'  ,tid='enco' ,l=5    ,w=120-5,cap='>'+_('&Encodings:')       ,hint=enco_h))# &e
                ,('enco',d(tp='cb-r',t=5+29*4   ,l=5+120,w=200  ,items=ENCO_L                               ))# 
                ,('okok',d(tp='bt'  ,t=150      ,l=260  ,w= 65  ,cap='OK'   ,def_bt=True    ,call=LMBD_HIDE ))# 
                        ][1:]
                ,vals   = d(skip=self.skip_s
                           ,sort=self.sort_s
                           ,olde=olde_n
                           ,oldu=olde_ui
                           ,frst=self.frst_s
                           ,enco=self.enco_s
                           )
                ,fid    = self.stores.get('mofi.fid', 'skip')
                              #,options={'gen_repro_to_file':'repro_dlg_pres.py'}
        )
        ag_mofi.show(callbk_on_exit=lambda ag: self.stores.update({'mofi.fid':ag.fattr('fid')}))
        age         = ag_mofi.cval('olde').strip()
        age         = age if re.match('[<>]?\d+$', age) else '0' 
        self.skip_s = ag_mofi.cval('skip')
        self.sort_s = ag_mofi.cval('sort')
        self.olde_s = age+'/'+OLDE_U0[ag_mofi.cval('oldu')][0]
        self.frst_s = ag_mofi.cval('frst').strip()
        self.enco_s = ag_mofi.cval('enco')
        pass;                  #log('self.skip_s={}',(self.skip_s))
        self.upd_def_status(True)
        return []
       #def do_mofi
    
    def do_morp(self, aid, ag, data=''):
        msg_status(self.status_s)
        M,m     = self.__class__,self
        
        def do_totb(aid, ag, data=''):
            pass;              #LOG and log('totb props={}',(ag.cattrs('totb')))
            self.totb_i = ag.cval('totb')
            pass;              #log('totb_i={}',(self.totb_i))
            totb_i_pre  = self.totb_i
    #       self.copy_vals(self.ag)
            totb_v      = self.totb_l[self.totb_i]
            pass;               LOG and log('totb_i_pre,totb_i,totb_v={}',(totb_i_pre,self.totb_i,totb_v))
            fxs         = self.stores.get('tofx', [])
            if False:pass
            elif totb_v==_('[Clear fixed files]') and fxs:
                if app.ID_YES != app.msg_box(
                                  f(_('Clear all fixed files ({}) for "{}"?'), len(fxs), _('Report to'))
                                , app.MB_OKCANCEL+app.MB_ICONQUESTION):
                    self.totb_i  = totb_i_pre
                    return {'vals':{'totb':self.totb_i}}            # Cancel, set prev state
                self.stores['tofx']  = []
                self.totb_i  = 1                                    # == TOTB_USED_TAB
            elif totb_v==_('[Clear fixed files]'): #  and not fxs
                self.totb_i  = 1                                    # == TOTB_USED_TAB
            elif totb_v==_('[Add fixed file]'):
                fx      = app.dlg_file(True, '', os.path.expanduser(self.fold_s), '')
                if not fx or not os.path.isfile(fx):
                    self.totb_i  = totb_i_pre
                    return {'vals':{'totb':self.totb_i}}            # Cancel, set prev state
                fxs     = self.stores.get('tofx', [])
                if fx in fxs:
                    self.totb_i  = 4+fxs.index(fx)
                else:
                    self.stores['tofx'] = fxs + [fx]
                    self.totb_i  = 4+len(self.stores['tofx'])-1     # skip: new,prev,clear,add,files-1
            else:
                return self.do_focus(aid,ag)
        
            self.totb_l = FifD.get_totb_l(self.stores.get('tofx', []))
            pass;                   LOG and log('self.totb_i={}',(self.totb_i))
            return d(ctrls=[0
                           ,('totb', d(val=self.totb_i  ,items=self.totb_l))
                           ][1:]
                   ) 
           #def do_totb

        self.copy_vals(ag)
        if aid=='send':
            if self.send_s=='1':
                self.do_morp('morp', ag)
            self.pre_cnts()
            send_b  = '1'==self.send_s
            self.upd_def_status(True)
            self.pre_cnts() 
            return d(ctrls=self.get_fif_cnts('vis+pos')
                     ,form=d(h    =self.dlg_h
                            ,h_max=self.dlg_h if send_b else 0
                            )
                    ,fid='what')
        
        ag_morp = DlgAgent(form   =dict(cap=morp_h, w=330, h=205)                                                   #NOTE: ag_morp Report opts
                ,ctrls  =[0
                ,('tot_',d(tp='lb'  ,t=  5      ,l=  5  ,w=100  ,cap=_('&Report to:')                               ))# &r
                ,('totb',d(tp='cb-r',t= 23      ,l=  5  ,w=140  ,items=m.totb_l                     ,call=do_totb   ))# 
                ,('join',d(tp='ch'  ,tid='totb' ,l=170  ,w=140  ,cap=_('Appen&d results')                           ))# &d
                ,('sht_',d(tp='lb'  ,t= 60      ,l=  5  ,w=100  ,cap=_('&Tree type:')       ,hint=shtp_h            ))# &t
                ,('shtp',d(tp='cb-r',t= 78      ,l=  5  ,w=140  ,items=SHTP_L                                       ))# 
                ,('algn',d(tp='ch'  ,tid='shtp' ,l=170  ,w= 80  ,cap=_('&Align (r:c:l)')    ,hint=algn_h            ))# &a
                ,('cntx',d(tp='ch'  ,t=115      ,l=  5  ,w=140  ,cap=_('Add conte&xt lines'),hint=cntx_h            ))# &x
                ,('cxb_',d(tp='lb'  ,tid='cxbf' ,l=  5  ,w= 80  ,cap='>'+_('&Before:')                              ))# &b
                ,('cxbf',d(tp='sed' ,t=140      ,l=100  ,w= 45  ,min_max_inc='0,9,1'                                ))# 
                ,('cxa_',d(tp='lb'  ,tid='cxaf' ,l=  5  ,w= 80  ,cap='>'+_('A&fter:')                               ))# &f
                ,('cxaf',d(tp='sed' ,t=169      ,l=100  ,w= 45  ,min_max_inc='0,9,1'                                ))# 
                ,('okok',d(tp='bt'  ,tid='cxaf' ,l=260  ,w= 65  ,cap='OK'           ,def_bt=True    ,call=LMBD_HIDE ))# 
                        ][1:]
                ,vals   = d(totb=self.totb_i
                           ,join=self.join_s
                           ,shtp=self.shtp_s
                           ,algn=self.algn_s
                           ,cntx=self.cntx_s
                           ,cxbf=self.cntx_b
                           ,cxaf=self.cntx_a
                           )
                ,fid    = self.stores.get('morp.fid', 'totb')
                              #,options={'gen_repro_to_file':'repro_dlg_pres.py'}
        )
        ag_morp.show(callbk_on_exit=lambda ag: self.stores.update({'morp.fid':ag.fattr('fid')}))
        self.totb_i = ag_morp.cval('totb')
        self.join_s = ag_morp.cval('join')
        self.shtp_s = ag_morp.cval('shtp')
        self.cntx_s = ag_morp.cval('cntx')
        self.cntx_b = ag_morp.cval('cxbf')
        self.cntx_a = ag_morp.cval('cxaf')
        self.algn_s = ag_morp.cval('algn')
        ag.activate()
        self.upd_def_status(True)
        self.pre_cnts()
        return d(form=d(h_max=self.dlg_h if '1'==self.send_s else 0
                ))
       #def do_morp
    
    def do_more(self, aid, ag, data=''):
        msg_status(self.status_s)
        self.copy_vals(ag)
#       ag.bind_do()
#       ag.bind_do(['excl','repl','adva'])
#       btn_p,btn_m = FifD.scam_pair(aid)
        btn_p,btn_m = ag.scam_pair(aid)

        if False:pass

        elif btn_m=='c/more':     # [Ctrl+]More       = show/hide excl
            self.wo_excl    = not self.wo_excl
        elif btn_m=='s/more':     # [Shift+]More      = show/hide repl
            self.wo_repl    = not self.wo_repl

        elif btn_p=='loop':
            v_excl  = not self.wo_excl
            v_repl  = not self.wo_repl
            (v_excl,v_repl) = (T,F) if (v_excl,v_repl)==(F,F) else \
                              (T,T) if (v_excl,v_repl)==(T,F) else \
                              (F,T) if (v_excl,v_repl)==(T,T) else \
                              (F,F) if (v_excl,v_repl)==(F,T) else (v_excl,v_repl)
            self.wo_excl    = not v_excl
            self.wo_repl    = not v_repl
        else:
            return self.do_focus(aid,ag)
        
#       self.store() # in do_focus
        self.pre_cnts()
        pass;                  #LOG and log('dlg_h={}',(dlg_h))
        return (dict(form =dict(h    =self.dlg_h ,h_min=self.dlg_h     ,h_max=self.dlg_h if '1'==self.send_s else 0
                                )
                    ,vals =self.get_fif_vals()
                    ,ctrls=self.get_fif_cnts('vis+pos'))
               ,self.do_focus(aid,ag)
               )
       #def do_more

    def do_help(self, aid, ag, data=''):
        msg_status(self.status_s)

        self.stores['dlg.help.data'] = dlg_fif_help(self, self.stores.get('dlg.help.data'))

        open(CFG_PATH, 'w').write(json.dumps(self.stores, indent=4))
        ag.activate()
        return self.do_focus('what',ag)
       #def do_help
    
    def do_exit(self, aid, ag, data=''):
#       scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        scam    = ag.scam()
        pass;                  #log('###aid,scam={}',(aid,scam))
        if self.progressor and 'c'!=scam:
            return False
#       ag.bind_do()
        self.copy_vals(ag)
        pass;                  #LOG and log('self.totb_i={}',(self.totb_i))
        self.store()
        use_statusbar(None)
        return None
       #def do_exit
    
    def do_menu_event(self, aid, ag, data=''):
        self.do_menu(aid, self.ag, data)
        return False
    
    encoding_detector   = UniversalDetector() 
    rslt_timer_cb       = None
    last_click_t        = 0
    SEL_TO_ACT_DELAY    = 0.200 # sec
    TIMER_DELAY         = 200   # msec
    def do_rslt_click(self, aid, ag, data='', timer=False):  #NOTE: do_rslt_click
        pass;                  #log('aid={}',(aid))
        M,m     = self.__class__,self

        now_t   = round(time.perf_counter(), 4)
        if not timer:
            # Direct call
            M.last_click_t  = now_t                         # time of user click
            if  M.rslt_timer_cb:
                return [] 
            M.rslt_timer_cb     = lambda tag: self.do_rslt_click(aid, ag, data, timer=True)
            app.timer_proc(app.TIMER_START, M.rslt_timer_cb, M.TIMER_DELAY)
            return []

        # Timer call
        pre_t   = M.last_click_t
        if  (now_t - pre_t) < M.SEL_TO_ACT_DELAY:           # too small pause after last user click
            return []                                       # wait next timer tick or user click
        assert M.rslt_timer_cb
        app.timer_proc(app.TIMER_DELETE, M.rslt_timer_cb, 0)
        M.rslt_timer_cb = None
        
        if aid=='rslt' and M.rslt_body!=M.DEF_RSLT_BODY:
            row     = self.rslt.get_carets()[0][1]
            M.rslt_body_r   = row
            path,rw,\
            cl, ln  = get_data4nav(self.rslt, row)
            lexer   = ''
            pass;              #log('row, path,rw,cl,ln={}',(row,path,rw, cl, ln))
            msg_status(path) if path else 0
            if not path:    return []
            if  self.srcf._loaded_file != path:
                self.srcf.set_prop(app.PROP_LEXER_FILE, '')
                self.srcf._loaded_file  = path
                text    = ''
                self.srcf.set_prop(app.PROP_RO, False)
                if path.startswith('tab:'):
                    tab_id  = int(path.split('/')[0].split(':')[1])
                    tab_ed  = apx.get_tab_by_id(tab_id)
                    text    = tab_ed.get_text_all()
                    lexer   = tab_ed.get_prop(app.PROP_LEXER_FILE)
                elif os.path.isfile(path):
                    text    = self.srcf_acts('load-body', par=path)
                    lexer   = app.lexer_proc(app.LEXER_DETECT, path)
                self.srcf.set_text_all(text) 
                self.srcf.set_prop(app.PROP_LEXER_FILE, lexer)
                self.srcf.set_prop(app.PROP_RO, True)
                pass;          #log('ok load path={}',(path))
            app.app_idle()                      # Hack to problem: PROP_LINE_TOP sometime skipped after set_prop(PROP_LEXER_FILE)
            self.srcf_acts('nav-to', par=(lexer, rw, cl, ln, -3))
#           nav_to_frag(self.srcf, rw, cl, ln, indent_vert=-3)
        return []
       #def do_rslt_click
    
    def srcf_acts(self, act, ag=None, par=None):
        M,m     = self.__class__,self
        
        if act=='nav-to':
            lexer, rw, cl, ln, indent_vert = par
            nav_to_frag(self.srcf, rw, cl, ln, indent_vert=indent_vert)
            return 
        
        if act=='show-enco':
            return  '<'+_('detect')+'>' \
                        if not self.enc_srcf else \
                    f('<{}>', ENCO_L[int(self.enco_s)]) \
                        if self.enc_srcf=='=' else \
                    self.enc_srcf
        
        if act=='ask-enco':
            encsNAC = ENCODINGS
            encsN   = [nm for nm,al,cm in encsNAC]
            enc_ind = encsN.index(self.enc_srcf)    if self.enc_srcf in encsN   else \
                      1+len(encsN)                  if self.enc_srcf=='='       else \
                        len(encsN)
#           enc_ind = encsN.index(self.enc_srcf) if self.enc_srcf in encsN else len(encsN)
            enc_ind = app.dlg_menu(app.MENU_LIST + MENU_CENTERED
                    ,   '\n'.join([f('{}\t{}', nm+(f(' ({}) ', al) if al!='' else ''),  cm)  
                                    for nm,al,cm in encsNAC] 
                                 +['<'+_('detect')+'>']
                                 +[f(_('<{}> (search setting)'), ENCO_L[int(self.enco_s)])])
                    ,   focused=enc_ind
                    ,   caption=_('Source encoding'))
            if enc_ind is None: return []
            if enc_ind == len(encsN):       # '<Detect>'
                self.enc_srcf = ''
            elif enc_ind == 1+len(encsN):   # '<As in searching>'
                self.enc_srcf = '='
            else:
                self.enc_srcf = encsN[enc_ind]
            self.stores['enc_srcf'] = self.enc_srcf
            return self.do_rslt_click(self, 'rslt', ag)
            
        if act=='load-body':
            path    = par
            encsN   = [nm for nm,al,cm in ENCODINGS]
            enc_l   = [self.enc_srcf]                       if self.enc_srcf in encsN   else \
                      ENCO_L[int(self.enco_s)].split(', ')  if self.enc_srcf=='='       else \
                      [ENCO_DETD]
            text    = ''
            for enc in enc_l:
                enc_    = detect_encoding(path, M.encoding_detector) if enc==ENCO_DETD else enc
                pass;          #log('enc,enc_={}',(enc,enc_))
                try:
                    text= open(path, encoding=enc_).read()
                    break#for
                except:
                    text= _('<ERROR. See "Source encoding" in menu>')
            return text

        if act=='set-no-src':
            self.srcf._loaded_file  = None
            self.srcf.set_prop(app.PROP_RO                  , False)
            self.srcf.set_text_all(_('(no source)'))
            self.srcf.set_prop(app.PROP_RO                  , True)
            self.srcf.set_prop(app.PROP_LEXER_FILE, '')
       #def srcf_acts
    
    def do_work(self, aid, ag, btn_m=''):
        M,m     = self.__class__,self
        msg_status(self.status_s)
#       ag.bind_do()
        self.copy_vals(ag)
#       self.store() # in do_focus
        
#       btn_p,btn_m = FifD.scam_pair(aid)       if not btn_m else   (aid, btn_m)
        btn_p,btn_m = ag.scam_pair(aid)         if not btn_m else   (aid, btn_m)
        btn_p,btn_m = btn_p.replace('!ctt', '!cnt'),btn_m.replace('!ctt', '!cnt')
        if btn_p not in ('!cnt', '!fnd', '!rep'):   return self.do_focus(aid,ag)
        pass;                  #log('btn_p,btn_m={}',(btn_p,btn_m))
        
        w_excl      = not self.wo_excl
        self.excl_s = self.excl_s if w_excl else ''

        w_rslt  = '0'==self.send_s
        
        if btn_m=='!rep' \
        and app.ID_OK != app.msg_box(
             f(_('Do you want to replace in {}?'), 
                _('current tab')        if root_is_tabs(self.fold_s) and not ('*' in self.incl_s or '?' in self.incl_s) else 
                _('all tabs')           if root_is_tabs(self.fold_s) else 
                _('all found files')
             )
            ,app.MB_OKCANCEL+app.MB_ICONQUESTION):
            return self.do_focus(aid,ag)

        w_repl      = not self.wo_repl
        self.repl_s = self.repl_s if w_repl else ''
        
        if 0 != self.fold_s.count('"')%2:
            msg_status(f(_('Fix quotes in the "{}" field'), self.caps['fold'])) 
            return {'fid':'fold'}
            
        if not self.what_s:
            msg_status( f(_('Fill the "{}" field'), self.caps['what']))
            return {'fid':'what'}
        
        if self.reex01=='1':
            try:
                re.compile(self.what_s)
            except Exception as ex:
                app.msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}')
                             , self.caps['what'], ex), app.MB_OK+app.MB_ICONWARNING) 
                return {'fid':'what'}
            if btn_p=='!rep':
                try:
                    re.sub(self.what_s, self.repl_s, '')
                except Exception as ex:
                    app.msg_box(f(_('Set correct "{}" reg.ex.\n\nError:\n{}')
                                 , self.caps['repl'], ex), app.MB_OK+app.MB_ICONWARNING) 
                    return {'fid':'repl'}
        if not self.incl_s:
            msg_status(f(_('Fill the "{}" field'), self.caps['incl'])) 
            return {'fid':'incl'}
        if 0 != self.incl_s.count('"')%2:
            msg_status(f(_('Fix quotes in the "{}" field'), self.caps['incl'])) 
            return {'fid':'incl'}
        if 0 != self.excl_s.count('"')%2:
            msg_status(f(_('Fix quotes in the "{}" field'), self.caps['excl'])) 
            return {'fid':'excl'}

        pass;                  #work_start  = time.monotonic()
        roots       = []
        if root_is_proj(self.fold_s) or root_is_tabs(self.fold_s):
            roots   = [self.fold_s]
        else:
            roots   = prep_quoted_folders(self.fold_s)
            pass;               LOG and log('roots={}',(roots))
            roots   = map(os.path.expanduser, roots)
            roots   = map(os.path.expandvars, roots)
            roots   = map(lambda f: f.rstrip(r'\/') if f!='/' else f, roots)
            roots   = list(roots)
            pass;               LOG and log('roots={}',(roots))
            if not all(map(lambda f:os.path.isdir(f), roots)):
                app.msg_box(f(_('Set existing folder in "{}" \nor use "{}" \nor use "{}".\n\n=/Presets can help.')
                             , self.caps['fold'], IN_OPEN_FILES, IN_PROJ_FOLDS), app.MB_OK+app.MB_ICONWARNING) 
                return {'fid':'fold'}

        shtp_v      = SHTP_L[int(self.shtp_s)]

        if shtp_v in (SHTP_MIDDL_R, SHTP_MIDDL_RCL
                     ,SHTP_SPARS_R, SHTP_SPARS_RCL) and (self.sort_s!='0' or self.fold_s==IN_OPEN_FILES):
            # Auto-change Tree type
            shtp_v  = ( SHTP_SHORT_R    if shtp_v==SHTP_MIDDL_R     else
                        SHTP_SHORT_RCL  if shtp_v==SHTP_MIDDL_RCL   else
                        SHTP_SHRTS_R    if shtp_v==SHTP_SPARS_R     else
                        SHTP_SHRTS_RCL  if shtp_v==SHTP_SPARS_RCL   else SHTP_SHORT_R)

        # Block action buttons
        self.lock_act(ag, 'lock-save')
        
        pass;                  #LOG and log('self.dept_n={}',(repr(self.dept_n)))
        pass;                  #LOG and log('self.olde_s={}',(self.olde_s))
        age         = self.olde_s if re.match('[<>]?[1-9]\d*/[hdwmy]$', self.olde_s) else ''
        age         = age.replace('/', '')
        age         = ('<' if age and age[0]!='<' and age[0]!='>' else '') + age
        how_walk    = dict(                                 #NOTE: fif params
             roots      =roots
            ,file_incl  =self.incl_s
            ,file_excl  =self.excl_s + ' ' + ALWAYS_EXCL
            ,depth      =self.dept_n-1               # ['All', 'In folder only', '1 level', …]
            ,skip_hidn  =self.skip_s in ('1', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
            ,skip_binr  =self.skip_s in ('2', '3')   # [' ', 'Hidden', 'Binary', 'Hidden, Binary']
            ,sort_type  =apx.icase( self.sort_s=='0','' 
                                   ,self.sort_s=='1','date,desc' 
                                   ,self.sort_s=='2','date,asc' ,'')
            ,age        =age
            ,only_frst  =int((self.frst_s+',0').split(',')[1])
            ,skip_unwr  =btn_p=='!rep'
            ,enco       =ENCO_L[int(self.enco_s)].split(', ')
            )
        what_find   = dict(
             find       =self.what_s
            ,repl       =self.repl_s if btn_p=='!rep' else None
            ,mult       =False
            ,reex       =self.reex01=='1'
            ,case       =self.case01=='1'
            ,word       =self.word01=='1'
            ,only_frst  =int((self.frst_s+',0').split(',')[0])
            )
        what_save   = dict(
             count      = btn_m!='s/!cnt'
            ,place      = btn_p!='!cnt'
            ,lines      = btn_p!='!cnt'
            )
        totb_it     = self.totb_l[self.totb_i]
        fxs         = self.stores.get('tofx', [])
        totb_v      = TOTB_NEW_TAB                  if btn_m=='s/!fnd' or totb_it==TOTB_NEW_TAB     else \
                      totb_it                       if totb_it.startswith('tab:')                   else \
                      'file:'+fxs[self.totb_i-4]    if totb_it.startswith('file:')                  else \
                      TOTB_USED_TAB
        pass;                   #LOG and log('totb_i,totb_it,totb_v={}',(totb_i,totb_it,totb_v))
        how_rpt     = dict(
             rpt_to_ed = self.rslt
            ,sprd   =    False
            ,shtp   =    SHTP_SHRTS_RCL
            ,cntx   =    False
            ,algn   =    True
            ,join   =    False
                    ) if w_rslt else dict(
             totb   =    totb_v
            ,sprd   =              self.sort_s=='0' and shtp_v not in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_SHRTS_R, SHTP_SHRTS_RCL)
            ,shtp   =    shtp_v if self.sort_s=='0' or  shtp_v     in (SHTP_SHORT_R, SHTP_SHORT_RCL, SHTP_SHRTS_R, SHTP_SHRTS_RCL) else SHTP_SHORT_R
            ,cntx   =    '1'==self.cntx_s and btn_p!='!rep'
            ,cntb   =    self.cntx_b
            ,cnta   =    self.cntx_a
            ,algn   =    '1'==self.algn_s
            ,join   =    '1'==self.join_s or  btn_m=='c/!fnd' # Append if Ctrl+Find
            )
        fil_tab     = _('tab') if root_is_tabs(self.fold_s) else _('file')
        ################################
        pass;                  #v=[].get('k')       # Err as while search
        M.rslt_body   = M.DEF_RSLT_BODY
        M.rslt_body_r = -1
        self.rslt.set_prop(app.PROP_RO                  , False)
        self.rslt.set_text_all(M.rslt_body)
        self.rslt.set_prop(app.PROP_RO                  , True)
        self.progressor = ProgressAndBreak()
        pass;                  #v=[].get('k')       # Err as while search
        rpt_data, rpt_info = None, None
        try:
            rpt_data, rpt_info = find_in_files(     #NOTE: run-fif
             how_walk   = how_walk
            ,what_find  = what_find
            ,what_save  = what_save
            ,how_rpt    = how_rpt
            ,progressor = self.progressor
            )
        except Exception as e:
            log(traceback.format_exc()) 
        if not rpt_data and not rpt_info: 
            msg_status(_("Search stopped"))
            self.lock_act(ag, 'unlock-saved')
            self.progressor = None
            return self.do_focus(aid,ag)   #continue#while_fif
        if 0==rpt_info['cllc_files']: 
            msg_status(f(_("No {}s picked"), fil_tab))
            self.lock_act(ag, 'unlock-saved')
            self.progressor = None
            return self.do_focus(aid,ag)   #continue#while_fif
        clfls   = rpt_info['cllc_files']
        frfls   = rpt_info['files']
        frgms   = rpt_info['frgms']

        pass;                  #search_end    = time.monotonic()
        pass;                  #print(f('search done: {:.2f} secs', search_end-work_start))

        ################################
        pass;                  #LOG and log('frgms={}, rpt_data=\n{}',frgms, pf(rpt_data))
        fil_tabs= fil_tab+'s'   if clfls>1 else fil_tab
        matchs  = 'matches'     if frgms>1 else 'match'
        msg_rpt = f(_('No matches found (in {} {})'), clfls, fil_tabs) \
                    if 0==frfls else \
                  f(_('Found {} {} in {}({}) {}'), frgms, matchs, frfls, clfls, fil_tabs)
        self.progressor.set_progress(msg_rpt)
        if 0==frgms and not REPORT_FAIL:    
            self.lock_act(ag, 'unlock-saved')
            self.progressor = None
            return self.do_focus(aid,ag)   #continue#while_fif
        req_opts= None
        if SAVE_REQ_TO_RPT:
            req_opts= {k:v for (k,v) in self.stores.items() if k[:3] not in ('wd_', 'wo_', 'pse')}
            req_opts['what']=self.what_s
            req_opts['repl']=self.repl_s
            req_opts['incl']=self.incl_s
            req_opts['excl']=self.excl_s
            req_opts['fold']=self.fold_s
            req_opts['dept']-=1
            req_opts    = json.dumps(req_opts)
        try:
            report_to_tab(                      #NOTE: run-report
                rpt_data
               ,rpt_info
               ,how_rpt
               ,how_walk
               ,what_find
               ,what_save
               ,progressor  = self.progressor
               ,req_opts    = req_opts
               )
        except Exception as e:
            log(traceback.format_exc()) 
        self.progressor.set_progress(msg_rpt)
        self.progressor = None
        ################################
        if 0<frgms and CLOSE_AFTER_GOOD and not w_rslt:
            self.store()
            return None #break#while_fif

        self.lock_act(ag, 'unlock-saved')
        self.progressor = None
        if '1'==self.send_s:
            return self.do_focus(aid,ag)
        pass;                  #log("STORE_PREV_RSLT={}",(STORE_PREV_RSLT))
        M.rslt_body     = self.rslt.get_text_all() if STORE_PREV_RSLT else ''
        M.rslt_body_r   = -1
        self.srcf_acts('set-no-src')
        pass;                  #work_end    = time.monotonic()
        pass;                  #print(f('report done: {:.2f} secs', work_end-search_end))
        pass;                  #print(f('woks   done: {:.2f} secs', work_end-work_start))
        return d(fid='rslt')
       #def do_work
       
    def lock_act(self, ag, how, cids=None):
        ''' Block/UnBlock controls while working 
                how     'lock'          from cids
                        'unlock'        from cids
                        'lock-save'     save locked controls
                        'unlock-saved'  saved controls
        '''
        pass;                  #log("###how, cids={}",(how, cids))
        if False:pass
        elif how=='lock'     and cids:
            ag.update(ctrls={cid:{'en': False} for cid in cids})
        elif how=='unlock'   and cids:
            ag.update(ctrls={cid:{'en': True } for cid in cids})
        elif how=='lock-save':
            pass;              #log('c-type={}',({cid:cfg['type'] for cid,cfg in ag.ctrls.items()}))
            self.locked_cids    = [cid 
                for cid,cfg in ag.ctrls.items()
                if  cfg['type'] in ('button', 'edit', 'check', 'checkbutton', 'combo_ro')    # types of the active controls in main dlg
                and cfg.get('en', True)
            ]
            pass;              #log('self.locked_cids={}',(self.locked_cids))
            ag.update(ctrls={cid:{'en': False} for cid in self.locked_cids})
        elif how=='unlock-saved'   and self.locked_cids:
            ag.update(ctrls={cid:{'en': True } for cid in self.locked_cids})
       #def lock_act
       
    def wnen_menu(self, ag, tag):
        pass;              #log('tag={}',(tag))
        if False:pass
        elif tag=='help':       return self.do_help('help', ag)
        elif tag=='!fnd-main':  return self.do_work('!fnd', ag, btn_m=   '!fnd')
        elif tag=='!fnd-ntab':  return self.do_work('!fnd', ag, btn_m= 's/!fnd')
        elif tag=='!fnd-apnd':  return self.do_work('!fnd', ag, btn_m= 'c/!fnd')
        elif tag=='!cnt-main':  return self.do_work('!cnt', ag, btn_m=   '!cnt')
        elif tag=='!cnt-name':  return self.do_work('!cnt', ag, btn_m= 's/!cnt')
        elif tag=='!rep-main':  return self.do_work('!rep', ag, btn_m=   '!rep')
        elif tag=='!rep-noqu':  return self.do_work('!rep', ag, btn_m= 's/!rep')
        elif tag=='cfld-main':  return self.do_fold('cfld', ag, btn_m=   'cfld')
        elif tag=='cfld-file':  return self.do_fold('cfld', ag, btn_m= 's/cfld')
        elif tag=='cfld-tabs':  return self.do_fold('cfld', ag, btn_m= 'c/cfld')
        elif tag=='cfld-ctab':  return self.do_fold('cfld', ag, btn_m='sc/cfld')
        elif tag=='brow-main':  return self.do_fold('brow', ag, btn_m=   'brow')
        elif tag=='brow-file':  return self.do_fold('brow', ag, btn_m= 's/brow')
        elif tag=='dept-all':   return self.do_dept('depa', ag)
        elif tag=='dept-only':  return self.do_dept('depo', ag)
        elif tag=='dept-one':   return self.do_dept('dep1', ag)
        elif tag=='pres-1':     return self.do_pres('prs1', ag)
        elif tag=='pres-2':     return self.do_pres('prs2', ag)
        elif tag=='pres-3':     return self.do_pres('prs3', ag)
        elif tag=='pres-4':     return self.do_pres('prs4', ag)
        elif tag=='pres-5':     return self.do_pres('prs5', ag)
        elif tag=='pres-cfg':   return self.do_pres('conf', ag)
        elif tag=='pres-save':  return self.do_pres('save', ag)
        elif tag=='cust-rprt':  return self.do_morp('morp', ag)
        elif tag=='cust-srch':  return self.do_mofi('mofi', ag)
        elif tag=='cust-enco':  return self.srcf_acts('ask-enco', ag)

        elif tag=='pres-tabs':  self.fold_s     = IN_OPEN_FILES
        elif tag=='pres-proj':  self.fold_s     = IN_PROJ_FOLDS
            
        elif tag=='cust-excl':  self.wo_excl    = not self.wo_excl
        elif tag=='cust-repl':  self.wo_repl    = not self.wo_repl
            
        elif tag=='edit-opts':  dlg_fif_opts(self)
        elif tag=='edit-dcls':
            self.store(what='save')
            dlg_nav_by_dclick()
            self.store(what='load')

        elif tag=='rsva' and '0'==self.send_s:
            self.rslt_va= not self.rslt_va
            self.stores['rslt_va']  = self.rslt_va
            rslt_ali= ALI_TP if self.rslt_va else ALI_LF
            return [d(ctrls=[0
                            ,('rslt',d(ali=rslt_ali   ,w=self.rslt_w   ,h=self.rslt_h     ))
                            ,('sptr',d(ali=rslt_ali   ,x=self.rslt_w+5 ,y=self.rslt_h+5   ))
                           ][1:])
                   ,self.do_resize(self.ag)
                   ]
        elif tag[:4] in ('relt', 'rmlt', 'svlt') and '0'==self.send_s:
            lays_l      = self.stores.get('layouts', [])  # [{nm:Nm, dlg_x:?, dlg_y:?, dlg_h:?, dlg_w:?, split:?}]
            lays_d      = {lt['nm']:lt for lt in lays_l}
            lt_i        = int(tag[4:])-1  if tag[:4] in ('relt', 'rmlt')    else -1
            layout      = lays_l[lt_i]  if 0<=lt_i<len(lays_l)              else None
            if 0:pass
            elif tag[:4]=='rmlt':
                if not layout:  return []
                if  app.ID_OK != app.msg_box(
                            f(_('Remove "{}"?'), layout['nm'])
                            , app.MB_OKCANCEL+app.MB_ICONQUESTION): return []
                del lays_l[lt_i]
            elif tag=='svlt':
                nm_tmpl     = '#{}'
                lt_nm       = f(nm_tmpl
                               ,first_true(itertools.count(1+len(lays_d))
                                        ,pred=lambda n:f(nm_tmpl, n) not in lays_d))     # First free #N after len()
                while True:
                    pass;  #LOG and log('lt_nm={!r}',(lt_nm))
                    lt_nm   = app.dlg_input('Name to save dialog and controls positions', lt_nm)
                    if not lt_nm:   return []
                    lt_nm   = lt_nm.strip()
                    if not lt_nm:   return []
                    if lt_nm in lays_d and \
                        app.ID_OK != app.msg_box(
                                f(_('Name "{}" already used. Overwrite?'), lt_nm)
                                , app.MB_OKCANCEL+app.MB_ICONQUESTION): continue
                    break
                layout      = None
                if lt_nm in lays_d:
                    layout  = lays_d[lt_nm]     # Overwrite
                else:
                    layout  = d(nm=lt_nm)       # Create
                    lays_l+=[layout]
                # Fill
                f_xywh      = ag.fattrs(attrs=('x', 'y', 'w', 'h'))
                layout.update(d(dlg_x=f_xywh['x']
                               ,dlg_y=f_xywh['y']
                               ,dlg_w=f_xywh['w']
                               ,dlg_h=f_xywh['h']
                               ,over =self.rslt_va
                               ,split=ag.cattr('rslt', 'h' if self.rslt_va else 'w')
                             ))
            elif tag[:4]=='relt':
                if not layout:  return []
                self.rslt_va    = layout.get('over', False)
                if self.rslt_va:
                    self.rslt_h = layout.get('split', self.rslt_h)
                else:
                    self.rslt_w = layout.get('split', self.rslt_w)
                self.stores['rslt_va']  = self.rslt_va
                rslt_ali= ALI_TP    if self.rslt_va else ALI_LF
                ctrls   = [0
                        ,('rslt',d(ali=rslt_ali   ,h=self.rslt_h    ))
                        ,('sptr',d(ali=rslt_ali   ,y=self.rslt_h+5  ))
                       ][1:]        if self.rslt_va else [0
                        ,('rslt',d(ali=rslt_ali   ,w=self.rslt_w    ))
                        ,('sptr',d(ali=rslt_ali   ,x=self.rslt_w+5  ))
                       ][1:]
                msg_status(f(_('Apply layout: {}'), layout['nm']))
                return [d(form=d(x=layout['dlg_x']
                                ,y=layout['dlg_y']
                                ,w=layout['dlg_w']
                                ,h=layout['dlg_h']))
                       ,d(ctrls=ctrls)
                       ,self.do_resize(self.ag)
                       ]
            # Save
            self.stores['layouts']  = lays_l
            self.store()
            return []

        elif tag=='rslt-fold':
            toggle_folding(self.rslt)                   ;return []
        elif tag=='rslt-opfr':
            nav_to_src('same', _ed=self.rslt)           ;return []
        elif tag=='rslt-tofr':
            nav_to_src('same', _ed=self.rslt)           ;return None
        elif tag=='srcf-opfr':
            nav_as(self.srcf._loaded_file, self.srcf)   ;return None
        elif tag=='rslt-move':
            app.file_open('')
            ed.set_prop(app.PROP_ENC,       'UTF-8')
            ed.set_prop(app.PROP_TAB_TITLE, _('Results'))
            ed.set_text_all(self.rslt.get_text_all())
            mrks    = self.rslt.attr(app.MARKERS_GET)
            for mrk in (mrks if mrks else []):
                ed.attr(app.MARKERS_ADD, *mrk)
            ed.set_prop(app.PROP_LEXER_FILE, FIF_LEXER)
            ed.set_prop(app.PROP_TAB_SIZE  , 1)
            return None
        
        else:
            return []
        self.upd_def_status(True)
        self.pre_cnts()
        return (dict(form =dict(h    =self.dlg_h ,h_min=self.dlg_h     ,h_max=self.dlg_h if '1'==self.send_s else 0
                                )
                    ,vals =self.get_fif_vals()
                    ,ctrls=self.get_fif_cnts('vis+pos'))
               ,self.do_focus('what',ag)
               )
       #def wnen_menu
        
    def do_menu(self, aid, ag, data=''):
        M,m     = self.__class__,self
        msg_status(self.status_s)
        pass;                  #log('aid,data={}',(aid,data))
#       btn_p,btn_m = FifD.scam_pair(aid)
        btn_p,btn_m = ag.scam_pair(aid)
        if btn_m=='c/menu':     # [Ctrl+"="] - dlg_valign_consts
            dlg_valign_consts()
            return []

        if aid in ('rslt', 'srcf'):
            pass;              #log('',())
            where, dx, dy       = '+h', 0, 0
            if type(data)==dict:
                pass;          #log('data={}',(data))
                where, dx, dy   = 'dxdy', 7+data['x'], 7+data['y']
            if aid=='rslt': ag.show_menu(aid, [
                    d(tag='rslt-opfr'   ,key='Enter'        ,cap=  _('Open fragment')       ,cmd=self.wnen_menu ,en=bool(self.srcf._loaded_file)
                  ),d(tag='rslt-tofr'   ,key='Ctrl+Enter'   ,cap=  _('Go to fragment')      ,cmd=self.wnen_menu ,en=bool(self.srcf._loaded_file)
                  ),d(                                       cap='-'
                  ),d(tag='rslt-fold'   ,key='Ctrl++'       ,cap=  _('Fold branch')         ,cmd=self.wnen_menu ,en=(M.rslt_body_r!=-1)
                  ),d(                                       cap='-'
                  ),d(tag='rslt-move'                       ,cap=  _('Copy Results to tab') ,cmd=self.wnen_menu ,en=(M.rslt_body_r!=-1)
                                 )]
                ,   where, dx, dy)
            if aid=='srcf': ag.show_menu(aid, [
                    d(tag='srcf-opfr'   ,key='Ctrl+Enter'   ,cap=  _('Go to fragment')      ,cmd=self.wnen_menu ,en=bool(self.srcf._loaded_file)
                                 )]
                ,   where, dx, dy)
            return False

        self.copy_vals(ag) 
        find_c  = self.caps['!fnd']
        repl_c  = self.caps['!rep']
        cfld_c  = self.caps['cfld']
        brow_c  = self.caps['brow'].replace('.', '').replace('...', '').replace('…', '')
        fold_c  = self.caps['fold']
        w_rslt  = '0'==self.send_s
        mn_coun = [
    d(tag='!cnt-main'   ,key='Alt+T'        ,cap=  _('Count matches only')
  ),d(tag='!cnt-name'   ,key='Ctrl+T'       ,cap=  _('Find file names only')
                   )]
        mn_repl = [
    d(tag='!rep-main'   ,key='Alt+P'        ,cap=  _('Find and replace')                                                    ,en=not self.wo_repl
  ),d(tag='!rep-noqu'                       ,cap=f(_('Find and replace (without question)   [Shift+"{}"]')      , repl_c)   ,en=not self.wo_repl
                   )]
        mn_find = [
    d(tag='!fnd-main'   ,key='Enter'        ,cap=  _('Find')
  ),d(tag='!fnd-ntab'                       ,cap=f(_('Find and put report to new tab   [Shift+"{}"]')           , find_c)    ,en=not w_rslt
  ),d(tag='!fnd-apnd'                       ,cap=f(_('Find and append result to existing report   [Ctrl+"{}"]') , find_c)    ,en=not w_rslt
  ),d(                                       cap='-'
                   )] +mn_coun+ [
    d(                                       cap='-'
                   )] +mn_repl
        mn_cfld = [
    d(tag='cfld-main'   ,key='Alt+C'        ,cap=  _('Use folder of current file')                                          ,en=bool(ed.get_filename())
  ),d(tag='cfld-file'   ,key='Ctrl+Shift+C' ,cap=f(_('Prepare search in the current file   [Shift+"{}"]')       , cfld_c)   ,en=bool(ed.get_filename())
  ),d(                                       cap='-'
  ),d(tag='cfld-tabs'                       ,cap=f(_('Prepare search in all tabs   [Ctrl+"{}"]')                , cfld_c)
  ),d(tag='cfld-ctab'                       ,cap=f(_('Prepare search in the current tab   [Shift+Ctrl+"{}"]')   , cfld_c)
  ),d(                                       cap='-'
  ),d(tag='pres-proj'                       ,cap=f(_('Fill "{}" to find in project folders')                    , fold_c)
  ),d(tag='pres-tabs'                       ,cap=f(_('Fill "{}" to find in tabs')                               , fold_c)
                   )]
        mn_brow = [
    d(tag='brow-main'   ,key='Alt+B'        ,cap=  _('Choose folder…')
  ),d(tag='brow-file'   ,key='Ctrl+B'       ,cap=f(_('Choose file to find in it…')+ '[Shift+"{}"]'              , brow_c)
                   )]
        mn_dept = [
    d(tag='dept-only'   ,key='Alt+Y'        ,cap=  _('Apply "Onl&y"   [Ctrl+Num0]')
  ),d(tag='dept-one'    ,key='Alt+Shift+1'  ,cap=  _('Apply "+1 level"   [Ctrl+Num1]')
  ),d(tag='dept-all'    ,key='Alt+L'        ,cap=  _('Apply "+A&ll"   [Ctrl+Num9]')
                   )]
        mn_cust = [
    d(tag='cust-rprt'   ,key='Alt+O'        ,cap=  _('Options for report t&o tab…')                                         ,en=not w_rslt
  ),d(tag='cust-srch'   ,key='Alt+E'        ,cap=  _('Extra options for s&earch…')
  ),d(tag='edit-opts'   ,key='Ctrl+E'       ,cap=  _('&View and edit engine options…')
  ),d(tag='edit-dcls'                       ,cap=  _('&Configure navigation with double-click in tab report…')
  ),d(tag='cust-enco'                       ,cap=f(_('Source encod&ing{}…'), f(' ({})', self.srcf_acts('show-enco')))       ,en=w_rslt
# ),d(tag='cust-enco'                       ,cap=f(_('Source Encod&ing{}…'), f(' ({})', self.enc_srcf) if self.enc_srcf else ''),en=w_rslt
  ),d(                                       cap='-'
  ),d(tag='cust-excl'   ,ch=not self.wo_excl,cap=f(_('Show "{}"')           , self.caps['excl'])
  ),d(tag='cust-repl'   ,ch=not self.wo_repl,cap=f(_('Show "{}" and "{}"')  , self.caps['repl']                 , repl_c)
                   )]
        pset_l  = self.stores.get('pset', [])
        pset_n  = len(pset_l)
        mn_pres = [
    d(tag='pres-save',key='Ctrl+S'                     ,cap=  _('&Save preset as…')
  ),d(tag='pres-cfg' ,key='Ctrl+Alt+S'  ,en=pset_n>0   ,cap=f(_('Presets [{}]…'), pset_n)
  ),d(                                                  cap='-')
                  ]+[
    d(tag='pres-'+str(1+nps)    ,cap=f('&{}: {}' ,1+nps, limit_len(ps['name'], 60))   
                    ,key=(f('Ctrl+{}', 1+nps) if nps<5 else '')
                                                                             ) for nps, ps in enumerate(pset_l)
                  ]

        mn_its  = None
        if False:pass
        elif aid=='menu':
            pass;              #log('?menu',())
            lays_l  = self.stores.get('layouts', [])  # [{nm:Nm, dlg_x:?, dlg_y:?, dlg_h:?, dlg_w:?, split:?}]
            mn_lays =      [
    d(tag='rsva'              ,cap=_('Set Results o&ver Source')        ,ch=self.rslt_va
  ),d(tag='svlt'              ,cap=_('&Save dialog and controls positions...')
                          )]
            if lays_l: 
                mn_lays += [d( cap='-')]
                mn_lays += [
    d(tag='relt'+str(1+nlt)   ,cap=f(_('&{}: Restore "{}"') ,1+nlt, limit_len(lt['nm'], 30))
                    ,key=(f('Alt+{}', 1+nlt) if nlt<5 else '')
                                                                                            )   for nlt, lt in enumerate(lays_l)
                           ]
                mn_lays += [d( cap=_('&Forget'),sub=[
    d(tag='rmlt'+str(nlt)     ,cap=f('&{}: "{}"...'      ,1+nlt, limit_len(lt['nm'], 30)))      for nlt, lt in enumerate(lays_l)
                                                              ]
                          )]
            mn_its  = [ 
      d(                             cap=_('&Find')      ,sub=mn_find
    ),d(                             cap=_('Sco&pe')     ,sub=mn_cfld
    ),d(                             cap=_('&Browse')    ,sub=mn_brow
    ),d(                             cap=_('&Depth')     ,sub=mn_dept
    ),d(                             cap=_('Pre&sets')   ,sub=mn_pres
    ),d(                             cap=_('&Layout')    ,sub=mn_lays   ,en=w_rslt
    ),d(                             cap='-'
    )                                                     ] + mn_cust + [
      d(                             cap='-'
    ),d(tag='help'    ,key='Alt+H'  ,cap=_('&Help…')
                   )]
        elif aid=='!fnd':
            mn_its  = mn_find
        elif aid=='!rep':
            mn_its  = mn_repl
        elif aid=='cfld':
            mn_its  = mn_cfld
        elif aid=='brow':
            mn_its  = mn_brow
        elif aid=='dept':
            mn_its  = mn_dept

        if mn_its:
            set_all_for_tree(mn_its, 'sub', 'cmd', self.wnen_menu)
            ag.show_menu(aid, mn_its)
        return []
       #def do_menu
       
    def do_key_down(self, idd, idc, data=''):
        M,m     = self.__class__,self
#       scam    = data if data else app.app_proc(app.PROC_GET_KEYSTATE, '')
        ag      = self.ag
        scam    = ag.scam()
        pass;                  #log('idc, data, scam, chr(idc)={}',(idc, data, scam, chr(idc)))
        fid     = ag.fattr('fid')
#       if (scam,idc)==('sca',VK_ENTER):                                                            # Alt+Ctrl+Shift+Enter
#           pass;           log('ag.hide()',())
#           ag.hide()
#           return 
        if idc==VK_APPS and fid in ('rslt', 'srcf'):                                                # ContextMenu in rslt or srcf
            _ed     = m.rslt if fid=='rslt' else m.srcf
            c, r    = _ed.get_carets()[0][:2]
            x, y    = _ed.convert(app.CONVERT_CARET_TO_PIXELS, c, r)
            m.do_menu(fid, m.ag, data=d(x=x, y=y))
            return False
        
        if (scam,idc)==('c',ord('F')) or (scam,idc)==('c',ord('R')):                                # Ctrl+F or Ctrl+R
            ag.opts['on_exit_focus_to_ed'] = None
            ag.hide()
            to_dlg  = cmds.cmd_DialogFind if idc==ord('F') else cmds.cmd_DialogReplace
            ed.cmd(to_dlg)
            if app.app_api_version()>='1.0.248':
                prop    = d(
                    find_d      = ag.cval('what')
                ,   op_regex_d  = ag.cval('reex')
                ,   op_case_d   = ag.cval('case')
                ,   op_word_d   = ag.cval('word')
                )
                if not m.wo_repl and to_dlg==cmds.cmd_DialogReplace:
                    prop[rep_d] = ag.cval('repl')
                app.app_proc(app.PROC_SET_FINDER_PROP, prop)
            return
        pass;                  #log('send.val={}',(ag.cval('send')))
        upd     = {}
        if 0:pass           #NOTE: do_key_down
        elif scam=='c'  and idc==VK_ENTER \
                        and '0'==self.send_s \
                        and fid!='rslt' \
                        and fid!='srcf':            upd={'fid':'rslt'}                              # Ctrl+Enter
        elif scam==''   and idc==VK_ENTER \
                        and fid=='rslt':            nav_to_src('same', _ed=m.rslt)      ;upd={}     # Enter      in rslt
        elif scam=='c'  and idc==VK_ENTER \
                        and fid=='rslt':            nav_to_src('same', _ed=m.rslt)      ;upd=None   # Ctrl+Enter in rslt
        elif scam=='c'  and idc==VK_ENTER \
                        and fid=='srcf'\
                        and m.srcf._loaded_file:    nav_as(m.srcf._loaded_file, m.srcf) ;upd=None   # Ctrl+Enter in srcf
        
        elif scam==''   and idc==VK_TAB \
                        and fid=='rslt':            upd={'fid':'srcf'}                              # Tab in rslt
        elif scam=='s'  and idc==VK_TAB \
                        and fid=='srcf':            upd={'fid':'rslt'}                              # Shift+Tab in srcf
        elif scam==''   and idc==VK_TAB \
                        and fid=='srcf':            upd={'fid':'what'}                              # Tab in srcf
        elif scam== 'c' and idc==187 \
                        and fid=='rslt':            toggle_folding(m.rslt)                          # Ctrl+= in rslt
        elif scam== 'c' and idc==VK_NUMPAD0:        upd=m.do_dept('depo', ag)                       # Ctrl+Num0
        elif scam== 'c' and idc==VK_NUMPAD1:        upd=m.do_dept('dep1', ag)                       # Ctrl+Num1
        elif scam== 'c' and idc==VK_NUMPAD9:        upd=m.do_dept('depa', ag)                       # Ctrl+Num9
        elif scam=='sc' and idc==ord('C'):          upd=m.do_fold('cfld', ag, btn_m='s/cfld')       # Ctrl+Shift+C
        elif scam== 'c' and idc==ord('B'):          upd=m.do_fold('brow', ag, btn_m='s/brow')       # Ctrl+B
        elif scam== 'c' and idc==ord('S'):          PresetD(self).save()                ;upd={}     # Ctrl+S
        elif scam=='ca' and idc==ord('S'):          PresetD(self).config()              ;upd={}     # Ctrl+Alt+S
        elif scam== 'c' and idc==ord('T'):          upd=m.do_work('!cnt', ag, btn_m='s/!cnt')       # Ctrl+T
        elif scam== 'c' and ord('1')<=idc<=ord('5'):upd=m.do_pres('prs'+chr(idc), ag)               # Ctrl+1..Ctrl+5
        elif scam== 'a' and ord('1')<=idc<=ord('5'):upd=m.wnen_menu(ag, 'relt'+chr(idc))            # Alt+1..Alt+5
        elif scam== 'c' and idc==ord('E'):          dlg_fif_opts(self)                              # Ctrl+E
        else:                                       return 
        pass;                  #log('upd={}',(upd))
        ag._update_on_call(upd)
        return False
       #def do_key_down

    def do_click_dbl(self, aid, ag, data=''):
        M,m     = self.__class__,self
#       scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        scam    = ag.scam()
        pass;                  #log('aid, data, scam={}',(aid, data, scam))
        upd     = None
        if 0:pass
        elif aid=='rslt':
            nav_to_src('same', _ed=m.rslt)
            upd = None if scam=='c' else {}
        elif aid=='srcf':
            nav_as(m.srcf._loaded_file, m.srcf)
            upd = None
        else:
            return 
        ag._update_on_call(upd)
        return False
       #def do_click_dbl
    
    def pre_cnts(self):
        M,m     = self.__class__,self
        hp      = self.hip
        self.what_l = [s for s in self.stores.get(hp+'what', []) if s ]
        self.incl_l = [s for s in self.stores.get(hp+'incl', []) if s ]
        self.excl_l = [s for s in self.stores.get(hp+'excl', []) if s ]
        self.fold_l = [s for s in self.stores.get(hp+'fold', []) if s ]
        self.repl_l = [s for s in self.stores.get(hp+'repl', []) if s ]
        self.totb_l = FifD.get_totb_l(self.stores.get('tofx', []))
        self.incl_s = self.incl_s if self.incl_s else self.incl_l[0] if self.incl_l else ''
        self.excl_s = self.excl_s if self.excl_s else self.excl_l[0] if self.excl_l else ''
        self.fold_s = self.fold_s if self.fold_s else self.fold_l[0] if self.fold_l else ''
        
        w_rslt      = '0'==self.send_s
        self.gap1   = (GAP- 28 if self.wo_repl else GAP)
        self.gap2   = (GAP- 28 if self.wo_excl else GAP)+self.gap1 -GAP
        rslt_srcf_h =   0 if not w_rslt else max(100, M.RSLT_H+5+M.SRCF_H)
        self.dlg_w  = self.TBN_L + FifD.BTN_W + GAP
        self.dlg_h  = FifD.DLG_H0 + self.gap2 + 25 + rslt_srcf_h   +(0 if 'win'==get_desktop_environment() else 23)
        self.dlg_h0 = FifD.DLG_H0 + self.gap2 + 5                  +(0 if 'win'==get_desktop_environment() else 23)
        pass;                  #log('DLG_H0, gap2={}',(FifD.DLG_H0, self.gap2))
        pass;                  #log('dlg_w, dlg_h, dlg_h0={}',(self.dlg_w, self.dlg_h, self.dlg_h0))
        return self
       #def pre_cnts

    def get_fif_cnts(self, how=''): #NOTE: fif_cnts
        M,m     = self.__class__,self
        pass;                  #LOG and log('dlg_w, dlg_h={}',(dlg_w, dlg_h))
        pass;                  #LOG and log('gap1={}',(gap1))
        pass;                  #log('m.rslt_w={}',(m.rslt_w))
        g1      = m.gap1
        g2      = m.gap2
        w_excl  = not self.wo_excl
        w_repl  = not self.wo_repl
        w_rslt  = '0'==self.send_s
        dept_l  = M.CMB_L+M.TXT_W-100
        pass;                  #log('mask_h={}',(mask_h))
        d       = dict
        if how=='vis+pos':  return [0
 ,('rep_',d(         tid='repl'             ,vis=w_repl ))
 ,('repl',d(         t  =5+  28+M.EG1       ,vis=w_repl ))
 ,('inc_',d(         tid='incl'                         ))
 ,('incl',d(         t  =g1+ 56+M.EG2                   ))
 ,('exc_',d(         tid='excl'             ,vis=w_excl )) 
 ,('excl',d(         t  =g1+ 84+M.EG3       ,vis=w_excl )) 
 ,('fol_',d(         tid='fold'                         ))
 ,('fold',d(         t  =g2+112+M.EG4                   ))
 ,('dept',d(         t  =g2+112+M.EG4                   ))
 ,('brow',d(         tid='fold'                         ))
 ,('mofi',d(         tid='incl'                         ))
 ,('send',d(         tid='fold'                         ))
 ,('morp',d(         tid='fold'          ,en=not w_rslt ))
 ,('pt'  ,d(                    h=m.dlg_h0              ))
 ,('pb'  ,d(                                 vis=w_rslt ))
 ,('rslt',d(                                 en =w_rslt ))
 ,('sptr',d(                                 en =w_rslt ))
 ,('srcf',d(                                 en =w_rslt ))
 ,('!rep',d(         tid='repl'             ,vis=w_repl ))
 ,('cfld',d(         tid='incl'                         ))
  ][1:] 

    # Start=Full cnts
        rslt_ali= ALI_TP if m.rslt_va else ALI_LF
        cnts    = [0                                                      #  ghjmqsz ?&m
 ,('depa',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&l'    ,call=m.do_dept ))# &l
 ,('depo',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&y'    ,call=m.do_dept ))# &y
 ,('dep1',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&!'    ,call=m.do_dept ))# &!
 ,('!ctt',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&t'    ,call=m.do_work ))# &t
 ,('loop',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&v'    ,call=m.do_more ))# &v
 ,('help',d(tp='bt' ,t=0,l=-99,w=44,sto=F  ,cap='&h'    ,call=m.do_help ))# &h

 ,('pt'  ,d(tp='pn'         ,ali=ALI_TP ,w=m.dlg_w ,h=m.dlg_h0))

 ,('reex',d(tp='chb',p='pt' ,tid='what'     ,l= 5+38*0      ,w=39               ,cap='&.*'                  ,hint=reex_h            ,bind='reex01'  ,call=m.do_focus                ))# &*
 ,('case',d(tp='chb',p='pt' ,tid='what'     ,l= 5+38*1      ,w=39               ,cap=_('&aA')               ,hint=case_h            ,bind='case01'  ,call=m.do_focus                ))# &a
 ,('word',d(tp='chb',p='pt' ,tid='what'     ,l= 5+38*2      ,w=39               ,cap=_('"&w"')              ,hint=word_h            ,bind='word01'  ,call=m.do_focus                ))# &w
                                                                                                                                                                                    
 ,('wha_',d(tp='lb' ,p='pt' ,tid='what'     ,l=M.LBL_L      ,r=M.CMB_L-5        ,cap='>'+_('*&Find what:')                                                                          ))# &f
 ,('what',d(tp='cb' ,p='pt' ,t= 5           ,l=M.CMB_L      ,w=M.TXT_W  ,a='lR' ,items=m.what_l                                     ,bind='what_s'                                  ))# 
 ,('rep_',d(tp='lb' ,p='pt' ,tid='repl'     ,l=M.LBL_L      ,r=M.CMB_L-5        ,cap='>'+_('&Replace with:')            ,vis=w_repl                                                 ))# &r
 ,('repl',d(tp='cb' ,p='pt' ,t= 5+ 28+M.EG1 ,l=M.CMB_L      ,w=M.TXT_W  ,a='lR' ,items=m.repl_l                         ,vis=w_repl ,bind='repl_s'                                  ))# 
 ,('inc_',d(tp='lb' ,p='pt' ,tid='incl'     ,l=M.LBL_L      ,r=M.CMB_L-5        ,cap='>'+_('*&In files:')   ,hint=mask_h                                                            ))# &i
 ,('incl',d(tp='cb' ,p='pt' ,t=g1+ 56+M.EG2 ,l=M.CMB_L      ,w=M.TXT_W  ,a='lR' ,items=m.incl_l                                     ,bind='incl_s'                                  ))# 
 ,('exc_',d(tp='lb' ,p='pt' ,tid='excl'     ,l=M.LBL_L      ,r=M.CMB_L-5        ,cap='>'+_('Not in files:') ,hint=excl_h,vis=w_excl                                               ))# 
 ,('excl',d(tp='cb' ,p='pt' ,t=g1+ 84+M.EG3 ,l=M.CMB_L      ,w=M.TXT_W  ,a='lR' ,items=m.excl_l                         ,vis=w_excl ,bind='excl_s'                                  ))# 
 ,('fol_',d(tp='lb' ,p='pt' ,tid='fold'     ,l=M.LBL_L      ,r=M.CMB_L-5        ,cap='>'+_('*I&n folder:')  ,hint=fold_h                                                           ))# &n
 ,('fold',d(tp='cb' ,p='pt' ,t=g2+112+M.EG4 ,l=M.CMB_L  ,w=M.TXT_W-102  ,a='lR' ,items=m.fold_l                                     ,bind='fold_s'                                  ))# 
 ,('dept',d(tp='cbr',p='pt' ,t=g2+112+M.EG4 ,l=dept_l       ,w=100      ,a='LR' ,items=DEPT_L               ,hint=dept_h            ,bind='dept_n'                  ,menu=m.do_menu ))# 
 ,('brow',d(tp='bt' ,p='pt' ,tid='fold'     ,l=M.TBN_L      ,w=M.BTN_W  ,a='LR' ,cap=_('&Browse…')          ,hint=brow_h                            ,call=m.do_fold ,menu=m.do_menu ))# &b
 ,('cfld',d(tp='bt' ,p='pt' ,tid='incl'     ,l=M.TBN_L      ,w=M.BTN_W  ,a='LR' ,cap=_('&Current')          ,hint=cfld_h                            ,call=m.do_fold ,menu=m.do_menu ))# &c
                                                                                                                                                                                    
 ,('mofi',d(tp='bt' ,p='pt' ,tid='incl'     ,l= 5           ,w=39*3             ,cap=_('For s&earch…')      ,hint=mofi_h                            ,call=m.do_mofi                 ))# &e
 ,('send',d(tp='ch' ,p='pt' ,tid='fold'     ,l= 5           ,w=39*1             ,cap=_('Sen&d')             ,hint=send_h                            ,call=m.do_morp                 ))# &d
 ,('morp',d(tp='bt' ,p='pt' ,tid='fold'     ,l= 5+39*2-10   ,w=39*1+10          ,cap=_('t&o…')              ,hint=morp_h,en=not w_rslt              ,call=m.do_morp                 ))# &o
                                                                                                                                                                                    
 ,('!fnd',d(tp='bt' ,p='pt' ,tid='what'     ,l=M.TBN_L  ,w=M.BTN_W-39   ,a='LR' ,cap=_('Find'),def_bt=True  ,hint=find_h                            ,call=m.do_work ,menu=m.do_menu ))# 
 ,('!rep',d(tp='bt' ,p='pt' ,tid='repl'     ,l=M.TBN_L  ,w=M.BTN_W      ,a='LR' ,cap=_('Re&place')          ,hint=repl_h,vis=w_repl                 ,call=m.do_work ,menu=m.do_menu ))# &p
 ,('menu',d(tp='bt' ,p='pt' ,tid='what'     ,l=M.TBN_L+M.BTN_W-39,w=39  ,a='LR' ,cap='&='                   ,hint=menu_h,sto=False                  ,call=m.do_menu                 ))# &=
                                                                                                                                                                                    
 ,('pb'  ,d(tp='pn'         ,ali=ALI_CL     ,vis=w_rslt                                                                             ))
#,('rslt',d(tp='edr',p='pb' ,ali=rslt_ali   ,en =w_rslt     ,w=m.rslt_w     ,w_min=M.RSLT_W ,border='1'                                                             ,menu=m.do_menu 
 ,('rslt',d(tp='edr',p='pb' ,ali=rslt_ali   ,en =w_rslt     ,w=m.rslt_w     ,w_min=M.RSLT_W ,border='1'                                                             ,on_menu=m.do_menu_event#,menu=m.do_menu 
                                                            ,h=m.rslt_h     ,h_min=M.RSLT_H             ,on_caret    =m.do_rslt_click                               
                                                                                                        ,on_click_dbl=m.do_click_dbl))
 ,('sptr',d(tp='sp' ,p='pb' ,ali=rslt_ali   ,en =w_rslt     ,x=m.rslt_w+5
                                                            ,y=m.rslt_h+5                                                           )) 
#,('srcf',d(tp='edr',p='pb' ,ali=ALI_CL     ,en =w_rslt                     ,w_min=M.SRCF_W ,border='1'                                                             ,menu=m.do_menu  
 ,('srcf',d(tp='edr',p='pb' ,ali=ALI_CL     ,en =w_rslt                     ,w_min=M.SRCF_W ,border='1'                                                             ,on_menu=m.do_menu_event#,menu=m.do_menu  
                                                                            ,h_min=M.SRCF_H             ,on_click_dbl=m.do_click_dbl))
                                                                                                                                      
 ,('stbr',d(tp='sb'         ,ali=ALI_BT         ))  # 
                ][1:]
        self.caps   = {cid:cnt['cap']             for cid,cnt           in cnts
                        if cnt['tp'] in ('bt', 'ch')          and 'cap' in cnt}
        self.caps.update({cid:cnts[icnt-1][1]['cap'] for (icnt,(cid,cnt)) in enumerate(cnts)
                        if cnt['tp'] in ('cb', 'cb-r', 'ed')  and 'cap' in cnts[icnt-1][1]})
        self.caps   = {k:v.strip(' :*|\\/>*').replace('&', '') for (k,v) in self.caps.items()}
        return cnts
       #def get_fif_cnts
    
    def get_fif_vals(self):
        vals    =       dict( reex=self.reex01
                             ,case=self.case01
                             ,word=self.word01
                             ,what=self.what_s
                             ,incl=self.incl_s
                             ,fold=self.fold_s
                             ,dept=self.dept_n
                             ,send=self.send_s
                            )
        if not self.wo_excl:
            vals.update(dict( excl=self.excl_s))
        if not self.wo_repl:
            vals.update(dict( repl=self.repl_s))
        pass;                  #LOG and log('vals={}',pf(vals))
        return vals
       #def get_fif_vals
    
   #class FifD

def toggle_folding(ed_):
    """ Try to toggle folding for line of first caret
    """
    row     = ed_.get_carets()[0][1]
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
    fold_i, \
    fold_d  = r_fold_l[0][:2]
    folded  = fold_d[4]
    pass;                  #log('fold_i,folded,fold_d={}',(fold_i,folded,fold_d))
    if not folded:
        pass;              #log('set_caret row={}',(fold_d[0]))
        ed_.set_caret(0, fold_d[0])
    ed_.folding(app.FOLDING_UNFOLD if folded else app.FOLDING_FOLD, index=fold_i)
   #def toggle_folding

#####################################
class CodeTreeAg:
    """ Agent to build CodeTree for any text and get tree infos
    """
    
    def __init__(self):
        if app.app_api_version()<'1.0.289': return 
        self.did= app.dlg_proc(0, app.DLG_CREATE)
        idc     = app.dlg_proc(self.did, app.DLG_CTL_ADD, "editor")
        app.dlg_proc(self.did, app.DLG_CTL_PROP_SET, index=idc, prop={'name':'ed', 'x': 0, 'y': 0, 'w':100, 'h':100})
        idc     = app.dlg_proc(self.did, app.DLG_CTL_ADD, "treeview")
        app.dlg_proc(self.did, app.DLG_CTL_PROP_SET, index=idc, prop={'name':'tr', 'x':10, 'y':100, 'w':100, 'h':100})
        self.ed = app.Editor(app.dlg_proc(self.did, app.DLG_CTL_HANDLE, name='ed'))
        self.tr =            app.dlg_proc(self.did, app.DLG_CTL_HANDLE, name='tr')
       #def __init__
       
    def parse_text(self, text, lexer=''):
        if app.app_api_version()<'1.0.289': return 
        self.ed.set_text_all(text)
        self.ed.set_prop(app.PROP_LEXER_FILE, lexer)
        ok_scan = self.ed.action(app.EDACTION_LEXER_SCAN, 0)
        ok_fill = self.ed.action(app.EDACTION_CODETREE_FILL, self.tr)
    #   print("tid=",tid,"self.ed=",self.ed,"CODETREE_FILL is",ok)
        nodes = app.tree_proc(self.tr, app.TREE_ITEM_ENUM, 0)
        
       #def parse_text

   #class CodeTreeAg:

if __name__ == '__main__' :     # Tests
    pass
#   Command().show_dlg()    #??
        
#   app.app_log(app.LOG_CONSOLE_CLEAR, 'm')
#   for smk in [smk for smk 
#       in  sys.modules                             if 'cuda_find_in_files.tests.test_fif' in smk]:
#       del sys.modules[smk]        # Avoid old module 
#   import                                              cuda_find_in_files.tests.test_fif
#   import unittest
#   suite = unittest.TestLoader().loadTestsFromModule(  cuda_find_in_files.tests.test_fif)
#   unittest.TextTestRunner(verbosity=0).run(suite)

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
[+][kv-kv][0?apr16] 'Firsts' for walk or for results?
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
[-][kv-kv][12apr17] os.walk is wide or depth? How to switch mode?
[ ][kv-kv][17apr17] ? Use local menu to show presets (after dlg_proc)
[+][kv-kv][28apr17] ReStore user's (x,y) for dlg (after dlg_proc)
[+][kv-kv][03may17] BUG on move in ConfigPreset
[+][kv-kv][03may17] Hide Collect in ConfigPreset and SavePreset
[+][kv-kv][12may17] Use T/F as short form of True/False
[+][kv-kv][15may17] Help and Adjust to move to right+bottom, Close not to relocate, DlgHeight to reduce
[ ][at-kv][19may17] Anchor --- to right
[ ][at-kv][31may17] Live apply changes from opt-dlg
[ ][at-kv][31may17] en=F for PresDlg Up/Dn if sel=0/max
[ ][at-kv][31may17] ? Use pages control for Help
[ ][kv-kv][01jun17] ? Show in Help ref to Issues on GH
[ ][kv-kv][01jun17] ? Add hidden button to find in current file (=Shift+"CurrFold")
[ ][kv-kv][16jun17] Show src ed AFTER set src caret to fragment
[+][kv-kv][10jul17] Save "Find what" value on load preset
[+][kv-kv][12jul17] Esc dont to close dlg while seaching
[ ][kv-kv][13jul17] ? Bold for def-button (as in dlg FindReplace)
[+][at-kv][22aug17] Start folder[s] from current project (cuda_project_man.global_project_info['nodes'])
[+][kv-kv][22aug17] Hint for 'In folder'
[-][kv-kv][22aug17] ? Rename to 'In folder[s]'
[+][kv-kv][08sep17] "Context -1+1"
[ ][kv-kv][14sep17] Save fold before to work
[+][kv-kv][27sep17] ? New "Show in": in dlg editor (footer?)
[+][kv-kv][04oct17] "No files found" if collect_files returns []
[+][at-kv][25oct17] DLG_SCALE
[+][kv-kv][01dec17] Show count of searched files in status (NB for "nothing")
[ ][at-kv][07jan18] Replace: Create backup of modified files
[ ][at-kv][07jan18] Replace: Simulate, don’t actually modify
[ ][at-kv][07jan18] Replace: Prompt and confirm each modification
[ ][at-kv][07feb18] Event on_click_dbl by PROC_SET_EVENTS with lexers
[ ][kv-kv][07feb18] Use pathlib
[?][at-kv][12feb18] "Install" lexer on init
[ ][kv-kv][21feb18] Use ~ to show path in msg/report
[ ][kv-kv][22feb18] Catch report bug - "cut lines"
[+][kv-kv][22feb18] ? Remove Close, set Help under Browse, set Adjust on ----
[+][kv-kv][12mar18] Rebuild help-pic
[ ][kv-kv][12apr18] ? Call app_idle to enable ESC
[+][at-kv][18may18] ? As API-bag "Config presets" blocked checks. re-Try!
[+][at-kv][18may18] Set tab_size to 2 in lexer if no such setting
[+][kv-kv][21may18] Start and second pos of Less is diff
[+][kv-kv][24may18] Add statusbar
[+][kv-kv][04jun18] ? Ctrl+F calls native dialog Find. Ctrl+R calls native dialog Replace
[+][kv-kv][08jun18] Store "in module var" prev Results (a-la in tab)
[+][kv-kv][08jun18] ? Ctrl+S to save a new preset
[ ][kv-kv][09jun18] Skip to control excl and repl vals if fields are hidden (into do_work)
[-][kv-kv][21jun18] ? Src-ed: call open_file (not set_text_all(read))
[+][kv-kv][22jun18] ! Copy rslt to tab
[+][kv-kv][22jun18] Add to history 'what' after start-work
[+][kv-kv][22jun18] Command to point src encoding
[ ][kv-kv][22jun18] ? How to 'jump to next' after Ctrl+Enter from rslt?
[+][kv-kv][25jun18] Save/set line in rslt
[+][at-kv][25jun18] Allow vert/horz layout for Rslt/Src
[ ][kv-kv][25jun18] Opt to gap src sel row from top
[ ][kv-kv][26jun18] Splitter has bad pos after 'over' turn off
[ ][kv-kv][02jul18] Show/Hide rslt after apply preset
[+][kv-kv][02jul18] Set "waiting" after empty found
[+][kv-kv][05jul18] Split search history for session/project
[ ][kv-kv][06jul18] Repeat search by sel in rslt/srcf
[ ][kv-kv][09jul18] Event on_open for *.fif to set markers by (r:c:l)
[+][at-kv][14jul18] Add opt fif_always_not_in_files to section Searching with def val '/.svn /.git /.hg'
[ ][kv-kv][23jul18] ? Why need dlg_h0+=23 at Lin?
[ ][kv-kv][24apr19] Allow menu Layout if [ ]Send. Only "over" item will be unenabled
[ ][kv-kv][15may19] Add encodings into menu over Source
[ ][kv-kv][15may19] ? Add *lexer path* to statusbar when Source by opt "lex-path for lexers: ['']"
[ ][kv-kv][30may19] ? Add *lexer path* to "In files"/"In folder"
[ ][kv-kv][06jun19] Add depth to report: +Search "**" in "**"(+2) 
[ ][kv-kv][06jun19] Allow all tree in Results panel
[+][kv-kv][06jun19] bug: +-context
[ ][kv-kv][06jun19] Add m-datetime for files in report by new opt
[ ][kv-kv][19jun19] FIF4: cells for status: [walked dirs], [reported/matched/tested fns], [reported/found frags] 
[ ][kv-kv][19jun19] FIF4: m-dt of files 
[ ][kv-kv][19jun19] FIF4: lexer path of frags
[ ][kv-kv][19jun19] FIF4: unsaved text of tabs
[ ][kv-kv][19jun19] FIF4: yield based obj chain: report - finder in text - file/tab... - walker
[ ][kv-kv][21jun19] bug! enco_l[enco_n] = enco_s
'''
