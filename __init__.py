from .cd_fi_in_fi import Command as CommandRLS
RLS  = CommandRLS()
class Command:
    def show_dlg(self, what='', opts={}):   return RLS.show_dlg(what, opts)
    def nav_to_src_same(self):              return RLS._nav_to_src('same', 'move')
    def nav_to_src_next(self):              return RLS._nav_to_src('next', 'stay')
    def nav_to_src_prev(self):              return RLS._nav_to_src('prev', 'stay')
    def nav_to_src_next_act(self):          return RLS._nav_to_src('next', 'move')
    def nav_to_src_prev_act(self):          return RLS._nav_to_src('prev', 'move')
