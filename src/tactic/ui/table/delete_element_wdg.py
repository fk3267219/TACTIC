############################################################
#
#    Copyright (c) 2012, Southpaw Technology
#                        All Rights Reserved
#
#    PROPRIETARY INFORMATION.  This software is proprietary to
#    Southpaw Technology, and is not to be reproduced, transmitted,
#    or disclosed in any way without written permission.
#
#


__all__ = ['DeleteElementWdg']

from pyasm.widget import IconWdg

from .button_wdg import ButtonElementWdg

class DeleteElementWdg(ButtonElementWdg):
    ARGS_KEYS = {
    }

    def is_editable(self):
        return False

    def preprocess(self):

        #self.set_option( "icon", "DELETE" )
        #self.set_option( "icon", "BS_REMOVE" )
        self.set_option("icon", "FA_TRASH")
        self.set_option("icon_tip", "Delete")

        # NOTE: not sure why this needs to be in kwargs and not option
        self.kwargs["cbjs_action"] = '''
        var layout = bvr.src_el.getParent(".spt_layout");
        spt.table.set_layout(layout);

        var row = bvr.src_el.getParent(".spt_table_row");
        spt.table.unselect_all_rows();
        spt.table.select_row(row);
        spt.table.delete_selected();
        spt.table.unselect_all_rows();
        '''


    def get_display(self):

        return super(DeleteElementWdg, self).get_display()


