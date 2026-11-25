"""Ephemeral frame-count progress and cooperative precommit stopping."""
import math
import time


class RenderStopped(RuntimeError):
    pass


class RenderProgress:
    def __init__(self, plan, report=None, should_stop=None, *, clock=time.monotonic):
        self.frames=tuple(row['frames'] for row in plan)
        if not self.frames or any(type(n) is not int or n<1 for n in self.frames):
            raise ValueError('Invalid render progress frame plan')
        self.total=sum(self.frames)
        self.report=report
        self.should_stop=should_stop
        self.clock=clock
        self.start=clock()
        self.done=set()
        self.count=0
        self.stage=0

    def checkpoint(self):
        if self.should_stop is not None and self.should_stop():
            raise RenderStopped('Studio render stopped at a verified checkpoint before saving candidate')

    def _emit(self, action, *, stop_allowed=True):
        if self.report is None:return
        elapsed=max(0,self.clock()-self.start)
        remaining=None
        if self.stage==0 and len(self.done)>=2 and elapsed>=0.5 and 0<self.count<self.total:
            estimate=elapsed*(self.total-self.count)/self.count
            if math.isfinite(estimate) and estimate<=86400:remaining=round(estimate,1)
        self.report({'action':action,'completed_actions':len(self.done)+self.stage,
                     'action_limit':len(self.frames)+3,'verified_frames':self.count,
                     'total_frames':self.total,'segment_eta_seconds':remaining,
                     'stop_allowed':stop_allowed})

    def begin(self):
        self._emit('studio-render-segments')
        self.checkpoint()

    def segment(self,index):
        if self.stage!=0 or type(index) is not int or not 0<=index<len(self.frames) or index in self.done:
            raise ValueError('Invalid or repeated verified render segment')
        self.done.add(index);self.count+=self.frames[index]
        self._emit('studio-render-segments')
        self.checkpoint()

    def muxed(self):
        if self.stage!=0 or len(self.done)!=len(self.frames):raise ValueError('Incomplete studio segments')
        self.stage=1;self._emit('studio-mux-verified');self.checkpoint()

    def committing(self):
        if self.stage!=1:raise ValueError('Studio mux not verified')
        self.stage=2
        # Publish the non-cancellable state before checking the final stop flag.
        self._emit('studio-commit',stop_allowed=False);self.checkpoint()

    def finished(self):
        if self.stage!=2:raise ValueError('Studio commit not started')
        self.stage=3;self._emit('studio-audit-complete',stop_allowed=False)
