###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['SearchLimitWdg', 'SearchLimitSimpleWdg']

from pyasm.common import Environment
from pyasm.web import WebContainer, Widget, HtmlElement, DivWdg, SpanWdg, Table
from pyasm.widget import HiddenWdg, SubmitWdg, SelectWdg, TextWdg, IconSubmitWdg, IconWdg, SwapDisplayWdg
from tactic.ui.filter import FilterData
from tactic.ui.common import BaseRefreshWdg

from tactic.ui.widget import IconButtonWdg
       
class SearchLimitWdg(Widget):
    DETAIL = "detail_style"
    LESS_DETAIL = "less_detail_style"
    SIMPLE = "simple_style"

    def __init__(self, name='search_limit', label="Showing", limit=None, refresh=True):

        self.search_limit_name = name
        self.label = label
        if limit:
            self.search_limit = int(limit)
        else:
            self.search_limit = None
        self.fixed_offset = False
        self.style = self.DETAIL
        self.prefix = "search_limit"
        self.refresh = refresh
        self.refresh_script = 'spt.dg_table.search_cbk(evt, bvr)'
        if self.refresh:
            self.prev_hidden_name = 'Prev'
            self.next_hidden_name = 'Next'
        else:
            self.prev_hidden_name = '%s_Prev' %self.label
            self.next_hidden_name = '%s_Next' %self.label


        self.chunk_size = 0
        self.chunk_num = 0

        super(SearchLimitWdg, self).__init__()
        
    def init(self):
        self.current_offset = 0
        self.count = None
        #self.text = TextWdg(self.search_limit_name)
        self.text = HiddenWdg(self.search_limit_name)
        self.text.add_style("width: 23px")
        self.text.add_style("margin-bottom: -1px")
        self.text.add_class("spt_search_limit_text")
        self.text.set_persist_on_submit(prefix=self.prefix)

        behavior = {
                'type': 'keydown',
                'cbjs_action': '''
                 if (evt.key=='enter') {
                    // register this as changed item
                    var value = bvr.src_el.value;
                    
                        if (isNaN(value) || value.test(/[\.-]/)) {
                            spt.error('You have to use an integer.');
                        }
                }
        '''}

        self.text.add_behavior(behavior)

        # get the search limit that is passed in
        filter_data = FilterData.get()
        values = filter_data.get_values_by_prefix(self.prefix)
        if not values:
            # check web for embedded table
            web = WebContainer.get_web()
            values = {}
            limit_value = web.get_form_value("search_limit")
            label_value = web.get_form_value(self.label)
            if limit_value:
                values['search_limit'] = limit_value
            if label_value:
                values[self.label] = label_value
        else:
            values = values[0]


        self.values2 = filter_data.get_values_by_prefix("search_limit_simple")
        if not len(self.values2):
            self.values2 = {}
        elif len(self.values2) == 2:
            if self.values2[0]['page']:
                self.values2 = self.values2[0]
            else:
                self.values2 = self.values2[1]
        else:
            self.values2 = self.values2[0]


        self.stated_search_limit = values.get("search_limit")
        """
        if not self.stated_search_limit:
            self.stated_search_limit = values.get("limit_select")
        if not self.stated_search_limit:
            self.stated_search_limit = values.get("custom_limit")
        """
        if self.stated_search_limit:
            self.stated_search_limit = int(self.stated_search_limit)
        else:
            self.stated_search_limit = 0
      
        # reused for alter_search() later
        self.values = values
       
    def set_refresh_script(self, script):
        self.refresh_script = script

    def set_label(self, label):
        self.label = label

    def get_limit(self):
        return self.search_limit

    def get_stated_limit(self):
        return self.stated_search_limit


    def get_count(self):
        return self.count


    def set_limit(self, limit):
        self.search_limit = limit
        # this is user defined, should be set in init() instead
        #self.stated_search_limit = limit
 

    def set_offset(self, offset):
        self.fixed_offset = True
        self.current_offset = offset


    def set_style(self, style):
        self.style = style


    def set_chunk(self, chunk_size, chunk_num, limit=None):
        self.chunk_size = chunk_size
        self.chunk_num = chunk_num
        if limit:
            self.search_limit = limit
        else:
            # avoid undefined chunk_size
            if chunk_size:
                self.search_limit = chunk_size

        # to avoid 0 limit on undefined search limit in fast table
        if self.search_limit == 0:
            self.search_limit = 50
        

    def alter_search(self, search):
        if not search:
            return
        self.set_search(search)
        security = Environment.get_security()
        # allow security to alter the search
        security.alter_search(search)
        search.set_security_filter()

        self.count = search.get_count()

        web = WebContainer.get_web()

        values = self.values

        # look at the stated search limit only if there is no chunk_size
        if not self.chunk_size:
            search_limit = self.stated_search_limit
            if search_limit and self.search_limit != -1:
                try:
                    self.search_limit = int(search_limit)
                except ValueError:
                    self.search_limit = 20
                if self.search_limit <= 0:
                    self.search_limit = 1
            elif self.search_limit:
                # this usually happens with search_limit set in side bar or kwarg for TableLayoutWdg
                pass
            else:
                # for backward compatibility with the default chunk size of 100
                self.search_limit = 100

        
        # find out what the last offset was
        #last_search_offset = web.get_form_value("last_search_offset")
        last_search_offset = values.get("%s_last_search_offset"%self.label)
        if last_search_offset:
            last_search_offset = int(last_search_offset)
        else:
            last_search_offset = 0
        # based on the action, set the new offset
        #if web.get_form_value("Next"):
        # FIXME: Next Prev not working for embedded tables yet


        # look at various values to change the search criteria
        page = self.values2.get("page")
        if page:
            current_offset = self.search_limit * (int(page)-1)

        elif values.get("Next"):
            current_offset = last_search_offset + self.search_limit
            if current_offset >= self.count:
                current_offset = 0

        #elif web.get_form_value("Prev"):
        elif values.get("Prev"):
            current_offset = last_search_offset - self.search_limit
            if current_offset < 0:
                current_offset = int(self.count/self.search_limit) * self.search_limit




      
        # this happens when the user jumps from Page 3 of a tab to a tab that
        # doesn't really need this widget
        elif last_search_offset > self.count:
            current_offset = 0
        elif values.get(self.label):
            value = values.get(self.label)
            if not value.startswith("+"):
                current_offset, tmp = value.split(" - ")
                current_offset = int(current_offset) - 1
            else:
                current_offset = 0
        else:
            current_offset = 0 

        if self.fixed_offset == False:
            self.current_offset = current_offset


        # add ability to break search limit search into chunks
        self.current_offset = self.current_offset

        if self.chunk_num:
            self.current_offset = last_search_offset + (self.chunk_num*self.chunk_size)
      
       
        if self.search_limit >= 0:
            self.search.set_limit(self.search_limit)
        self.search.set_offset(self.current_offset)


    def get_info(self):

        return {
            "count": self.count,
            "current_offset": self.current_offset,
            "search_limit": self.search_limit,
        }



    def get_display(self):

        web = WebContainer.get_web()

        widget = DivWdg()
        widget.add_class("spt_search_limit_top")
        widget.add_color("background", "background")
        widget.add_color("color", "color")

        hidden = HiddenWdg("prefix", self.prefix)
        widget.add(hidden)

   
        if not self.search and not self.sobjects:
            widget.add("No search or sobjects found")
            return widget

        # self.count should have been set in alter_search()
        # which can be called explicitly thru this instance, self.
        if not self.count:
            self.count = self.search.get_count(no_exception=True)
        
        # if self.sobjects exist thru inheriting from parent widgets
        # or explicitly set, (this is not mandatory though)
        if self.sobjects and len(self.sobjects) < self.search_limit:
            limit = len(self.sobjects)
        elif self.search_limit and self.count < self.search_limit:
            # this is only true if the total result of the search is 
            # less than the limit and so this wdg will not display
            limit = self.count
        else:
            limit = self.search_limit

        if not limit:
            limit = 50
            self.search_limit = limit

    
        if self.refresh: 
            prev = SpanWdg( IconButtonWdg(title="Prev", icon="FA_CHEVRON_LEFT") )
            prev.add_style("margin-left: 8px")
            prev.add_style("margin-right: 6px")
            prev.add_style("margin-top: 5px")
            hidden_name = self.prev_hidden_name
            hidden = HiddenWdg(hidden_name, "")
            prev.add(hidden)

            prev.add_behavior( {
                'type': 'click_up',
                'cbjs_action': " bvr.src_el.getElement('input[name=%s]').value ='Prev';%s"\
                    % (hidden_name, self.refresh_script)
            } )

            next = SpanWdg( IconButtonWdg(title="Next", icon="FA_CHEVRON_RIGHT" ) )
            next.add_style("margin-left: 6px")
            next.add_style("margin-top: 5px")
            hidden_name = self.next_hidden_name
            hidden = HiddenWdg(hidden_name, "")
            next.add(hidden)

            next.add_behavior( {
                'type': 'click_up',
                'cbjs_action': " bvr.src_el.getElement('input[name=%s]').value ='Next';%s"\
                    % (hidden_name, self.refresh_script)
            } )

            prev.add_style("float: left")
            next.add_style("float: left")

        else: # the old code pre 2.5
            prev = IconButtonWdg(title="Prev", icon="FA_CHEVRON_LEFT" )
            hidden_name = self.prev_hidden_name
            hidden = HiddenWdg(hidden_name,"")
            prev.add(hidden)
            prev.add_event('onclick'," spt.api.Utility.get_input(document,'%s').value ='Prev';%s"\
                    %(hidden_name, self.refresh_script))
            next = IconButtonWdg(title="Next", icon="FA_CHEVRON_RIGHT" )
            hidden_name = self.next_hidden_name
            hidden = HiddenWdg(hidden_name,"")
            next.add(hidden)
            next.add_event('onclick',"spt.api.Utility.get_input(document,'%s').value ='Next';%s" \
                    %(hidden_name, self.refresh_script))


        showing_wdg = DivWdg()
        widget.add(showing_wdg)
        showing_wdg.add_style("padding: 20px")
        #showing_wdg.add_style("margin: 10px")
        showing_wdg.add_style("border-top: solid 1px %s" % showing_wdg.get_color("border"))
        showing_wdg.add_color("background", "background", -5)
        #showing_wdg.add_border()

        label_span = SpanWdg("Showing: ")
        showing_wdg.add(label_span)

        range_wdg = DivWdg()
        showing_wdg.add(range_wdg)
        range_wdg.add_style("display: flex")
        range_wdg.add_style("justify-content: space-around")
        range_wdg.add_style("margin: 20px 10px")

        range_wdg.add( prev )
       

        # this min calculation is used so that if self.sobjects is not set
        # above for the calculation of the limit, which will make the last 
        # set of range numbers too big
        
        left_bound = self.current_offset+1
        if not limit:
            # prevent error in ItemsNavigatorWdg if a search encounters query error
            limit = 50
            self.search_limit = limit

        right_bound = min(self.current_offset+limit, self.count)
        if left_bound > right_bound:
            left_bound = 1
        current_value = "%d - %d" % (left_bound, right_bound)

        if self.style == self.SIMPLE:
            range_wdg.add( current_value )
        else:
            # add a range selector using ItemsNavigatorWdg
            from pyasm.widget import ItemsNavigatorWdg
            selector = ItemsNavigatorWdg(self.label, self.count, self.search_limit)
            selector.select.add_behavior( {
                'type': 'change',
                'cbjs_action': self.refresh_script
            } )

            selector.set_style(self.style)
            selector.select.add_style("width: 100px")
            #selector.add_style("display: inline")
            selector.add_style("float: left")
            selector.add_style("text-align: center")
            selector.add_style("text-align-last: center")

            selector.set_value(current_value)
            selector.set_display_label(False)

            range_wdg.add( selector) 

        range_wdg.add( next )




        #showing_wdg.add( " x ")
        showing_wdg.add(self.text)
        self.text.add_style("margin-top: -3px")
        self.text.set_attr("size", "1")
        self.text.add_attr("title", "Set number of items per page")


        # set the limit
        set_limit_wdg = self.get_set_limit_wdg()
        widget.add(set_limit_wdg)


        from tactic.ui.widget.button_new_wdg import ActionButtonWdg
        button = ActionButtonWdg(title='Search')
        widget.add(button)
        button.add_style("float: right")
        button.add_style("margin-top: 8px")
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''
            var top = bvr.src_el.getParent(".spt_search_limit_top");
            var select = top.getElement(".spt_search_limit_select");
            var value = select.value;
            if (value == 'Custom') {
                custom = top.getElement(".spt_search_limit_custom_text");
                value = custom.value;
            }
            if (value == '') {
                value = 20;
            }
            var text = top.getElement(".spt_search_limit_text");
            text.value = value;

            spt.dg_table.search_cbk({}, bvr) 
            '''
        } )


        offset_wdg = HiddenWdg("%s_last_search_offset" %self.label)
        offset_wdg.set_value(self.current_offset)
        widget.add(offset_wdg)

        widget.add("<br clear='all'/>")
 
        return widget


    def get_set_limit_wdg(self):
        limit_content = DivWdg()
        limit_content.add_style("font-size: 10px")
        limit_content.add_style("padding", "15px")
        #limit_content.add_border()

        limit_content.add("Show ")

        limit_select = SelectWdg("limit_select")
        limit_select.add_class("spt_search_limit_select")
        limit_select.set_option("values", "10|20|50|100|200|Custom")
        limit_select.add_style("font-size: 10px")
        limit_content.add(limit_select)
        limit_content.add(" items per page<br/>")

        if self.search_limit in [10,20,50,100,200]:
            limit_select.set_value(self.search_limit)
            is_custom = False
        else:
            limit_select.set_value("Custom")
            is_custom = True

        limit_select.add_behavior( {
            'type': 'change',
            'cbjs_action': '''
            var top = bvr.src_el.getParent(".spt_search_limit_top");
            var value = bvr.src_el.value;
            var custom = top.getElement(".spt_search_limit_custom");
            if (value == 'Custom') {
                custom.setStyle("display", "");
            }
            else {
                custom.setStyle("display", "none");
            }

            '''
        } )


        custom_limit = DivWdg()
        limit_content.add(custom_limit)
        custom_limit.add_class("spt_search_limit_custom")
        custom_limit.add("<br/>Custom: ")
        text = TextWdg("custom_limit")
        text.add_class("spt_search_limit_custom_text")
        text.add_style("width: 50px")
        if not is_custom:
            custom_limit.add_style("display: none")
        else:
            text.set_value(self.search_limit)
        custom_limit.add(text)
        text.add(" items")
        behavior = {
                'type': 'keydown',
                'cbjs_action': '''
                 if (evt.key=='enter') {
                    // register this as changed item
                    var value = bvr.src_el.value;
                    if (isNaN(value) || value.test(/[\.-]/)) {
                        spt.error('You have to use an integer.');
                    }
                }
        '''}

        
        text.add_behavior(behavior)

        return limit_content


class SearchLimitSimpleWdg(BaseRefreshWdg):

    def alter_search(self, search):
        pass



    def get_display(self):
        top = self.top
        self.set_as_panel(top)
        top.set_unique_id()
        top.add_class("spt_search_limit_top")



        # this info comes from the SearchLimit above (function get_info() )
        count = self.kwargs.get("count")
        if count == 0:
            return top

        search_limit = self.kwargs.get("search_limit")
        # account for cases where this shouldn't even be called in a non search scenario
        if not search_limit:
            search_limit = 100
        current_offset = self.kwargs.get("current_offset")

        num_pages = int( float(count-1) / float(search_limit) ) + 1
        current_page = int (float(current_offset) / count * num_pages) + 1

        # show even if there is only a single page
        #if num_pages == 1:
        #    return top

        #print("current: ", current_offset)
        #print("search_limit: ", search_limit)
        #print("current_page: ", current_page)

        table = Table()
        table.add_style("float: right")
        top.add(table)

        
        top.add_color("background", "background", -2)
        top.add_color("color", "color3")
        #top.add_style("margin: 0px 0px 10px 0px")
        #top.add_border(color="table_border")
        top.add_style("padding-right: 30px")
        top.add_style("padding-left: 8px")
        top.add_style("padding-top: 5px")
        top.add_style("padding-bottom: 8px")
        top.add_style("position: relative")

        showing_div = DivWdg()
        showing_div.add_style("padding: 5px")
        top.add(showing_div)
        start_count = current_offset + 1
        end_count = current_offset + search_limit

        if end_count > count:
            end_count = count

        total_count = count
        bgcolor = top.get_color("background", -2)
        bgcolor2 = top.get_color("background", 10)
        
        showing_div.add_color('background', bgcolor)
        showing_div.add_color('color', 'color')

        if num_pages > 1:
            showing_div.add("Showing &nbsp; %s - %s &nbsp; of &nbsp; %s" % (start_count, end_count, total_count))
        else:
            showing_div.add("Showing &nbsp; %s - %s &nbsp; of &nbsp; %s" % (start_count, count, count))
            return top


        table.add_row()


        top.add_smart_style("spt_link", "padding", "5px 10px 5px 10px")
        top.add_smart_style("spt_link", "margin", "0px 5px 0px 5x")
        top.add_smart_style("spt_link", "cursor", "pointer")
        #top.add_smart_style("spt_link", "border", "solid 1px blue")

        top.add_smart_style("spt_no_link", "padding", "5px 10px 5px 10px")
        top.add_smart_style("spt_no_link", "margin", "0px 5px 0px 5x")
        top.add_smart_style("spt_no_link", "opacity", "0.5")
        top.add_smart_style("spt_no_link", "font-style", "italic")


        top.add_relay_behavior( {
            'type': 'mouseup',
            'search_limit': search_limit,
            'limit': search_limit,
            'current_page': current_page,
            'num_pages': num_pages,
            'bvr_match_class': 'spt_link',
            'cbjs_action': '''

            var top = bvr.src_el.getParent(".spt_search_limit_top");
            var page_el = top.getElement(".spt_page");

            var layout = bvr.src_el.getParent(".spt_layout");
            spt.table.set_layout(layout);

            var value = bvr.src_el.getAttribute("spt_page");
            if (value == 'next') {
                value = bvr.current_page + 1;
                if ( value < 1 ) value = 1;
            }
            else if (value == 'prev') {
                value = bvr.current_page - 1;
                if ( value > bvr.num_pages ) value = bvr.num_pages;
            }
            page_el.value = value;


            // remap the bvr.src_el
            var tableTop = bvr.src_el.getParent('.spt_table_top');
            var tableSearch = tableTop.getElement(".spt_table_search");
            var hidden_el = tableSearch.getElement(".spt_text_value");

            bvr.src_el = tableSearch.getElement(".spt_text_input_wdg");
            bvr.src_el.setAttribute("spt_input_value", bvr.src_el.value);
            hidden_el.setAttribute("spt_input_value", bvr.src_el.value);
            hidden_el.value = bvr.src_el.value;

            spt.dg_table.search_cbk({}, {src_el: bvr.src_el});
            return;



            // NOTE: below doesn't work just yet because search_cbk, which calls
            // replace_inner_html deactivates all of the behaviors.  We need a flag
            // that can disable the deactivation of behaviors

            var layout_top = layout.getParent(".spt_layout_top");

            var pages = layout_top.pages;
            if (!pages) {
                pages = {};
                layout_top.pages = pages;
            }


            
            var children = bvr.src_el.getChildren();
            layout_top.pages[bvr.current_page] = children;



            var html = pages[value];
            if (!html) {
                spt.dg_table.search_cbk(evt, bvr);
            }
            else {
                bvr.src_el.innerHTML = "";
                html.forEach( function(child) {
                    bvr.src_el.appendChild(child);
                } );
        
            }
 
            '''
        } )


        top.add_relay_behavior( {
            'type': 'mouseover',
            'bgcolor': bgcolor2,
            'bvr_match_class': 'spt_link',
            'cbjs_action': '''
            bvr.src_el.setStyle("background", bvr.bgcolor);
            '''
        } )
        top.add_relay_behavior( {
            'type': 'mouseout',
            'bgcolor': bgcolor,
            'bvr_match_class': 'spt_link',
            'cbjs_action': '''
            if (!bvr.src_el.hasClass('spt_current_page'))
                bvr.src_el.setStyle("background", bvr.bgcolor);
            '''
        } )



        top.add_class("spt_table_search")
        hidden = HiddenWdg("prefix", "search_limit_simple")
        top.add(hidden)

        hidden = HiddenWdg("page", "")
        hidden.add_class("spt_page")
        top.add(hidden)


        td = table.add_cell()
        left = "< Prev"
        td.add(left)
        if current_page > 1:
            td.add_class("spt_link")
        else:
            td.add_class("spt_no_link")

        td.add_attr("spt_page", "prev")

        # find the range ... always show 10 pages max
        start_page = current_page - 5
        if start_page < 1:
            start_page = 1


        if start_page + 9 <= num_pages:
            end_page = start_page + 10 - 1
        elif start_page > 5:
            end_page = current_page + 5
        else:
            end_page = num_pages
            start_page = 1

        # if end_pages for whatever reason, exceeds num_pages, limit it
        if end_page > num_pages:
            end_page = num_pages

        # if for whatever reason, end_page - 10 > 1, then limit it
        if end_page == num_pages and end_page - 10 > 1:
            start_page = end_page - 10

       
        for i in range(start_page, end_page + 1):
            td = table.add_cell()
            td.add(i)
            td.add_class("spt_link")
            td.add_attr("spt_page", i)
            if i == current_page:
                td.add_color("color", "color")
                td.add_class("spt_current_page")
                td.add_color("background", "background", 10)
                td.add_color("border-color", "border")
                td.add_style("border-width", "0px 1px 0px 1px")
                td.add_style("border-style", "solid")


        td = table.add_cell()
        right = "Next >"
        td.add(right)
        if current_page < num_pages:
            td.add_class("spt_link")
        else:
            td.add_class("spt_no_link")
        td.add_attr("spt_page", "next")




        return top









