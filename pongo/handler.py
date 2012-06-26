import SocketServer
import logging
import datetime

class MongoException(Exception):
    """Exception raised when there is a communication problem with mongodb"""
    pass


class RequestHandler(SocketServer.StreamRequestHandler):
    """Hnadler for TCP requests coming from Postfix"""
    def handle(self):
        """Handle the request"""
        data = self.rfile.readline().strip()
        response = "400 Unknown error\n"
        try:
            parts = data.split()
            method = parts[0]
            email = parts[1]
            value = None
            if len(parts) > 2:
                value = parts[2]
            assert (method == "get" or method == "put")
        except:
            self.server.logger.warning("Invalid request: %s" % data)
        else:
            if method == "get":
                try:
                    result = self.lookup(email)
                    if result:
                        response = "200 %s\n" % self.server.args.string
                    else:
                        response = "500 Not found\n"
                except MongoException,e:
                    self.server.logger.critical("Error: %s" % str(e))
            elif method == "put":
                try:
                    result = self.insert(email,value)
                    if result:
                        response = "200 %s\n" % "Successfully inserted"
                    else:
                        response = "400 %s\n" % "Insert failed"
                except MongoException,e:
                    self.server.logger.critical("Error: %s" % str(e))
        self.wfile.write(response)
    
    def lookup(self,key):
        """Lookup key in the specified mongo collection"""
        if not self.server.db:
            self.server.connect()
        try:
            count = self.server.db[self.server.args.collection].find({self.server.args.key_field:key}).count()
        except Exception,e:
            self.server.logger.critical("Error querying mongo database: %s" % str(e))
            raise MongoException
        if count > 0:
            self.server.logger.info("Query for %s: found" % key)
            return True
        else:
            self.server.logger.info("Query for %s: not found" % key)
            return False

    def insert(self,key,value):
        """Insert or update key with the specified value in mongo collection."""
        if not self.server.db:
            self.server.connect()
        try:
            #Upsert the new value
            self.server.db[self.server.args.collection].update({self.server.args.key_field:key},{self.server.args.key_field:key,"dateTime":datetime.datetime.now()},True)
            self.server.logger.info("Inserted: %s" % key)
        except Exception,e:
            self.server.logger.critical("Error inserting key %s in mongo database: %s" % (key,str(e)))
            raise MongoException
        return True
