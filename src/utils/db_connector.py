import pymysql

'''
Connects to the standard mysql database
'''


class DB_Connector:

    db = None

    def __init__(self, host, db_user, db_pass, database):
        self.db = pymysql.connect(host, db_user, db_pass, database)

    def queryAndResult(self, query, statement):
        cursor = self.db.cursor()
        cursor.execute(query, statement)
        data = cursor.fetchall()
        return data

