import multiprocessing
import logging
import signal
import time
import os
import sys
import signal
from pongo.server import PongoServer
from pongo.handler import RequestHandler

must_stop = multiprocessing.Value("i",0)


def sig_handler(signal, frame):
    must_stop.value = 1

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)


def serve_forever(server):
    """Entry point for spawned processes"""
    server.must_stop = must_stop
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    pid = multiprocessing.current_process().pid
    server.logger = logging.getLogger("Worker-%d" % pid)
    server.connect()
    server.serve_forever()


class Main(object):
    """Main process class

    Spawns the specified workers and tracks them, creating new ones if they die.

    """
    def __init__(self,args):
        self.args = args
        self.server = PongoServer(args,RequestHandler)
        self.workers = [ self.spawn_worker() for i in range(0,self.args.workers - 1)]

    def spawn_worker(self):
        """Returns a new worker"""
        new_worker = multiprocessing.Process(target=serve_forever,args=(self.server,))
        new_worker.daemon = True
        return new_worker

    def run(self):
        """Main loop method"""
        #Get uid
        if os.getuid() == 0 and not self.args.insecure:
            logging.critical("Running as root. Aborting... (force with -i)")
            sys.exit(1)

        # Create pid file
        try:
            pid_dir = os.path.dirname(self.args.pidfile)
            pid_file = os.path.basename(self.args.pidfile)
            if not os.path.isdir(pid_dir):
                os.mkdir(pid_dir)
            f = open(self.args.pidfile,"w")
            f.write(str(multiprocessing.current_process().pid))
            f.close()
            logging.info("Pid file written to %s" % self.args.pidfile)
        except Exception,e:
            logging.critical("Can't create pid file at %s: %s" % (self.args.pidfile,str(e)))
            sys.exit(1)

        # start workers
        for worker in self.workers:
            worker.start()
           
        while not must_stop.value:
            for worker in self.workers:
               if not worker.is_alive():
                   self.workers.remove(worker)
                   new_worker = self.spawn_worker()
                   new_worker.start()
                   self.workers.append(new_worker)
                   logging.warning("Child process died, replacing with a new one")
            time.sleep(0.5)
        logging.info("Stopping Pongo server")
        for worker in self.workers:
            logging.debug("Joining %s" % worker.pid)
            worker.join()

        # Remove pid file
        try:
            os.remove(self.args.pidfile)
        except Exception,e:
            logging.critical("Can't remove pid file at %s:%s" % (self.args.pidfile,str(e)))
