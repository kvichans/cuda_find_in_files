from .cd_fi_in_fi import Command as CommandRLS
RLS  = CommandRLS()
class Command:
    def show_dlg(self, what='', opts={}):   return RLS.show_dlg(what, opts)
    def find_in_ed(self):                   return RLS.find_in_ed()
    def find_in_tabs(self):                 return RLS.find_in_tabs()
    def repeat_find_by_rpt(self):           return RLS.repeat_find_by_rpt()
#   def undo_by_report(self):               return RLS.undo_by_report()
    def nav_to_src_same(self):              return RLS._nav_to_src('same', 'move')
    def nav_to_src_next(self):              return RLS._nav_to_src('next', 'stay')
    def nav_to_src_prev(self):              return RLS._nav_to_src('prev', 'stay')
    def nav_to_src_next_act(self):          return RLS._nav_to_src('next', 'move')
    def nav_to_src_prev_act(self):          return RLS._nav_to_src('prev', 'move')
    def jump_to_next_rslt(self):            return RLS._jump_to('next', 'rslt')
    def jump_to_prev_rslt(self):            return RLS._jump_to('prev', 'rslt')
    def jump_to_next_file(self):            return RLS._jump_to('next', 'file')
    def jump_to_prev_fold(self):            return RLS._jump_to('next', 'fold')

    def on_goto_def(self, ed_self):         return RLS.on_goto_def(ed_self)
    
def show_dlg(what='', opts={}):
    """ Show dlg "Find in Files" and set field values.
        Params              Dlg field           Type            Comment
            what            'Find'              str
            opts['repl']    'Replace with'      str
            opts['reex']    '.*'                ('0','1')
            opts['case']    'aA'                ('0','1')
            opts['word']    '"w"'               ('0','1')
            opts['incl']    'In files'          str             '<Open Files>'-in tabs
            opts['excl']    'Not in files'      str
            opts['fold']    'In folder'         str
            opts['dept']    'In subfolders'     (0..6)          0-all, 1-folder only , 2-with 1-level, ..., 6-with 5-level
            opts['cllc']    'Collect'           ('0'..'2')      0-match, 1-count, 2-names
            opts['join']    'Append results'    ('0','1')
            opts['totb']    'Show in'           ('0','1')       0-new tab, 1-prev tab
            opts['shtp']    'Tree type'         ('0'..'7')      0-path(r):line, 1-path(r:c:l):line, 2-path/(r):line, 3-path/(r:c:l):line, 4-dir/file(r):line, 5-dir/file(r:c:l):line, 6-dir/file/(r):line, 7-dir/file/(r:c:l):line
            opts['cntx']    'Context'           ('0','1')
            opts['algn']    'Align'             ('0','1')
            opts['skip']    'Skip files'        ('0'..'3')      0-"Don't skip", 1-'Hidden', 2-'Binary', 3-'Hidden, Binary'
            opts['sort']    'Sort file list'    ('0'..'2')      0-"Don't sort", 1-'By date, from newest', 2-'By date, from oldest'
            opts['frst']    'Firsts (0=all)'    ('0', 'N')      0-all, N-only N files
            opts['enco']    'Encodings'         ('0'..'8')      0-'os, utf8, <det>', 1-'utf8, os, <det>', 2-'os, <det>', 3-'utf8, <det>', 4-'os, utf8', 5-'utf8, os', 6-'os', 7-'utf8', 8-'<det>'
        Hidden params
            All implicit options will be restored from states in prev dlg usage
        Example 
            show_dlg(   what = 'Text to find'
            ,opts=dict( repl = 'Text to replace'
                       ,incl = '*'             # in all files
                       ,fold = 'c:\\'          # start folder
                       ,dept = 0               # with all subfolders
            ))
            
    """
    return RLS.show_dlg(what, opts)