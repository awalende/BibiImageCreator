"""Deprecated module fo connecting to a mysql database without orm."""

import pymysql



class DB_Connector:
    """Connects to an mysql server. (deprecated)"""
    db = None

    def __init__(self, host, db_user, db_pass, database):
        self.db = pymysql.connect(host, db_user, db_pass, database, autocommit=True)

    def queryAndResult(self, query, statement):
        cursor = self.db.cursor()
        execsql = cursor.execute(query, statement)
        #print('SQL Execute code: '+  str(execsql) )
        data = cursor.fetchall()
        return data

