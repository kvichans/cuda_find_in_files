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