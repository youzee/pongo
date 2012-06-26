import socket
import SocketServer
import logging
import select
import pymongo

class PongoServer(SocketServer.TCPServer):
    """TCP server"""
    def __init__(self,settings,*args,**kwargs):
        self.args = settings
        SocketServer.TCPServer.__init__(self,(self.args.listen,self.args.port),*args,**kwargs)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # Some systems doesn't support this
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:
            pass
        self.logger = logging.getLogger("Worker")
        self.db = None
 
    def serve_forever(self, poll_interval=0.5):
        """Serve request while there is no stop instruction from parent process to stop
        
        TODO: remove this method and inmplement per-child threads to shutdown the tcp server.
        """
        while not self.must_stop.value:
            logging.debug("no-stop")
            try:
                r, w, e = select.select([self], [], [], poll_interval)
                if self in r:
                    self._handle_request_noblock()
            except KeyboardInterrupt:
                pass
        self.logger.info("Worker terminating...")

    def connect(self):
        """Connects to the mongo database"""
        try:
            self.db = pymongo.Connection(self.args.host,replicaset=self.args.replicaset)[self.args.database]
            self.logger.info("Succesfully connected to database")
        except Exception,e:
            self.logger.critical("Connection to mongo database failed: %s" % str(e))
