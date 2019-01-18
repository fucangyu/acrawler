import logging
import sched
import time
import traceback

from cronjob.core.registry import Registry
from cronjob.queue import Queue

LOGGER = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, registry, queue):
        self.registry = registry
        self.queue = queue
        self._scheduler = sched.scheduler(time.time, time.sleep)

    @classmethod
    def from_settings(cls):
        return cls(
            registry=Registry.from_settings(),
            queue=Queue.from_settings(),
        )

    def periodic(self, func, job_cls):
        if not job_cls.cancelled:
            interval = job_cls.interval
            self._scheduler.enter(
                interval,
                job_cls.priority,
                self.periodic,
                (func, job_cls),
            )
            if job_cls.right_now:
                func(job_cls)
            else:
                job_cls.right_now = True

    def schedule_all(self):
        LOGGER.info('schedule all...')
        for job_rk in self.registry:
            job_cls = self.registry[job_rk]
            self.periodic(self.schedule, job_cls)

    def schedule(self, job_cls):
        LOGGER.info(f'schedule {job_cls.__name__}')
        # TODO handle enqueue failed
        self.queue.enqueue(job_cls.register_key)

    def _run(self):
        try:
            self.schedule_all()
            self._scheduler.run()
        except Exception:
            LOGGER.error('scheduler error')
            traceback.print_exc()
            time.sleep(1)
        LOGGER.error('scheduler stop')

    def run(self):
        while True:
            self._run()

    def restart(self):
        # TODO
        pass