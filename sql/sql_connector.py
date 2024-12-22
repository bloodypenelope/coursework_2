"""Module that provides functionality for work with temperature database"""
from mysql.connector import connect, Error
import numpy as np


class DBConnectionError(Error):
    """
    Raises whenever connection to the MySQL server failed
    """


class QuerySyntaxError(Error):
    """
    Raises when given query has syntax errors
    """


class MonitorSQLConnector:
    """
        Class which allows to retrieve data from temperature\
            monitoring system

        Args:
            info (tuple[str]): Information needed to connect to the database\
                in order -> (host, port, user, password, database)
    """

    def __init__(self, info: tuple[str]) -> None:
        self.sensors = [1000, 2000, 2300, 2600]
        host, port, user, password, database = info

        try:
            self.connection = connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
        except Error as e:
            raise DBConnectionError("Couldn't connect to the server") from e

    def get_depths(self, station: int) -> set[int]:
        """
        Retrieves all depths at which temperature is monitored in the soil

        Args:
            station (int): Number of the monitor station in the database

        Returns:
            set[int]: Set of depths
        """
        result = set()
        columns = []

        with self.connection.cursor() as cursor:
            try:
                cursor.execute("""
                               SELECT COLUMN_NAME
                               FROM INFORMATION_SCHEMA.COLUMNS
                               WHERE TABLE_NAME = %s
                               """,
                               (station,))
                temp = cursor.fetchall()
                columns = [int(x[0]) for x in temp if x[0].isdigit()]
                columns = list(filter(
                    lambda x: self.sensors[0] <= x < self.sensors[1], columns))
            except Error as e:
                raise QuerySyntaxError("Invalid passed arguments") from e

        for col in columns:
            result.add(col - self.sensors[0])

        return result

    def get_temperature(self, station: int, timestamp: int,
                        depth: int) -> tuple[float]:
        """
        Retrieves temperature data from all sensors at given station,\
            timestamp and depth

        Args:
            station (int): Number of the monitor station in the database
            timestamp (int): Timestamp of the requested measurement
            depth (int): Depth at which measurement is taken

        Returns:
            tuple[float]: Tuple of the temperature data from all sensors
        """
        if depth not in self.get_depths(station):
            raise ValueError("Can't retrieve temperature info at that depth")

        columns = [x + depth for x in self.sensors]

        with self.connection.cursor() as cursor:
            try:
                cursor.execute("""
                               SELECT `%s`, `%s`, `%s`, `%s`
                               FROM `%s`
                               WHERE time = %s
                               """,
                               (*columns, station, timestamp))
                result = cursor.fetchone()
                result = tuple(map(lambda x: x if x != -100 else None, result))

                return result
            except Error as e:
                raise QuerySyntaxError("Invalid passed arguments") from e

    def get_average_temperature(self, station: int, start: int,
                                interval: int, depth: int) -> tuple[float]:
        """
        Retrieves average temperature data from all sensors at given station,\
            time interval, and depth

        Args:
            station (int): Number of the monitor station in the database
            start (int): Beginning of the considered time interval
            interval (int): Considered time interval
            depth (int): Depth at which measurement is taken

        Returns:
            tuple[float]: Tuple of the average temperature data from all\
                sensors at given time interval
        """
        if depth not in self.get_depths(station):
            raise ValueError("Can't retrieve temperature info at that depth")

        result = [(-100,) * len(self.sensors)]
        columns = [x + depth for x in self.sensors]
        stop = start + interval

        with self.connection.cursor() as cursor:
            try:
                cursor.execute("""
                               SELECT `%s`, `%s`, `%s`, `%s`
                               FROM `%s`
                               WHERE time >= %s
                               AND time < %s
                               """,
                               (*columns, station, start, stop))
                result.extend(cursor.fetchall())
            except Error as e:
                raise QuerySyntaxError("Invalid passed arguments") from e

        mtx = np.array(result)

        if np.all(mtx == -100):
            result = tuple(None for _ in range(mtx.shape[1]))
        else:
            mtx[mtx == -100] = np.nan
            mtx = np.nanmean(mtx, axis=0)
            result = tuple(np.where(np.isnan(mtx), None, mtx))

        return result
