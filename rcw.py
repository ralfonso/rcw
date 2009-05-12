#!/usr/bin/python

from __future__ import division # this makes the division operator always return a float
import gtk
import pango
import cairo
from optparse import OptionParser

MAX_FONTSIZE = 40
MIN_FONTSIZE = 7

class RCW(object):
    def __init__(self,options):
        self.options = options
        self.window = gtk.Window()

        self.window.connect("delete_event", self.delete_event)
        self.window.connect('expose-event', self.expose)
        self.window.connect('screen-changed', self.screen_changed)
        self.window.set_resizable(False)

        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_app_paintable(True)

        try:
            self.bg_rgb = gtk.gdk.color_parse(self.options.bgcolor)
        except ValueError:
            if options.debug:
                print "DEBUG: unable to parse bgcolor name"
            self.bg_rgb = gtk.gdk.color_parse('#000000')

        self.bg_color_rgb = (float(self.bg_rgb.red)/256/256, float(self.bg_rgb.green)/256/256, float(self.bg_rgb.blue)/256/256)
        self.window.modify_bg(gtk.STATE_NORMAL,self.bg_rgb)

        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        self.entry = CalcEntry('0123456789+-/*. ()',max=100)
        self.entry.set_width_chars(10)
        self.entry.connect("activate", self.enter_callback, self.entry)
        self.entry.set_has_frame(False)
        self.vbox.pack_start(self.entry,expand=False,fill=False)

        self.label = gtk.Label()
        self.label.set_use_markup(True)
        self.font_desc = pango.FontDescription("%s %s" % (self.options.font,MAX_FONTSIZE))
        markup = '<span font_desc="%s" color="%s">%s</span>' % (self.font_desc,self.options.text_color,0)
        self.label.set_markup(markup)
        self.label.set_alignment(0.5,0.5)
        self.label.set_justify(gtk.JUSTIFY_CENTER)

        # we have to put the label in an event box in case we want to trap events
        self.ebox = gtk.EventBox()         
        self.ebox.set_visible_window(False)
        self.ebox.add(self.label)
        self.vbox.pack_start(self.ebox,expand=True,padding=5)

        self.screen_changed(self.window)

        if self.options.stick:
            self.window.stick()
        self.window.set_border_width(2)

    def expose(self, widget, event=None):
        # signal handler for expose. called every time the window needs to be redrawn. with alpha!

        cr = self.window.window.cairo_create()
        if self.window.is_composited() == True and self.options.opacity < 100:
            cr.set_source_rgba(self.bg_color_rgb[0], self.bg_color_rgb[1],
                               self.bg_color_rgb[2], float(self.options.opacity)/100) # Transparent
            # Draw the background
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()

        return False

    def show(self):
        self.window.show_all()
        self.width,self.height = self.window.get_size()
        self.window.set_geometry_hints(None,min_height=self.height)

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def screen_changed(self, widget, old_screen=None):
        screen = widget.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap == None:
            colormap = screen.get_rgb_colormap()

        widget.set_colormap(colormap)
        return False

    def enter_callback(self,widget,entry):
        # signal handler for when the user presses enter

        text = entry.get_text()
        try:
            # we can run eval() here because user input can ALWAYS be trusted, right?  right?
            result = eval(text)
        except SyntaxError:
            return

        # get a pango context for the label and test the size for the new result
        # if it's too wide for the window, continue to make the font smaller until it fits
        context = self.label.get_pango_context()
        layout = pango.Layout(context)

        for point_size in reversed(range(MIN_FONTSIZE,MAX_FONTSIZE+1)):
            self.font_desc.set_size(point_size * pango.SCALE)

            markup = '<span font_desc="%s" color="%s">%s</span>' % (self.font_desc,self.options.text_color,result)
            layout.set_markup(markup)
            width,height = layout.get_pixel_size()
            if float(width) * 1.2 <= self.width:
                break

        self.label.set_markup(markup)

        #always highlight the entire expression after the user presses enter
        self.entry.select_region(0,-1)

class CalcEntry(gtk.Entry):
    def __init__(self, allowed_chars,**kwargs):
        gtk.Entry.__init__(self,**kwargs)
        self.allowed_chars = allowed_chars
        self.connect("changed", self.check_char, None)

    def check_char(self, widget, string, *args):
        #signal handler for any sort of input. due to X11 pasting, we have to check the entire expression every time

        for pos,char in enumerate(widget.get_chars(0,-1)):
            if char not in self.allowed_chars:
                widget.select_region(pos, pos + 1)
                widget.delete_selection()

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    parser.add_option('-f','--font',dest='font',
                      help="select the font to use for the display. ex: 'bitstream vera sans','monospace','sans'",
                      default="sans")
                          
    parser.add_option('--bgcolor',dest='bgcolor',default='#050050',
                          help='set the background color')
    parser.add_option('--color',dest='text_color',default='white',                          
                          help='set the text color')
    parser.add_option('-o','--opacity',dest='opacity',type="int",default=100,
                          help='set the opacity between 0 and 100')
    parser.add_option('-d', "--debug", dest="debug",action="store_true",
                          help="print extra info",default=False)
    parser.add_option('-s','--stick',dest='stick',action='store_true',default=False,
                          help='make window sticky (display on all desktops)')

    (options, args) = parser.parse_args()

    rcw = RCW(options)
    gtk.gdk.error_trap_push()

    #dname.position()
    rcw.show()
    gtk.main()  

if __name__ == '__main__':
    main()