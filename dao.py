import sqlite3
import base64


class DAO:
    def __init__(self, dbpath):
        self.conn = sqlite3.connect(dbpath)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS frames
                               (project_name TEXT, frame_id INT, frame_data TEXT)''')
        self.conn.commit()

    def delete_frame(self, project_name, frame_id):
        self.cursor.execute("DELETE FROM frames WHERE project_name=? AND frame_id=?", (project_name, frame_id))
        self.conn.commit()

    def delete_all_frames(self, project_name):
        self.cursor.execute("DELETE FROM frames WHERE project_name=?", (project_name,))
        self.conn.commit()

    def get_last_frame_id(self, project_name):
        self.cursor.execute("SELECT MAX(frame_id) FROM frames WHERE project_name=?", (project_name,))
        result = self.cursor.fetchone()
        return int(result[0]) if result and result[0] is not None else 0

    def save_frame(self, project_name, frame_data):
        last_frame_id = self.get_last_frame_id(project_name)
        new_frame_id = last_frame_id + 1
        frame_data_base64 = base64.b64encode(frame_data).decode('utf-8')
        self.cursor.execute("INSERT INTO frames (project_name, frame_id, frame_data) VALUES (?, ?, ?)",
                            (project_name, new_frame_id, frame_data_base64))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_frame(self, project_name, frame_id):
        self.cursor.execute("SELECT frame_data FROM frames WHERE project_name=? AND frame_id=?",
                            (project_name, frame_id))
        result = self.cursor.fetchone()
        if result:
            frame_data_base64 = result[0]
            frame_data = base64.b64decode(frame_data_base64)
            print(f"Frame data for frame {frame_id}: {frame_data[:100]}")
            return frame_data
        return None
