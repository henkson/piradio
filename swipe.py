import pygame
from time import *
import colors
# from pygame import *

__author__ = 'jeroen'


class SwipePane:
    mouse_down_stop_threshold = 10  # pixels

    def __init__(self,
                 browser,         # Browser
                 init_rect,
                 pane=None):
        self.browser = browser
        self.world_size = browser.get_size()
        self.view_port = init_rect
        self.pane = pane

        self.scrolling = False
        self.dirty = True
        self.offset = [0,0]

        self.click = None  # user event

        self.start_scroll = None
        self.start_mousedown = None

        self.scroll_rect = pygame.Rect(0,0,browser.scroll_width,240)

    def update(self, event):  # event must not be None
        """ Called by user with mouse events. event must not be none. """

        # 1. Basic idea of scrolling:
        # 1a. on mousebutton DOWN, we start "scrolling"
        # 1b. on mouse MOTION, if we are "scrolling", we scroll the screen
        # 1c. on mousebutton UP, we stop "scrolling"
        #
        # 2. But how do we decide (on mousebutton UP) that the user has clicked (and not scrolled)?
        # 2a. on mousebutton DOWN, we store the "start_mousedown" position
        # 2b. on mouse MOTION, if we have moved more than self.mouse_down_stop_threshold pixels (in either direction), we clear the "start_mousedown" position
        # 2c. on mousebutton UP, if the "start_mousedown" position is not cleared, we were not scrolling but clicking
        #
        # 3. But the PiTFT screen is not really accurate, while swiping we get several mouse-up, -down, -motion events
        # We should decide to accept the "click" only if no new event has occured after event_start_threshold milliseconds
        # 3a. on mousebutton UP, we create a click-USEREVENT holding
        #   - start_time: the timestamp on which the event must be executed (time() + threshold),
        #   - the current mouse position
        #   - the current swipe panel offset
        # 3b. on mousebutton DOWN and on mouse MOTION, we cancel the click-USEREVENT
        #
        # 4. Handle the click-USEREVENT:
        # 4a. if the event was disactivated: do nothing
        # 4b. otherwise, if the current time has passed the start_time of the event: pass the event to the Browser
        # 4c. otherwise: reschedule the event

        if event.type is pygame.MOUSEBUTTONDOWN:
            # 1a. scrolling has started
            self.scrolling = True
            # 2a. store start_mousedown
            self.start_mousedown = event.pos
            # 3b. cancel click-event (if any)
            self.cancel_click()
        elif event.type is pygame.MOUSEMOTION and self.scrolling:
            # 1b. do scroll!
            self.scroll(event.rel)
            # 2b. check if the start_mousedown needs to be cleared
            if self.start_mousedown \
                    and (abs(self.start_mousedown[0] - event.pos[0]) > self.mouse_down_stop_threshold
                         or abs(self.start_mousedown[1] - event.pos[1]) > self.mouse_down_stop_threshold):
                self.start_mousedown = None
            # 3b. cancel click-event (if any)
            self.cancel_click()
        elif event.type is pygame.MOUSEBUTTONUP:
            # 1c. scrolling should stop
            self.scrolling = False

            # 2c. check start_mousedown: if not cleared, we are clicking
            if self.start_mousedown:
                self.start_mousedown = None

                # 3a. create a click event
                if not self.click:  # shouldn't this always be True??
                    pygame.event.post(self.create_click_event(event.pos).event)
        elif event.type is pygame.USEREVENT and event.click:
            if not event.click.active:
                # 4a. event was disactivated
                pass  # do nothing
            elif time() >= event.start_time:
                # 4b. event ready to be processed!
                print "exec event after " + str(event.click.nb) + " reposts"
                self.click = None
                self.browser.update(event, self.offset)
            else:
                # 4c. event not ready to be executed, re-post
                event.click.nb += 1
                pygame.event.post(event)

    def create_click_event(self, pos):
        self.click = self.ClickEvent(pos, self.offset)
        return self.click

    def cancel_click(self):
        if self.click and self.click.active:
            self.click.active = False  # disactivate event
            self.click = None

    def scroll(self, rel):
        self._update_offset(rel, 0)
        self._update_offset(rel, 1)
        self.dirty = True

    def _update_offset(self, rel, xy):
        """set self.offset, limited to self.world_size and self.view_port.size"""
        self.offset[xy] = max(self.offset[xy] - rel[xy], 0)
        self.offset[xy] = min(self.offset[xy], self.world_size[xy] - self.view_port.size[xy])

    def draw(self, surface):
        """ Called by end user to draw state to the surface """
        result = []
        if self.dirty:

            # result.append()
            result.append(surface.blit(self.browser.get_view(),
                                       self.view_port.topleft,
                                       (self.offset, self.view_port.size)))
        return result

    # inner class
    class ClickEvent:
        event_start_threshold = 0.2     # seconds

        def __init__(self, pos, offset):
            self.event = pygame.event.Event(pygame.USEREVENT,
                                            start_time=time() + self.event_start_threshold,
                                            pos=pos,
                                            offset=[offset[0], offset[1]],
                                            click=self)
            self.active = True
            self.nb = 1

    def update_original(self, event):  # event must not be None
        """ Called by user with mouse events. event must not be none. """
        if event.type is pygame.MOUSEMOTION and self.scrolling:
            self.scroll(event.rel)
        elif event.type is pygame.MOUSEBUTTONDOWN:
            self.scrolling = True
        elif event.type is pygame.MOUSEBUTTONUP:
            self.scrolling = False

    def update_1(self, event):  # event must not be None
        """ Called by user with mouse events. event must not be none. """
        if event.type is pygame.MOUSEMOTION and self.scrolling:
            self.scroll((event.pos[0] - self.start_scroll[0], event.pos[1] - self.start_scroll[1]))
            self.start_scroll = event.pos
            if self.start_mousedown \
                    and (abs(self.start_mousedown[0] - event.pos[0]) > self.mouse_down_stop_threshold
                         or abs(self.start_mousedown[1] - event.pos[1]) > self.mouse_down_stop_threshold):
                # more than 10px diff: we are _really_ scrolling now, i.e. _not_ just pushing a button
                self.start_mousedown = None
        elif event.type is pygame.MOUSEBUTTONDOWN:
            print "DOWN " + str(event.pos)
            self.start_mousedown = event.pos
            self.start_scroll = event.pos
            self.scrolling = True
        elif event.type is pygame.MOUSEBUTTONUP:
            print "UP   " + str(event.pos)
            self.start_scroll = None
            self.scrolling = False
            if self.start_mousedown:
                # start_mousedown has not been cleared by a MOUSEMOTION event, i.e. we were pushing a button
                self.browser.update(event, self.offset)
